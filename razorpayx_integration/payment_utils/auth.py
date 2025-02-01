"""
Two Factor Authentication for Payment Entries before making payout.

Methods:

1. OTP via Authenticator App
2. OTP via Email
3. OTP via SMS
4. User Password

Reference: https://github.com/frappe/frappe/blob/13fbdbb0c478099dfac6c70b7e05eef97c14c5ad/frappe/twofactor.py
"""

# TODO: generalize this, not just for payment entries but also for other doctypes
import os
import pickle
from base64 import b32encode, b64decode, b64encode

import frappe
import frappe.defaults
import frappe.permissions
import pyotp
from frappe import _, enqueue, get_system_settings
from frappe.auth import get_login_attempt_tracker
from frappe.twofactor import (
    clear_default,
    delete_qrimage,
    get_default,
    get_link_for_qrcode,
    send_token_via_sms,
    set_default,
)
from frappe.utils import cint, fmt_money
from frappe.utils.password import check_password, decrypt, encrypt

from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import ROLE_PROFILE

# ! Important: Do not use `cache.get_value` or `cache.set_value` as it not working as expected. Use `cache.get` and `cache.set` instead.

##### Constants #####
OTP_ISSUER = "Bank Payments"


class AUTH_METHOD(BaseEnum):
    """
    Authentication Methods for Payment Entries to make payment.
    """

    PASSWORD = "Password"
    SMS = "SMS"
    EMAIL = "Email"
    OTP_APP = "OTP App"


##### APIs #####
@frappe.whitelist()
def generate_otp(payment_entries: list[str] | str) -> dict | None:
    """
    Generate and send OTP for Payment Entries if 2FA is enabled.

    Generates `auth_id` for the user and stores the data in cache.

    :param payment_entries: List of payment entry names.

    ---
    Example response:
    ```py
    {
        "method": "Email",
        "auth_id": "12345678",
        "setup": True,
        "prompt": "Verification code has been sent to your registered email address.",
    }
    ```

    ---
    Note:
    - If 2FA is not enabled, it will return generate `auth_id` with `Password` method.
    """
    if isinstance(payment_entries, str):
        payment_entries = frappe.parse_json(payment_entries)

    # checks permission and other tasks before sending OTP
    run_before_payment_authentication(payment_entries, throw=True)

    return Trigger2FA(payment_entries).send_otp()


@frappe.whitelist()
def verify_authenticator(authenticator: str, auth_id: str) -> dict:
    """
    Verify the OTP or Password for the Payment Entries.

    :param authenticator: OTP or Password.
    :param auth_id: Authentication ID (after otp or password verification).

    ---
    Example response:
    ```py
    {"verified": False, "message": "Invalid verification code"}
    ```
    """
    return Authenticate2FA(authenticator, auth_id).verify()


@frappe.whitelist()
def reset_otp_secret(user: str):
    """
    Reset payment OTP Secret for the user.

    :param user: User for which OTP Secret has to be reset.
    """
    if frappe.session.user != user:
        frappe.throw(_("You are not allowed to reset OTP Secret for another user."))

    if ROLE_PROFILE.PAYMENT_AUTHORIZER.value not in frappe.get_roles():
        frappe.throw(_("You do not have permission to reset OTP Secret."))

    settings = frappe.get_cached_doc("System Settings")

    if not settings.enable_two_factor_auth:
        frappe.throw(
            _("You have to enable Two Factor Auth from System Settings."),
            title=_("Enable Two Factor Auth"),
        )

    otp_issuer = Utils2FA.get_otp_issuer()
    user_email = frappe.get_cached_value("User", user, "email")

    clear_default(Utils2FA.get_otp_login_key(user))
    clear_default(Utils2FA.get_otp_secret_key(user))

    email_args = {
        "recipients": user_email,
        "sender": None,
        "subject": _("Payment OTP Secret Reset - {0}").format(otp_issuer),
        "message": _(
            "<p>Your payment OTP secret on <strong>{0}</strong> used for authorizing <strong>Bank Payments</strong> has been reset! <br><br> If you did not perform this reset and did not request it, please contact your <strong>System Administrator</strong> immediately!!</p>"
        ).format(otp_issuer),
        "delayed": False,
        "retry": 3,
    }

    enqueue(
        method=frappe.sendmail,
        queue="short",
        timeout=300,
        event=None,
        is_async=True,
        job_name=None,
        now=False,
        **email_args,
    )

    frappe.msgprint(
        msg=_(
            "Payment OTP Secret has been reset. <br> Re-registration will be required on next payment!"
        ),
        alert=True,
        indicator="green",
    )


##### Utilities #####
def run_before_payment_authentication(
    payment_entries: str | list[str], throw: bool = False
) -> bool:
    """
    Run `before_payment_authentication` hooks before sending OTP.

    :param payment_entries: List of payment entry names.
    """
    for fn in frappe.get_hooks("before_payment_authentication"):
        if not frappe.get_attr(fn)(payment_entries, throw=throw):
            return False

    return True


class Utils2FA:
    #### Suffixes for cache keys####
    _USER = "_user"
    _TOKEN = "_token"
    _OTP_SECRET = "_otp_secret"
    _OTP_LOGIN = "_otp_login"
    _AUTHENTICATED = "_authenticated"
    _PAYMENT_ENTRIES = "_payment_entries"

    #### Getters and Setters ####
    @staticmethod
    def get_otp_issuer() -> str:
        return f"{get_system_settings('otp_issuer_name') or 'Frappe Framework'} - {OTP_ISSUER}"

    @staticmethod
    def get_otp_login_key(user: str) -> str:
        return f"{user}_{frappe.scrub(OTP_ISSUER)}{Utils2FA._OTP_LOGIN}"

    @staticmethod
    def get_otp_secret_key(user: str) -> str:
        return f"{user}_{frappe.scrub(OTP_ISSUER)}{Utils2FA._OTP_SECRET}"

    @staticmethod
    def get_verification_method() -> str:
        """
        Get the verification method to authenticate the payment entries.

        :return: Verification method (Password, SMS, Email, OTP App)
        """
        if Utils2FA.is_two_factor_enabled():
            return get_system_settings("two_factor_method")

        return AUTH_METHOD.PASSWORD.value

    @staticmethod
    def get_otp_secret(user) -> str:
        """
        Get OTP Secret for the user.

        And set OTP Secret to default for user if not set.
        """
        key = Utils2FA.get_otp_secret_key(user)

        if otp_secret := get_default(key):
            return decrypt(otp_secret, key=key)

        otp_secret = b32encode(os.urandom(10)).decode("utf-8")
        set_default(key, encrypt(otp_secret))

        return otp_secret

    @staticmethod
    def get_otp_login(user) -> str:
        return get_default(Utils2FA.get_otp_login_key(user))

    @staticmethod
    def is_two_factor_enabled() -> int:
        return cint(get_system_settings("enable_two_factor_auth"))

    #### Sending Email ####
    @staticmethod
    def send_authentication_email(user: str, subject: str, message: str) -> bool:
        user_email = frappe.get_cached_value("User", user, "email")

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

    @staticmethod
    def get_email_body_for_2fa(
        otp: str, paid_amount: int | float, payment_entries: str, **kwargs
    ):
        body = """
        <p>Enter the verification code below to authenticate the payment of <strong>{{ paid_amount }}</strong></p>
        <br>
        <p style="text-align: center;">
        <strong style="font-size: 20px;">{{ otp }}</strong></p>
        <br>
        <p><strong>Payment Entries Authorized:</strong> [{{ payment_entries }}]</p>
        <br>
        <p><strong>Note:</strong> This code expires in 5 minutes.</p>
        """

        return frappe.render_template(
            body,
            {
                "otp": otp,
                "paid_amount": fmt_money(paid_amount, currency="INR"),
                "payment_entries": payment_entries,
            },
        )


##### Processors #####
class Trigger2FA:
    """
    Processor for generate and send OTP for Payment Entries.

    Handle OTP generation and sending via SMS, Email, and OTP App.

    If 2FA is not enabled, it will return generate `auth_id` with `Password` method.

    :param payment_entries: List of payment entry names.
    """

    def __init__(self, payment_entries: list[str]):
        self.user = frappe.session.user
        self.payment_entries = payment_entries
        self.pipeline = frappe.cache.pipeline()

    #### APIs ####
    def send_otp(self):
        """
        Send OTP for Payment Entries.

        Generates `auth_id` for the user and stores the data in cache.
        """
        self.auth_id = frappe.generate_hash(length=8)
        self.otp_issuer = Utils2FA.get_otp_issuer()
        self.auth_method = Utils2FA.get_verification_method()

        self.cache_2fa_data(user=self.user, payment_entries=self.payment_entries)

        if self.auth_method == AUTH_METHOD.PASSWORD.value:
            self.pipeline.execute()
            return {
                "method": self.auth_method,
                "auth_id": self.auth_id,
                "setup": True,
                "prompt": "Confirm your login password",
            }

        self.otp_secret = Utils2FA.get_otp_secret(self.user)
        self.token = pyotp.TOTP(self.otp_secret).now()

        self.cache_2fa_data(otp_secret=self.otp_secret)

        if self.auth_method == AUTH_METHOD.SMS.value:
            self.cache_2fa_data(token=self.token)
            self.pipeline.execute()

            return self.process_2fa_for_sms()

        if self.auth_method == AUTH_METHOD.EMAIL.value:
            self.cache_2fa_data(token=self.token)
            self.pipeline.execute()

            return self.process_2fa_for_email()

        if self.auth_method == AUTH_METHOD.OTP_APP.value:
            self.pipeline.execute()

            if Utils2FA.get_otp_login(self.user):
                return self.process_2fa_for_otp_app()

            return self.email_2fa_for_otp_app()

    ### Caching Data ###
    def cache_2fa_data(self, **kwargs):
        # set increased expiry time for SMS and Email
        if self.auth_method in [AUTH_METHOD.SMS.value, AUTH_METHOD.EMAIL.value]:
            expiry_time = 300
        else:
            expiry_time = 180

        for k, v in kwargs.items():
            if not isinstance(v, str | int | float):
                v = b64encode(pickle.dumps(v)).decode("utf-8")

            # for payment_entries, set expiry time to 100 seconds more than token expiry
            expiry_time = expiry_time + 100 if k == "payment_entries" else expiry_time

            self.pipeline.set(f"{self.auth_id}_{k}", v, expiry_time)

    #### 2FA Methods ####
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
            "method": self.auth_method,
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

        status = Utils2FA.send_authentication_email(
            user=self.user,
            subject=_("OTP from {0} for authorizing payment").format(self.otp_issuer),
            message=Utils2FA.get_email_body_for_2fa(**template_args),
        )

        return {
            "prompt": status
            and _("Verification code has been sent to your registered email address."),
            "method": self.auth_method,
            "setup": status,
            "auth_id": self.auth_id,
        }

    def process_2fa_for_otp_app(self):
        setup_complete = True if Utils2FA.get_otp_login(self.user) else False

        return {
            "method": self.auth_method,
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

        status = Utils2FA.send_authentication_email(
            user=self.user,
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
            "method": self.auth_method,
            "setup": status,
            "auth_id": self.auth_id,
        }


class Authenticate2FA:
    """
    Processor for verifying the OTP or Password for the Payment Entries.
    """

    def __init__(self, authenticator: str, auth_id: str):
        """
        Processor for verify the OTP or Password for the Payment Entries.

        :param authenticator: OTP or Password.
        :param auth_id: Authentication ID (after otp or password verification).
        """
        self.authenticator = authenticator
        self.auth_id = auth_id
        self.user = frappe.session.user
        self.tracker = get_login_attempt_tracker(self.user)

    def verify(self) -> dict:
        if not (_user := frappe.cache.get(f"{self.auth_id}{Utils2FA._USER}")):
            raise frappe.AuthenticationError(_("Invalid Authentication ID"))

        if self.user != _user.decode("utf-8"):
            raise frappe.AuthenticationError(_("Invalid user Authentication ID"))

        self.auth_method = Utils2FA.get_verification_method()
        if self.auth_method == AUTH_METHOD.PASSWORD.value:
            return self.with_password()

        if self.auth_method in [AUTH_METHOD.SMS.value, AUTH_METHOD.EMAIL.value]:
            return self.with_hotp()

        if self.auth_method == AUTH_METHOD.OTP_APP.value:
            return self.with_totp()

    #### Verification With Methods ####
    def with_password(self) -> dict:
        try:
            check_password(self.user, self.authenticator)
            return self.on_success()

        except frappe.AuthenticationError:
            return self.on_failure(_("Incorrect password"))

    def with_hotp(self) -> dict:
        """
        SMS and Email OTP Verification.
        """
        token = frappe.cache.get(f"{self.auth_id}{Utils2FA._TOKEN}")
        otp_secret = self.get_auth_opt_secret()

        if not token or not otp_secret:
            return self.on_failure(_("Session expired. Please try again."))

        hotp = pyotp.HOTP(otp_secret)
        if not hotp.verify(self.authenticator, int(token)):
            return self.on_failure(_("Invalid verification code"))

        return self.on_success()

    def with_totp(self) -> dict:
        """
        OTP App Verification.
        """
        otp_secret = self.get_auth_opt_secret()

        if not otp_secret:
            return self.on_failure(_("Session expired. Please try again."))

        totp = pyotp.TOTP(otp_secret)
        if not totp.verify(self.authenticator):
            return self.on_failure(_("Invalid verification code"))

        if not Utils2FA.get_otp_login(self.user):
            set_default(Utils2FA.get_otp_login_key(self.user), 1)
            delete_qrimage(self.user)

        return self.on_success()

    #### Helper Methods ####
    @staticmethod
    def is_authenticated(auth_id: str) -> bool:
        if authenticated := frappe.cache.get(f"{auth_id}{Utils2FA._AUTHENTICATED}"):
            return authenticated.decode("utf-8") == "True"

        return False

    @staticmethod
    def get_payment_entries(auth_id: str) -> list[str]:
        payment_entries = frappe.cache.get(f"{auth_id}{Utils2FA._PAYMENT_ENTRIES}")
        return pickle.loads(b64decode(payment_entries))

    def get_auth_opt_secret(self) -> str:
        return frappe.cache.get(f"{self.auth_id}{Utils2FA._OTP_SECRET}")

    def on_success(self) -> dict:
        self.tracker.add_success_attempt()
        frappe.cache.set(f"{self.auth_id}{Utils2FA._AUTHENTICATED}", "True", 180)
        return {"verified": True}

    def on_failure(self, message) -> dict:
        self.tracker.add_failure_attempt()
        return {"verified": False, "message": message}
