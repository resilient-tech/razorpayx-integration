import pickle
from abc import ABC, abstractmethod
from base64 import b64decode

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form

from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.razorpayx_integration.apis.payout import (
    RazorPayXCompositePayout,
    RazorPayXLinkPayout,
    RazorPayXPayout,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)


class PAYOUT_CHANNEL(BaseEnum):
    """
    Payout Channel for making payout.

    ---
    - fund_account.bank_account: Make payout with `Fund Account ID` which is linked with party's bank account.
    - fund_account.upi: Make payout with `Fund Account ID` which is linked with party's UPI ID.
    - composite.bank_account: Make payout with  party's bank account details.
    - composite.upi: Make payout with party's UPI ID.
    - link.contact_details: Send payout link to party's contact details.
    - link.contact_id: Send payout link to party's RazorPayX Contact ID.
    """

    # FUND_ACCOUNT_BANK_ACCOUNT = "fund_account.bank_account" # ! Not Supported
    # FUND_ACCOUNT_UPI = "fund_account.upi" # ! Not Supported
    COMPOSITE_BANK_ACCOUNT = "composite.bank_account"
    COMPOSITE_UPI = "composite.upi"
    LINK_CONTACT_DETAILS = "link.contact_details"
    # LINK_CONTACT_ID = "link.contact_id"  # RazorPayX Contact ID # ! Not Supported


class PayoutWithDocument(ABC):
    """
    Make RazorPayx Payout with given Document.

    - Base class for making payout with doctypes.
    - It is recommended to use `Submittable` doctype for making payout.

    :param doc: Document instance.
    """

    ### SETUPS ###
    def __init__(self, doc, *args, **kwargs):
        """
        :param doc: DocType instance.

        ---
        Caution: ⚠️  Don't forget to call `super().__init__()` in sub class.
        """
        self.doc = doc
        self.razorpayx_account = self._get_razorpayx_account()

    ### AUTHORIZATION ###
    # TODO: ? what if payout created from other doctype
    def is_authenticated_payout(self, auth_id: str | None = None) -> bool:
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
                exc=frappe.PermissionError,
            )

        if not frappe.cache.get(f"{auth_id}_authenticated"):
            frappe.throw(
                title=_("Unauthorized Access"),
                msg=_("You are not authorized to access this Payment Entry."),
                exc=frappe.PermissionError,
            )

        payment_entries = frappe.cache.get(f"{auth_id}_payment_entries")
        payment_entries = pickle.loads(b64decode(payment_entries))

        if self.doc.name not in payment_entries:
            frappe.throw(
                title=_("Unauthorized Access"),
                msg=_("This Payment Entry is not authenticated for payment."),
                exc=frappe.PermissionError,
            )

        return True

    ### APIs ###
    def make_payout(self, auth_id: str | None = None) -> dict:
        """
        Make payout with given document.

        :param auth_id: Authorization ID for making payout.
        """
        self.is_authenticated_payout(auth_id)

        self._set_payout_channel()

        if self.payout_channel not in PAYOUT_CHANNEL.values():
            frappe.throw(
                msg=_("Payout channel <strong>{0}</strong> is not supported.").format(
                    self.payout_channel
                ),
                title=_("Unsupported Payout Channel"),
            )

        payout_processor = self._get_payout_processor()
        payout_details = self._get_payout_details()

        # Note: Unsupported Payout Channel is not managed.
        match self.payout_channel:
            case PAYOUT_CHANNEL.COMPOSITE_BANK_ACCOUNT.value:
                return payout_processor.pay_to_bank_account(payout_details)
            case PAYOUT_CHANNEL.COMPOSITE_UPI.value:
                return payout_processor.pay_to_upi_id(payout_details)
            case PAYOUT_CHANNEL.LINK_CONTACT_DETAILS.value:
                return payout_processor.create_with_contact_details(payout_details)

    def cancel(self, update_status: bool = True, cancel_doc: bool = False):
        """
        Cancel payout and payout link of source document.

        :param update_status: Update status in document after cancelling payout and payout link.
        :param cancel_doc: Cancel document after cancelling payout and payout link.

        ---
        Note:
        - ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        - ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """

        self.cancel_payout(update_status=update_status, cancel_doc=cancel_doc)
        self.cancel_payout_link(update_status=update_status, cancel_doc=cancel_doc)

    def cancel_payout(
        self, *, update_status: bool = False, cancel_doc: bool = False
    ) -> dict:
        """
        Cancel payout.

        :param update_status: Update status in document after cancelling payout.
        :param cancel_doc: Cancel document after cancelling payout.

        ---
        Note: ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        """

        if not self.doc.razorpayx_payout_id:
            return

        payout = RazorPayXPayout(self.razorpayx_account)
        response = payout.cancel(
            self.doc.razorpayx_payout_id,
            source_doctype=self.doc.doctype,
            source_docname=self.doc.name,
        )

        self._update_doc_after_payout_cancelled(
            response, update_status=update_status, cancel_doc=cancel_doc
        )

        return response

    def cancel_payout_link(
        self, *, update_status: bool = False, cancel_doc: bool = False
    ) -> dict:
        """
        Cancel payout link.

        :param update_status: Update status in document after cancelling payout link.
        :param cancel_doc: Cancel document after cancelling payout link.

        ---
        Note: ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """
        if not self.doc.razorpayx_payout_link_id:
            return

        payout = RazorPayXLinkPayout(self.razorpayx_account)
        response = payout.cancel(
            self.doc.razorpayx_payout_link_id,
            source_doctype=self.doc.doctype,
            source_docname=self.doc.name,
        )

        self._update_doc_after_payout_cancelled(
            response, update_status=update_status, cancel_doc=cancel_doc
        )

        return response

    ### UTILITY ###
    def _update_doc_after_payout_cancelled(
        self, response: dict, *, update_status: bool = False, cancel_doc: bool = False
    ):
        """
        Update document after cancelling payout or payout link.

        :param response: Response after cancelling payout or payout link.
        :param update_status: Update status in document after cancelling payout or payout link.
        :param cancel_doc: Cancel document after cancelling payout or payout link.
        """

        if update_status:
            self.doc.db_set(
                "razorpayx_payout_status",
                (response.get("status") or PAYOUT_STATUS.CANCELLED.value).title(),
            )

        if cancel_doc and self.doc.docstatus == 1:
            self._cancel_doc()

    def _cancel_doc(self):
        """
        Cancel document.

        It will set `__canceled_by_rpx` flag in document.
        """
        self.doc.flags.__canceled_by_rpx = True
        self.doc.cancel()

    ### ABSTRACT METHODS ###
    @abstractmethod
    def _get_razorpayx_account(self) -> str:
        """
        Return RazorPayX Integration Account name.
        """
        pass

    @abstractmethod
    def _set_payout_channel(self):
        """
        Set Payout Channel for making payout.

        ---
        Example:

        If you want to make payout with party's bank account details,
        ```
        >>> self.payout_channel = PAYOUT_CHANNEL.COMPOSITE_BANK_ACCOUNT.value
        ```
        """
        pass

    @abstractmethod
    def _get_payout_processor(
        self,
    ) -> RazorPayXPayout | RazorPayXCompositePayout | RazorPayXLinkPayout:
        """
        Return Payout Processor for making payout.
        """
        pass

    @abstractmethod
    def _get_payout_details(self) -> dict:
        """
        Return payout details for making payout.
        """
        pass


class PayoutWithPaymentEntry(PayoutWithDocument):
    """
    Make RazorPayx Payout with Payment Entry.

    :param payment_entry: Payment Entry instance.

    ---
    Caution: 🔴 Payout with `Fund Account ID` and `Contact ID` are not supported.
    """

    def __init__(self, payment_entry: PaymentEntry, *args, **kwargs):
        """
        Make RazorPayx Payout with Payment Entry.

        :param payment_entry: Payment Entry instance.

        ---
        Caution: 🔴 Payout with `Fund Account ID` and `Contact ID` are not supported.
        """
        super().__init__(payment_entry, *args, **kwargs)

    ### APIs ###
    def make_payout(self, auth_id: str | None = None) -> dict | None:
        """
        Make payout with given Payment Entry.

        :param auth_id: Authorization ID for making payout.
        """
        response = super().make_payout(auth_id)
        self._update_pe_after_payout(response)

        return response

    ### UTILITY ###
    def _update_pe_after_payout(self, response: dict | None = None):
        """
        Update Payment Entry after making payout.

        :param response: Payout Response.
        """
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

        if status := response.get("status"):
            self.doc.update({"razorpayx_payout_status": status.title()}).save()

    ### HELPERS ###
    def _get_razorpayx_account(self) -> str:
        return self.doc.razorpayx_account

    def _set_payout_channel(self) -> str:
        match self.doc.razorpayx_payout_mode:
            case USER_PAYOUT_MODE.BANK.value:
                self.payout_channel = PAYOUT_CHANNEL.COMPOSITE_BANK_ACCOUNT.value
            case USER_PAYOUT_MODE.UPI.value:
                self.payout_channel = PAYOUT_CHANNEL.COMPOSITE_UPI.value
            case USER_PAYOUT_MODE.LINK.value:
                self.payout_channel = PAYOUT_CHANNEL.LINK_CONTACT_DETAILS.value

    def _get_payout_processor(
        self,
    ) -> RazorPayXPayout | RazorPayXCompositePayout | RazorPayXLinkPayout:
        match self.payout_channel.split(".")[0]:
            case "fund_account":
                return RazorPayXPayout(self.razorpayx_account)
            case "composite":
                return RazorPayXCompositePayout(self.razorpayx_account)
            case "link":
                return RazorPayXLinkPayout(self.razorpayx_account)

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
