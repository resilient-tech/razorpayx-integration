from abc import ABC, abstractmethod
from typing import ClassVar

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form

from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.razorpayx_integration.apis.payout import (
    RazorPayXCompositePayout,
    RazorPayXLinkPayout,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_STATUS,
    RAZORPAYX_USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_user_payout_mode,
)


class PayoutWithDocType(ABC):
    """
    Make RazorPayx Payout with given DocType.

    - Base class for making payout with doctypes.
    - It is recommended to use `Submittable` doctype for making payout.

    :param doc: DocType instance.

    ---
    Note: ⚠️ Inherit this class to make payout with different doctypes.

    Caution: 🔴 Payout with `Fund Account ID` is not supported.
    """

    class PAYOUT_METHOD(BaseEnum):
        FUND_ACCOUNT_BANK_ACCOUNT = "fund_account.bank_account"
        FUND_ACCOUNT_UPI = "fund_account.upi"
        COMPOSITE_BANK_ACCOUNT = "composite.bank_account"
        COMPOSITE_UPI = "composite.upi"
        LINK_CONTACT_DETAILS = "link.contact_details"
        LINK_CONTACT_ID = "link.contact_id"  # RazorPayX Contact ID

    class PAYOUT_TYPE(BaseEnum):
        PAYOUT = "payout"
        PAYOUT_LINK = "payout_link"

    PAYOUT_METHOD_MAPPING: ClassVar[dict] = {
        PAYOUT_METHOD.FUND_ACCOUNT_BANK_ACCOUNT.value: "bank_payout_with_fund_account",
        PAYOUT_METHOD.FUND_ACCOUNT_UPI.value: "upi_payout_with_fund_account",
        PAYOUT_METHOD.COMPOSITE_BANK_ACCOUNT.value: "bank_payout_with_composite",
        PAYOUT_METHOD.COMPOSITE_UPI.value: "upi_payout_with_composite",
        PAYOUT_METHOD.LINK_CONTACT_DETAILS.value: "link_payout_with_contact_details",
        PAYOUT_METHOD.LINK_CONTACT_ID.value: "link_payout_with_contact_id",
    }

    ### SETUPS ###
    def __init__(self, doc, *args, **kwargs):
        """
        :param doc: DocType instance.

        ---
        Caution: ⚠️  Don't forget to call `super().__init__()` in sub class.
        """
        self.doc = doc

        self.form_link = self._get_link()

        self.razorpayx_account = self._get_razorpayx_account()

    ### APIs ###
    def make_payout(self) -> dict:
        """
        Make payout with given document.
        """
        self._validate_payout_prerequisite()

        payout_method = self._get_method_for_payout()

        if payout_method not in self.PAYOUT_METHOD_MAPPING:
            frappe.throw(
                msg=_("Payout method <strong>{0}</strong> is not supported.").format(
                    payout_method
                ),
                title=_("Unsupported Payout Method"),
                exc=frappe.ValidationError,
            )

        return getattr(self, self.PAYOUT_METHOD_MAPPING[payout_method])()

    ### HELPERS ###
    def _get_link(self) -> str:
        """
        Return link to form of given document.
        """
        return get_link_to_form(self.doc.doctype, self.doc.name)

    @abstractmethod
    def _get_razorpayx_account(self) -> str:
        """
        Return RazorPayX Integration Account name for making payout.
        """
        pass

    @abstractmethod
    def _get_method_for_payout(self) -> str:
        """
        Return payout method for making payout.

        Decide which method to use for making payout.

        ---
        Example:

        If you want to make payout with `Fund Account ID` with `Bank Account`
        then return `PAYOUT_METHOD.FUND_ACCOUNT_BANK_ACCOUNT.value`.
        """
        pass

    def _get_base_mapped_request(self) -> dict:
        """
        Return base mapped request for making payout.
        """
        return {
            "source_doctype": self.doc.doctype,
            "source_docname": self.doc.name,
        }

    @abstractmethod
    def _get_request_for_fund_account(self) -> dict:
        """
        Return request body for making payout with `Fund Account ID` API.
        """
        pass

    @abstractmethod
    def _get_request_for_composite(self) -> dict:
        """
        Return request body for making payout with `Composite` API.
        """
        pass

    @abstractmethod
    def _get_request_for_link(self) -> dict:
        """
        Return request body for making payout with `Link` API.
        """
        pass

    # TODO: implement this
    ### PAYOUT METHODS ###
    def bank_payout_with_fund_account(self):
        pass

    def upi_payout_with_fund_account(self):
        pass

    def bank_payout_with_composite(self):
        pass

    def upi_payout_with_composite(self):
        pass

    def link_payout_with_contact_details(self):
        pass

    def link_payout_with_contact_id(self):
        pass

    ### VALIDATIONS ###
    @abstractmethod
    def _validate_payout_prerequisite(self):
        """
        Validate prerequisites for making payout.
        """
        pass


class PayoutWithPaymentEntry(PayoutWithDocType):
    """
    Make RazorPayx Payout with Payment Entry.

    :param payment_entry: Payment Entry instance.

    ---
    Caution: 🔴 Payout with `Fund Account ID` and `Contact ID` are not supported.
    """

    def __init__(self, payment_entry: PaymentEntry):
        super().__init__(payment_entry)

    ### APIs ###
    def make_payout(self) -> dict:
        response = super().make_payout()

        # TODO: update payment entry with response

        return response

    ### HELPERS ###
    def _get_razorpayx_account(self) -> str:
        return self.doc.razorpayx_account

    def _get_method_for_payout(self) -> str:
        if self.doc.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.BANK.value:
            return self.PAYOUT_METHOD.COMPOSITE_BANK_ACCOUNT.value
        elif self.doc.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.UPI.value:
            return self.PAYOUT_METHOD.COMPOSITE_UPI.value
        else:
            return self.PAYOUT_METHOD.LINK_CONTACT_DETAILS.value

    ### VALIDATIONS ###
    def _validate_payout_prerequisite(self):
        if self.doc.docstatus != 1:
            frappe.throw(
                msg=_(
                    "To make payout, Payment Entry must be submitted! Please submit <strong>{0}</strong>"
                ).format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if self.doc.payment_type != "Pay":
            frappe.throw(
                msg=_("Payment Entry <strong>{0}</strong> is not set to pay").format(
                    self.form_link
                ),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if not self.doc.make_online_payment:
            frappe.throw(
                msg=_(
                    "Online Payment is not enabled for Payment Entry <strong>{0}</strong>"
                ).format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if not self.doc.razorpayx_account:
            frappe.throw(
                msg=_(
                    "RazorPayX Account not found for Payment Entry <strong>{0}</strong>"
                ).format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if (
            self.doc.razorpayx_payment_status
            != RAZORPAYX_PAYOUT_STATUS.NOT_INITIATED.value.title()
        ):
            frappe.throw(
                msg=_(
                    "Payment Entry <strong>{0}</strong> is already initiated for payment."
                ).format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        validate_razorpayx_user_payout_mode(self.doc.razorpayx_payment_mode)


# Make more general
def get_mapped_request(payment_entry: PaymentEntry) -> dict:
    return frappe._dict(
        {
            "party_id": payment_entry.party,
            "party_type": payment_entry.party_type,
            "party_name": payment_entry.party_name,
            "party_bank_account": payment_entry.party_bank_account,
            "party_bank_account_no": payment_entry.party_bank_account_no,
            "party_bank_ifsc": payment_entry.party_bank_ifsc,
            "party_upi_id": payment_entry.party_upi_id,
            "party_email": payment_entry.contact_email,
            "party_mobile": payment_entry.contact_mobile,
            "amount": payment_entry.paid_amount,
            "payment_description": payment_entry.razorpayx_payment_desc,
            "payment_status": payment_entry.razorpayx_payment_status,
            "source_doctype": payment_entry.doctype,
            "source_docname": payment_entry.name,
        }
    )
