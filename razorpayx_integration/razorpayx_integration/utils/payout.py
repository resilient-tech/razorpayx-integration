from abc import ABC, abstractmethod
from typing import ClassVar, Literal

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
    PAYOUT_LINK_STATUS,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_user_payout_mode,
)


class PAYOUT_METHOD(BaseEnum):
    FUND_ACCOUNT_BANK_ACCOUNT = "fund_account.bank_account"
    FUND_ACCOUNT_UPI = "fund_account.upi"
    COMPOSITE_BANK_ACCOUNT = "composite.bank_account"
    COMPOSITE_UPI = "composite.upi"
    LINK_CONTACT_DETAILS = "link.contact_details"
    LINK_CONTACT_ID = "link.contact_id"  # RazorPayX Contact ID


class PAYOUT_TYPE(BaseEnum):
    PAYOUT = "payout"  # paid with `Fund Account ID`
    COMPOSITE = "composite"  # paid with party details
    PAYOUT_LINK = "payout_link"  # send link to party contact


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

    PAYOUT_METHOD_MAPPING: ClassVar[dict] = {
        PAYOUT_METHOD.FUND_ACCOUNT_BANK_ACCOUNT.value: "_bank_payout_with_fund_account",
        PAYOUT_METHOD.FUND_ACCOUNT_UPI.value: "_upi_payout_with_fund_account",
        PAYOUT_METHOD.COMPOSITE_BANK_ACCOUNT.value: "_bank_payout_with_composite",
        PAYOUT_METHOD.COMPOSITE_UPI.value: "_upi_payout_with_composite",
        PAYOUT_METHOD.LINK_CONTACT_DETAILS.value: "_link_payout_with_contact_details",
        PAYOUT_METHOD.LINK_CONTACT_ID.value: "_link_payout_with_contact_id",
    }

    PAYOUT_DETAILS_MAPPING: ClassVar[dict] = {
        PAYOUT_TYPE.PAYOUT.value: "_get_payout_details_for_fund_account",
        PAYOUT_TYPE.COMPOSITE.value: "_get_payout_details_for_composite",
        PAYOUT_TYPE.PAYOUT_LINK.value: "_get_payout_details_for_link",
    }

    ### SETUPS ###
    def __init__(self, doc, *args, **kwargs):
        """
        :param doc: DocType instance.

        ---
        Caution: ⚠️  Don't forget to call `super().__init__()` in sub class.
        """
        self.doc = doc
        self.form_link = self._get_form_link()
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
                msg=_("Payout method {0} is not supported.").format(
                    frappe.bold(payout_method)
                ),
                title=_("Unsupported Payout Method"),
                exc=frappe.ValidationError,
            )

        return getattr(self, self.PAYOUT_METHOD_MAPPING[payout_method])()

    def cancel_payout(self, cancel_doc: bool = False) -> dict:
        """
        Cancel payout.

        :param cancel_doc: Cancel document after cancelling payout.

        ---
        Note: ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
        """

        def get_cancelled_status(response: dict) -> str:
            return (
                response.get("status").title() or PAYOUT_STATUS.CANCELLED.value.title()
            )

        if not self.doc.razorpayx_payout_id:
            return

        payout = RazorPayXPayout(self.razorpayx_account)
        response = payout.cancel(self.doc.razorpayx_payout_id)

        self.doc.db_set(
            "razorpayx_payout_status",
            get_cancelled_status(response),
        )

        if cancel_doc:
            self.doc.__canceled_by_rpx = True
            self.doc.cancel()

        return response

    def cancel_payout_link(self, cancel_doc: bool = False) -> dict:
        """
        Cancel payout link.

        :param cancel_doc: Cancel document after cancelling payout link.

        ---
        Note: ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """

        def get_cancelled_status(response: dict) -> str:
            return (
                response.get("status").title()
                or PAYOUT_LINK_STATUS.CANCELLED.value.title()
            )

        if not self.doc.razorpayx_payout_link_id:
            return

        payout = RazorPayXLinkPayout(self.razorpayx_account)
        response = payout.cancel(self.doc.razorpayx_payout_link_id)

        self.doc.db_set(
            "razorpayx_payout_status",
            get_cancelled_status(response),
        )

        if cancel_doc:
            self.doc.__canceled_by_rpx = True
            self.doc.cancel()

        return response

    ### HELPERS ###
    def _get_form_link(self, bold: bool = True) -> str:
        """
        Return link to form of given document.
        """
        return frappe.bold(get_link_to_form(self.doc.doctype, self.doc.name))

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

    def _get_base_payout_details(self) -> dict:
        """
        Return base mapped request for making payout.
        """
        return {
            "source_doctype": self.doc.doctype,
            "source_docname": self.doc.name,
        }

    @abstractmethod
    def _get_payout_details_for_fund_account(self) -> dict:
        """
        Return request body for making payout with `Fund Account ID` API.
        """
        pass

    @abstractmethod
    def _get_payout_details_for_composite(self) -> dict:
        """
        Return request body for making payout with `Composite` API.
        """
        pass

    @abstractmethod
    def _get_payout_details_for_link(self) -> dict:
        """
        Return request body for making payout with `Link` API.
        """
        pass

    ### PAYOUT METHODS ###
    def _get_payout_instance_and_details(
        self,
        payout_type: Literal[
            "payout",
            "composite",
            "payout_link",
        ],
    ) -> tuple[RazorPayXPayout | RazorPayXCompositePayout | RazorPayXLinkPayout, dict]:
        """
        Prepare instance and payout details for making payout.
        """

        def get_api_instance():
            match payout_type:
                case PAYOUT_TYPE.PAYOUT.value:
                    return RazorPayXPayout(self.razorpayx_account)
                case PAYOUT_TYPE.COMPOSITE.value:
                    return RazorPayXCompositePayout(self.razorpayx_account)
                case PAYOUT_TYPE.PAYOUT_LINK.value:
                    return RazorPayXLinkPayout(self.razorpayx_account)

        instance = get_api_instance()
        payout_details = getattr(self, self.PAYOUT_DETAILS_MAPPING[payout_type])()

        return instance, payout_details

    def _bank_payout_with_fund_account(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.PAYOUT.value
        )
        return payout.pay_to_bank_account(payout_details)

    def _upi_payout_with_fund_account(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.PAYOUT.value
        )
        return payout.pay_to_upi_id(payout_details)

    def _bank_payout_with_composite(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.COMPOSITE.value
        )
        return payout.pay_to_bank_account(payout_details)

    def _upi_payout_with_composite(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.COMPOSITE.value
        )
        return payout.pay_to_upi_id(payout_details)

    def _link_payout_with_contact_details(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.PAYOUT_LINK.value
        )
        return payout.create_with_contact_details(payout_details)

    def _link_payout_with_contact_id(self):
        payout, payout_details = self._get_payout_instance_and_details(
            PAYOUT_TYPE.PAYOUT_LINK.value
        )
        return payout.create_with_razorpayx_contact_id(payout_details)

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

        if not response:
            return

        self._update_payment_entry(response)

        return response

    def cancel_payout_and_payout_link(self) -> dict:
        """
        Cancel payout and payout link.

         ---
         Note:
         - ⚠️ Only `queued` payout can be cancelled, otherwise it will raise error.
         - ⚠️ Only `issued` payout link can be cancelled, otherwise it will raise error.
        """

        self.cancel_payout(cancel_doc=False)
        self.cancel_payout_link(cancel_doc=False)

    ### HELPERS ###
    def _get_razorpayx_account(self) -> str:
        return self.doc.razorpayx_account

    def _get_method_for_payout(self) -> str:
        match self.doc.razorpayx_payout_mode:
            case USER_PAYOUT_MODE.BANK.value:
                return PAYOUT_METHOD.COMPOSITE_BANK_ACCOUNT.value
            case USER_PAYOUT_MODE.UPI.value:
                return PAYOUT_METHOD.COMPOSITE_UPI.value
            case USER_PAYOUT_MODE.LINK.value:
                return PAYOUT_METHOD.LINK_CONTACT_DETAILS.value

    def _get_base_payout_details(self) -> dict:
        """
        Return base mapped request for making payout.
        """
        return {
            ## Mandatory Fields ##
            "amount": self.doc.paid_amount,
            "source_doctype": self.doc.doctype,
            "source_docname": self.doc.name,
            "party_type": self.doc.party_type,
            ## Payment Details ##
            "description": self.doc.razorpayx_payout_desc,
        }

    def _get_payout_details_for_fund_account(self) -> dict:
        """
        Return request body for making payout with `Fund Account ID` API.
        """
        return {
            **self._get_base_payout_details(),
            "pay_instantaneously": self.doc.razorpayx_pay_instantaneously,
            # "party_fund_account_id": self.doc.party_fund_account_id,  # ! Not Supported
        }

    def _get_payout_details_for_composite(self) -> dict:
        """
        Return request body for making payout with `Composite` API.
        """
        return {
            **self._get_base_payout_details(),
            "party_id": self.doc.party,
            "party_name": self.doc.party_name,
            "party_bank_account_no": self.doc.party_bank_account_no,
            "party_bank_ifsc": self.doc.party_bank_ifsc,
            "party_upi_id": self.doc.party_upi_id,
            "party_email": self.doc.contact_email,
            "party_mobile": self.doc.contact_mobile,
            "pay_instantaneously": self.doc.razorpayx_pay_instantaneously,
        }

    def _get_payout_details_for_link(self) -> dict:
        """
        Return request body for making payout with `Link` API.
        """
        return {
            **self._get_base_payout_details(),
            "party_name": self.doc.party_name,
            "party_email": self.doc.contact_email,
            "party_mobile": self.doc.contact_mobile,
            # "razorpayx_party_contact_id": self.doc.razorpayx_party_contact_id, # ! Not Supported
        }

    def _update_payment_entry(self, response: dict):
        """
        Update Payment Entry with response.
        """
        values = {}

        entity = response.get("entity")
        id = response.get("id")

        if entity == PAYOUT_TYPE.PAYOUT.value:
            values["razorpayx_payout_id"] = id

            if status := response.get("status"):
                values["razorpayx_payout_status"] = status.title()
        elif entity == PAYOUT_TYPE.PAYOUT_LINK.value:
            values["razorpayx_payout_link_id"] = id

        if values:
            self.doc.db_set(values, update_modified=True)

    ### VALIDATIONS ###
    def _validate_payout_prerequisite(self):
        if self.doc.docstatus != 1:
            frappe.throw(
                msg=_(
                    "To make payout, Payment Entry must be submitted! Please submit {0}"
                ).format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if self.doc.payment_type != "Pay":
            frappe.throw(
                msg=_("Payment Entry {0} is not set to pay").format(self.form_link),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if not self.doc.make_bank_online_payment:
            frappe.throw(
                msg=_("Online Payment is not enabled for Payment Entry {0}").format(
                    self.form_link
                ),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if not self.doc.razorpayx_account:
            frappe.throw(
                msg=_("RazorPayX Account not found for Payment Entry {0}").format(
                    self.form_link
                ),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        if self.doc.razorpayx_payout_id or self.doc.razorpayx_payout_link_id:
            frappe.throw(
                msg=_("Payout already created for Payment Entry {0}").format(
                    self.form_link
                ),
                title=_("Invalid Payment Entry"),
                exc=frappe.ValidationError,
            )

        validate_razorpayx_user_payout_mode(self.doc.razorpayx_payout_mode)
