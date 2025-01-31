import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.payment_utils.auth import Authenticate2FA
from razorpayx_integration.razorpayx_integration.apis.payout import (
    RazorPayXBankPayout,
    RazorPayXLinkPayout,
    RazorPayXPayout,
    RazorPayXUPIPayout,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_CURRENCY,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils import (
    is_already_paid,
    is_auto_cancel_payout_enabled,
    is_payout_via_razorpayx,
)


class PayoutWithPaymentEntry:
    """
    Handle RazorPayx Payout | Payout Link with Payment Entry.

    :param payment_entry: Payment Entry doc.

    ---
    Caution: 🔴 Payout with `Fund Account ID` and Payout Link with `Contact ID` are not supported.
    """

    def __init__(self, doc: PaymentEntry, *args, **kwargs):
        self.doc = doc
        self.razorpayx_setting_name = self.doc.integration_docname

    #### MAKE ####
    def _is_authenticated_payout(self, auth_id: str | None = None) -> bool:
        """
        Check if the Payout (Payment Entry) is authenticated or not.

        :param auth_id: Authentication ID

        ---
        Note: when `frappe.flags.authenticated_by_cron_job` is set, it will bypass the authentication.
        """
        if frappe.flags.authenticated_by_cron_job:
            return True

        if not auth_id:
            frappe.throw(
                title=_("Unauthorized Access"),
                msg=_("Authentication ID is required to make payout."),
                exc=frappe.AuthenticationError,
            )

        if not Authenticate2FA.is_authenticated(auth_id):
            frappe.throw(
                title=_("Unauthorized Access"),
                msg=_("You are not authorized to access this Payment Entry."),
                exc=frappe.AuthenticationError,
            )

        if self.doc.name not in Authenticate2FA.get_payment_entries(auth_id):
            frappe.throw(
                title=_("Unauthorized Access"),
                msg=_("This Payment Entry is not authenticated for payment."),
                exc=frappe.AuthenticationError,
            )

        return True

    def _can_make_payout(self) -> bool:
        return bool(
            self.doc.payment_type == "Pay"
            and self.doc.paid_from_account_currency == PAYOUT_CURRENCY.INR.value
            and self.doc.docstatus == 1
            and is_payout_via_razorpayx(self.doc)
        )

    def _get_payout_processor(
        self,
    ) -> RazorPayXBankPayout | RazorPayXUPIPayout | RazorPayXLinkPayout:
        match self.doc.razorpayx_payout_mode:
            case USER_PAYOUT_MODE.BANK.value:
                return RazorPayXBankPayout(self.razorpayx_setting_name)
            case USER_PAYOUT_MODE.UPI.value:
                return RazorPayXUPIPayout(self.razorpayx_setting_name)
            case USER_PAYOUT_MODE.LINK.value:
                return RazorPayXLinkPayout(self.razorpayx_setting_name)

    def _get_payout_details(self) -> dict:
        return {
            # Mandatory
            "source_doctype": self.doc.doctype,
            "source_docname": self.doc.name,
            "amount": self.doc.paid_amount,
            "party_type": self.doc.party_type,
            # Party Details
            "party_id": self.doc.party,
            "party_name": self.doc.party_name,
            "party_bank_account_no": self.doc.party_bank_account_no,
            "party_bank_ifsc": self.doc.party_bank_ifsc,
            "party_upi_id": self.doc.party_upi_id,
            "party_email": self.doc.contact_email,
            "party_mobile": self.doc.contact_mobile,
            # Payment Details
            "pay_instantaneously": self.doc.razorpayx_pay_instantaneously,
            "description": self.doc.razorpayx_payout_desc,
        }

    ### Make Payout | Payout Link ###
    def make(self, auth_id: str | None = None) -> dict | None:
        """
        Make payout with given Payment Entry.

        :param auth_id: Authentication ID for making payout.
        """
        if is_already_paid(self.doc.amended_from):
            return

        if not self._can_make_payout():
            frappe.throw(
                msg=_(
                    "Payout cannot be made for this Payment Entry. Please check the payout details."
                ),
                title=_("Invalid Payment Entry"),
            )

        self._is_authenticated_payout(auth_id)

        payout_processor = self._get_payout_processor()
        response = payout_processor.pay(self._get_payout_details())

        self._update_after_making(response)

        return response

    def _update_after_making(self, response: dict | None = None):
        self._update_authorized_by()

        if not response:
            return

        values = {}

        entity = response.get("entity")
        id = response.get("id")

        if not entity or not id:
            return

        if entity == "payout":
            values["razorpayx_payout_id"] = id
        elif entity == "payout_link":
            values["razorpayx_payout_link_id"] = id

        if values:
            self.doc.db_set(values, notify=True)

        if (status := response.get("status")) and entity == "payout":
            self.doc.update({"razorpayx_payout_status": status.title()}).save()

    def _update_authorized_by(self):
        user = (
            frappe.get_cached_value("User", "Administrator", "email")
            if frappe.session.user == "Administrator"
            else frappe.session.user
        )

        if user:
            self.doc.db_set("payment_authorized_by", user, notify=True)

    #### Cancel Payout | Payout Link ####
    def _can_cancel_payout_or_link(self) -> bool:
        return self.doc.razorpayx_payout_status.lower() not in [
            PAYOUT_STATUS.QUEUED.value,
            PAYOUT_STATUS.NOT_INITIATED.value,
        ] and is_payout_via_razorpayx(self.doc)

    def cancel(self, cancel_pe: bool = False):
        """
        Cancel payout and payout link of source document.

        :param cancel_pe: Cancel Payment Entry or not.

        ---
        Note:
        - ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        - ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """

        def manually_canceled():
            onload = self.doc.get_onload() or frappe._dict()
            return onload.get("cancel_payout")

        if not self._can_cancel_payout_or_link():
            frappe.msgprint(
                title=_("Invalid Action"),
                msg=_("Payout couldn't be cancelled."),
            )
            return

        if manually_canceled() or is_auto_cancel_payout_enabled(
            self.doc.razorpayx_setting_name
        ):
            self.cancel_payout(cancel_pe=cancel_pe)
            self.cancel_payout_link(cancel_pe=cancel_pe)

    def cancel_payout(self, *, cancel_pe: bool = False) -> dict:
        """
        Cancel payout.

        :param cancel_pe: Cancel Payment Entry or not.

        ---
        Note: ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        """

        if not self.doc.razorpayx_payout_id:
            return

        response = RazorPayXPayout(self.razorpayx_setting_name).cancel(
            self.doc.razorpayx_payout_id,
            source_doctype=self.doc.doctype,
            source_docname=self.doc.name,
        )

        self._update_after_cancelling(response, cancel_pe=cancel_pe)

        return response

    def cancel_payout_link(self, *, cancel_pe: bool = False) -> dict:
        """
        Cancel payout link.

        :param cancel_pe: Cancel Payment Entry or not.

        ---
        Note: ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """
        if not self.doc.razorpayx_payout_link_id:
            return

        response = RazorPayXLinkPayout(self.razorpayx_setting_name).cancel(
            self.doc.razorpayx_payout_link_id,
            source_doctype=self.doc.doctype,
            source_docname=self.doc.name,
        )

        self._update_after_cancelling(response, cancel_pe=cancel_pe)

        return response

    def _update_after_cancelling(self, response: dict, *, cancel_pe: bool = False):
        """
        Update document after cancelling payout or payout link.

        :param response: Cancel API response.
        :param cancel_pe: Cancel Payment Entry or not.
        """

        self.doc.db_set(
            "razorpayx_payout_status",
            (response.get("status") or PAYOUT_STATUS.CANCELLED.value).title(),
        )

        if cancel_pe and self.doc.docstatus == 1:
            self.doc.flags.__canceled_by_rpx = True
            self.doc.cancel()
