import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from payment_integration_utils.payment_integration_utils.constants.payments import (
    TRANSFER_METHOD as PAYOUT_MODE,
)
from payment_integration_utils.payment_integration_utils.utils import is_already_paid
from payment_integration_utils.payment_integration_utils.utils.auth import (
    Authenticate2FA,
)

from razorpayx_integration.razorpayx_integration.apis.payout import (
    RazorpayXCompositePayout,
    RazorpayXLinkPayout,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_CURRENCY,
    PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.utils import (
    is_auto_cancel_payout_enabled,
    is_payout_via_razorpayx,
)


class PayoutWithPaymentEntry:
    """
    Handle Razorpayx Payout | Payout Link with Payment Entry.

    :param payment_entry: Payment Entry doc.

    ---
    Caution: 🔴 Payout with `Fund Account ID` and Payout Link with `Contact ID` are not supported.
    """

    def __init__(self, doc: PaymentEntry, *args, **kwargs):
        self.doc = doc
        self.config_name = self.doc.integration_docname

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

        payout_details = self._get_payout_details()

        if self.doc.payment_transfer_method == PAYOUT_MODE.LINK.value:
            response = RazorpayXLinkPayout(self.config_name).pay(payout_details)
        else:
            response = RazorpayXCompositePayout(self.config_name).pay(payout_details)

        self._update_after_making(response)

        return response

    def _is_authenticated_payout(self, auth_id: str | None = None) -> bool:
        """
        Check if the Payout (Payment Entry) is authenticated or not.

        :param auth_id: Authentication ID

        ---
        Note: when `frappe.flags.initiated_by_payment_processor` is set, it will bypass the authentication.
        """
        if frappe.flags.initiated_by_payment_processor:
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

    def _get_payout_details(self) -> dict:
        return {
            # Mandatory for all
            "source_doctype": self.doc.doctype,
            "source_docname": self.doc.name,
            "amount": self.doc.paid_amount,
            "party_type": self.doc.party_type,
            "mode": self.doc.payment_transfer_method,
            # Party Details
            "party_id": self.doc.party,
            "party_name": self.doc.party_name,
            "party_payment_details": {
                "bank_account_no": self.doc.party_bank_account_no,
                "bank_ifsc": self.doc.party_bank_ifsc,
                "upi_id": self.doc.party_upi_id,
            },
            "party_contact_details": {
                "party_name": self.doc.party_name,
                "party_mobile": self.doc.contact_mobile,
                "party_email": self.doc.contact_email,
            },
            # Payment Details
            "description": self.doc.razorpayx_payout_desc,
        }

    def _update_after_making(self, response: dict | None = None):
        user = (
            frappe.get_cached_value("User", "Administrator", "email")
            if frappe.session.user == "Administrator"
            else frappe.session.user
        )

        if user:
            self.doc.db_set("payment_authorized_by", user, notify=True)

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

    #### Cancel Payout | Payout Link ####
    def cancel(self, cancel_pe: bool = False):
        """
        Cancel payout and payout link of source document.

        This method supported only after cancelling Payment Entry's `before cancel` doc event.

        :param cancel_pe: Cancel Payment Entry or not.

        ---
        Note:
        - ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        - ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """
        marked_to_cancel = PayoutWithPaymentEntry.is_cancel_payout_marked(self.doc.name)

        if not self._can_cancel_payout_or_link():
            # from client side manually marked to cancel
            if marked_to_cancel:
                frappe.msgprint(
                    title=_("Invalid Action"),
                    msg=_("Payout couldn't be cancelled."),
                )
            return

        if marked_to_cancel or is_auto_cancel_payout_enabled(self.config_name):
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

        response = RazorpayXCompositePayout(self.config_name).cancel(
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

        response = RazorpayXLinkPayout(self.config_name).cancel(
            self.doc.razorpayx_payout_link_id,
            source_doctype=self.doc.doctype,
            source_docname=self.doc.name,
        )

        self._update_after_cancelling(response, cancel_pe=cancel_pe)

        return response

    def _can_cancel_payout_or_link(self) -> bool:
        return self.doc.razorpayx_payout_status.lower() in [
            PAYOUT_STATUS.QUEUED.value,
            PAYOUT_STATUS.NOT_INITIATED.value,
        ] and is_payout_via_razorpayx(self.doc)

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

    @staticmethod
    def get_cancel_payout_key(docname: str) -> str:
        return f"cancel_payout_{frappe.scrub(docname)}"

    @staticmethod
    def is_cancel_payout_marked(docname: str) -> bool:
        key = PayoutWithPaymentEntry.get_cancel_payout_key(docname)

        if flag := frappe.cache.get(key):
            return flag.decode("utf-8") == "True"

        return False
