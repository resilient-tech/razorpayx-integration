import os
import pickle
from base64 import b32encode, b64encode
from io import BytesIO

import frappe
import frappe.defaults
import pyotp
from frappe import _, get_system_settings
from frappe.auth import get_login_attempt_tracker
from frappe.permissions import ALL_USER_ROLE
from frappe.twofactor import (
    ExpiredLoginException,
    clear_default,
    delete_qrimage,
    get_default,
    get_link_for_qrcode,
    send_token_via_sms,
    set_default,
)
from frappe.utils import cint, get_datetime, get_url, time_diff_in_seconds
from frappe.utils.background_jobs import enqueue
from frappe.utils.password import check_password, decrypt, encrypt


@frappe.whitelist()
def generate_otp(payment_entries):
    # TODO: check for role permissions. Throw if not allowed.

    if isinstance(payment_entries, str):
        payment_entries = frappe.parse_json(payment_entries)

    return Trigger2FA(payment_entries).send_otp()


@frappe.whitelist()
def verify_otp(auth_id, otp):
    return Authenticate2FA(auth_id, otp).verify()


@frappe.whitelist()
def reset_otp_secret(user):
    pass


OTP_ISSUER = "Payment Utils"


class Trigger2FA:

    def __init__(self, payment_entries):
        # self.user = frappe.session.user
        self.user = "smitvora203@gmail.com"
        self.payment_entries = payment_entries
        self.pipeline = frappe.cache.pipeline()

    def send_otp(self):
        self.auth_id = frappe.generate_hash(length=8)

        self.cache_2fa_data(user=self.user, payment_entries=self.payment_entries)

        self.otp_issuer = f"{get_system_settings('otp_issuer_name')} - {OTP_ISSUER}"
        auth_method = self.get_verification_method()

        if auth_method == "Password":
            self.pipeline.execute()
            return {
                "method": auth_method,
                "auth_id": self.auth_id,
                "setup": True,
                "prompt": "Confirm your login password",
            }

        self.otp_secret = self.get_otpsecret(self.user)
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

            if self.get_otplogin(self.user):
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
                self.pipeline.set(f"{self.auth_id}_{k}", v, expiry_time + 100)

            else:
                self.pipeline.set(f"{self.auth_id}_{k}", v, expiry_time)

    @staticmethod
    def get_verification_method():
        if Trigger2FA.two_factor_is_enabled():
            return get_system_settings("two_factor_method")

        return "Password"

    @staticmethod
    def two_factor_is_enabled():
        # TODO: allow server override from config ???
        return cint(get_system_settings("enable_two_factor_auth"))

    @staticmethod
    def get_otplogin(user):
        key = f"{user}_{frappe.scrub(OTP_ISSUER)}_otplogin"

        return get_default(key)

    @staticmethod
    def get_otpsecret(user):
        """Set OTP Secret for user even if not set."""
        key = f"{user}_{frappe.scrub(OTP_ISSUER)}_otpsecret"

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
            "auth_id": self.auth_id,
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
            "auth_id": self.auth_id,
        }

    def process_2fa_for_otp_app(self):
        setup_complete = True if self.get_otplogin(self.user) else False

        return {
            "method": "OTP App",
            "setup": setup_complete,
            "prompt": "Enter verification code from your OTP app",
            "auth_id": self.auth_id,
        }

    def email_2fa_for_otp_app(self):
        # TODO: new qrcode page for OTP App
        totp_uri = pyotp.TOTP(self.otp_secret).provisioning_uri(
            name=self.user, issuer_name=self.otp_issuer
        )
        qrcode_link = get_link_for_qrcode(self.user, totp_uri)

        status = self.send_token_via_email(
            subject=_("OTP registration code from {0}").format(self.otp_issuer),
            message=_(
                "Please click on the link below and follow the instructions on"
                " the page.<br><br><a href='{0}'>{0}</a>"
            ).format(qrcode_link),
        )

        return {
            "prompt": status
            and _(
                "Please check your registered email address for instructions on how to register with OTP App."
            ),
            "method": "Email",
            "setup": status,
            "auth_id": self.auth_id,
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
    def __init__(self, auth_id, otp):
        self.auth_id = auth_id
        self.otp = otp
        # self.user = frappe.session.user
        self.user = "smitvora203@gmail.com"
        self.tracker = get_login_attempt_tracker(self.user)

    def verify(self):
        if not (_user := frappe.cache.get(f"{self.auth_id}_user")):
            raise frappe.AuthenticationError(_("Invalid authentication ID"))

        if self.user != _user.decode("utf-8"):
            raise frappe.AuthenticationError(_("Invalid user authenting ID"))

        auth_method = Trigger2FA.get_verification_method()
        if auth_method == "Password":
            return self.with_password()

        if auth_method in ["SMS", "Email"]:
            return self.with_hotp()

        if auth_method == "OTP App":
            return self.with_totp()

    ##############################################################################################################

    def with_password(self):
        try:
            check_password(self.user, self.otp)
            return self.on_success()

        except frappe.AuthenticationError:
            return self.on_failure(_("Incorrect password"))

    def with_hotp(self):  # SMS and Email
        token = frappe.cache.get(f"{self.auth_id}_token")
        otp_secret = frappe.cache.get(f"{self.auth_id}_otp_secret")

        if not token or not otp_secret:
            return self.on_failure(_("Session expired. Please try again."))

        hotp = pyotp.HOTP(otp_secret)
        if not hotp.verify(self.otp, int(token)):
            return self.on_failure(_("Invalid verification code"))

        return self.on_success()

    def with_totp(self):  # OTP App
        otp_secret = frappe.cache.get(f"{self.auth_id}_otp_secret")

        if not otp_secret:
            return self.on_failure(_("Session expired. Please try again."))

        totp = pyotp.TOTP(otp_secret)
        if not totp.verify(self.otp):
            return self.on_failure(_("Invalid verification code"))

        if not Trigger2FA.get_otplogin(self.user):
            key = f"{self.user}_{frappe.scrub(OTP_ISSUER)}_otplogin"
            set_default(key, 1)
            delete_qrimage(self.user)

        return self.on_success()

    def on_success(self):
        self.tracker.add_success_attempt()
        frappe.cache.set(f"{self.auth_id}_authenticated", "True", 180)
        return {"verified": True}

    def on_failure(self, message):
        self.tracker.add_failure_attempt()
        return {"verified": False, "message": message}
