import os
import pickle
from base64 import b32encode, b64encode
from io import BytesIO

import frappe
import frappe.defaults
import pyotp
from frappe import _, get_system_settings
from frappe.permissions import ALL_USER_ROLE
from frappe.twofactor import (
    ExpiredLoginException,
    clear_default,
    get_default,
    get_link_for_qrcode,
    send_token_via_sms,
    set_default,
)
from frappe.utils import cint, get_datetime, get_url, time_diff_in_seconds
from frappe.utils.background_jobs import enqueue
from frappe.utils.password import decrypt, encrypt


@frappe.whitelist()
def generate_otp(payment_entries):
    # TODO: check for role permissions. Throw if not allowed.

    if isinstance(payment_entries, str):
        payment_entries = frappe.parse_json(payment_entries)

    return Trigger2FA(payment_entries).send_otp()


@frappe.whitelist()
def verify_otp(temp_id, otp):
    return Authenticate2FA(temp_id, otp)


class Trigger2FA:
    OTP_ISSUER = "Payment Utils"

    def __init__(self, payment_entries):
        # self.user = frappe.session.user
        self.user = "smitvora203@gmail.com"
        self.payment_entries = payment_entries
        self.pipeline = frappe.cache.pipeline()

    def send_otp(self):
        self.temp_id = frappe.generate_hash(length=8)

        self.cache_2fa_data(user=self.user, payment_entries=self.payment_entries)

        self.otp_issuer = (
            f"{get_system_settings('otp_issuer_name')} - {self.OTP_ISSUER}"
        )
        auth_method = self.get_verification_method()

        if auth_method == "Password":
            self.pipeline.execute()
            return {"method": auth_method, "temp_id": self.temp_id}

        self.otp_secret = self.get_otpsecret()
        self.token = pyotp.TOTP(self.otp_secret).now()

        self.cache_2fa_data(otp_secret=self.otp_secret)

        if auth_method == "SMS":
            self.cache_2fa_data(token=self.token)
            self.pipeline.execute()

            return self.process_2fa_for_sms()

        if auth_method == "Email":
            self.cache_2fa_data(token=self.token)
            self.pipeline.execute()

            return self.process_2fa_for_email()

        if auth_method == "OTP App":
            self.pipeline.execute()

            if self.get_otplogin():
                return self.process_2fa_for_otp_app()

            return self.email_2fa_for_otp_app()

    ##############################################################################################################

    def cache_2fa_data(self, **kwargs):
        auth_method = self.get_verification_method()

        # set increased expiry time for SMS and Email
        if auth_method in ["SMS", "Email"]:
            expiry_time = 300
        else:
            expiry_time = 180

        for k, v in kwargs.items():
            if not isinstance(v, str | int | float):
                v = b64encode(pickle.dumps(v)).decode("utf-8")

            if k == "payment_entries":
                # extra time for processing PEs
                self.pipeline.set(f"{self.temp_id}_{k}", v, expiry_time + 100)

            else:
                self.pipeline.set(f"{self.temp_id}_{k}", v, expiry_time)

    def get_verification_method(self):
        if self.two_factor_is_enabled():
            return get_system_settings("two_factor_method")

        return "Password"

    def two_factor_is_enabled(self):
        # TODO: allow server override from config ???
        return cint(get_system_settings("enable_two_factor_auth"))

    def get_otplogin(self):
        key = f"{self.user}_{frappe.scrub(self.OTP_ISSUER)}_otplogin"

        return get_default(key)

    def get_otpsecret(self):
        """Set OTP Secret for user even if not set."""
        key = f"{self.user}_{frappe.scrub(self.OTP_ISSUER)}_otpsecret"

        if otp_secret := get_default(key):
            return decrypt(otp_secret, key=key)

        otp_secret = b32encode(os.urandom(10)).decode("utf-8")
        set_default(key, encrypt(otp_secret))

        return otp_secret

    ##############################################################################################################

    def process_2fa_for_sms(self):
        phone = frappe.db.get_value(
            "User", self.user, ["phone", "mobile_no"], as_dict=1
        )
        phone = phone.mobile_no or phone.phone
        status = send_token_via_sms(self.otp_secret, self.token, phone_no=phone)

        return {
            "prompt": status
            and "Enter verification code sent to {}".format(
                phone[:4] + "******" + phone[-3:]
            ),
            "method": "SMS",
            "setup": status,
        }

    def process_2fa_for_email(self):
        hotp = pyotp.HOTP(self.otp_secret)
        otp = hotp.at(int(self.token))

        template_args = {
            "otp": otp,
            "payment_entries": ", ".join(self.payment_entries),
            "paid_amount": frappe.db.get_value(
                "Payment Entry",  # TODO: Generalize this
                {"name": ["in", self.payment_entries]},
                "sum(paid_amount)",
            ),
        }

        status = self.send_token_via_email(
            subject=_("OTP from {0} for authorizing payment").format(self.otp_issuer),
            message=self.email_body_for_2fa(**template_args),
        )

        return {
            "prompt": status
            and _("Verification code has been sent to your registered email address."),
            "method": "Email",
            "setup": status,
        }

    def process_2fa_for_otp_app(self):
        setup_complete = True if self.get_otplogin() else False

        return {
            "method": "OTP App",
            "setup": setup_complete,
            "prompt": "Enter verification code from your OTP app",
        }

    def email_2fa_for_otp_app(self):
        totp_uri = pyotp.TOTP(self.otp_secret).provisioning_uri(
            name=self.user, issuer_name=self.otp_issuer
        )
        qrcode_link = get_link_for_qrcode(self.user, totp_uri)

        status = self.send_token_via_email(
            subject=_("OTP Registration code from {0}").format(self.otp_issuer),
            message=_(
                "Please click on the link below and follow the instructions on"
                " the page.<br><br><a href='{0}'>{0}</a>"
            ).format(qrcode_link),
        )

        return {
            "prompt": status
            and _(
                "Please check your registered email address for instructions on how to proceed. Do not close this window as you will have to return to it."
            ),
            "method": "Email",
            "setup": status,
        }

    ##############################################################################################################

    def send_token_via_email(self, subject, message):
        user_email = frappe.db.get_value("User", self.user, "email")
        if not user_email:
            return False

        frappe.sendmail(
            recipients=user_email,
            subject=subject,
            message=message,
            header=[_("Verification Code"), "blue"],
            delayed=False,
        )

        return True

    def email_body_for_2fa(self, **kwargs):
        body = """
        Enter the verification code below to authenticate the payment of Rs. {{ paid_amount }}:
        <br><br>
        <b style="font-size: 18px;">{{ otp }}</b>
        <br><br>
        <b>Payment Entries Authorized:</b> {{ payment_entries }}<br>
        <b>Note:</b> This code expires in 5 minutes.
        """

        return frappe.render_template(body, kwargs)


class Authenticate2FA:
    def __init__(self, temp_id, otp=None):
        self.temp_id = temp_id
        self.otp = otp
