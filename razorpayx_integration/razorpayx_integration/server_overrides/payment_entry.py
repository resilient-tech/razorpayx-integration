# TODO: Validations
# Workflow => Payment Entry => Choose Mode of Payment => Choose Party => Bank Account, Party Bank Account and Credit Account (Account Paid From) is autoset.
# 1. Validation should start from Company Bank account. Check RazorPayX Settings.
# 2. Does Mode of Payment Match? Does Credit Account Match? If not, Validate and Show Message.
# 3. Don't automatically show the Paying via RazorPayX description.
# 4. On submit => Pay => Update Refernce No => Update Remarks

import frappe
from frappe import _
from frappe.utils import get_link_to_form

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils import (
    get_razorpayx_account,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_user_payout_mode,
)

# TODO: cancel workflow as decided like show dialog and then show if cancelled or not

# TODO: for amended form do copy the payout changes but do not allowed to change the payout details and for header pass amended_fromI


# TODO:  also validate IFSC code? (Must be 11 chars or some API)
# TODO: check payout details with amended from
#### DOC EVENTS ####
def onload(doc, method=None):
    doc.set_onload("disable_payout_fields", is_amended_pe_processed(doc))


def validate(doc, method=None):
    set_razorpayx_account(doc)

    if not doc.razorpayx_account:
        return

    validate_online_payment_requirements(doc)


def on_submit(doc, method=None):
    make_payout_with_razorpayx(doc)


def before_cancel(doc, method=None):
    if doc.flags.__canceled_by_rpx:
        return

    handle_payout_cancellation(doc)


#### VALIDATIONS ####
def validate_online_payment_requirements(doc):
    # Validation for amended details to be same of processed payout
    validate_amended_details(doc)

    # Validation for user to make payment
    if not doc.make_bank_online_payment:
        return

    # TODO: set razorpayx account if not already set
    # Ignore if razorpayx account is not set
    validate_payout_mode(doc)
    validate_upi_id(doc)


def validate_payout_mode(doc):
    if not doc.razorpayx_payout_mode:
        doc.razorpayx_payout_mode = frappe.get_value(
            "Bank Account",
            doc.party_bank_account,
            "default_online_payment_mode",
        )

    validate_razorpayx_user_payout_mode(doc.razorpayx_payout_mode)

    if doc.razorpayx_payout_mode == USER_PAYOUT_MODE.BANK.value:
        # TODO: also fetch `IFSC` and `Account Number` and check
        if not doc.party_bank_account:
            frappe.throw(
                msg=_("Party's Bank Account is mandatory to make payment."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

    elif doc.razorpayx_payout_mode == USER_PAYOUT_MODE.LINK.value:
        if not doc.contact_mobile or not doc.contact_email:
            frappe.throw(
                msg=_(
                    "Any one of Contact's Mobile or  Email is mandatory to make payment with Link."
                ),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

        if not doc.razorpayx_payout_desc:
            frappe.throw(
                msg=_("Payout Description is mandatory to make payment with Link."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

    elif doc.razorpayx_payout_mode == USER_PAYOUT_MODE.UPI.value:
        if not doc.party_upi_id:
            frappe.throw(
                msg=_("Party's UPI ID is mandatory to make payment."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )


def set_razorpayx_account(doc):
    if not doc.razorpayx_account:
        doc.razorpayx_account = get_razorpayx_account(doc.bank_account)


def validate_doc_company(doc):
    # TODO
    pass


def validate_upi_id(doc):
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.UPI.value:
        return

    associated_upi_id = frappe.get_value(
        "Bank Account",
        doc.party_bank_account,
        "upi_id",
    )

    if not associated_upi_id:
        frappe.throw(
            msg=_(
                "UPI ID not found for Party Bank Account <strong>{0}</strong>"
            ).format(doc.party_bank_account),
            title=_("Invalid Party Bank Account"),
            exc=frappe.ValidationError,
        )


def validate_amended_details(doc):
    if not doc.amended_from or not is_amended_pe_processed(doc):
        return

    amended_from_doc = frappe.get_doc("Payment Entry", doc.amended_from)

    # Payments Related Fields
    # TODO: accurate fields ?
    payout_fields = [
        # Common
        "payment_type",
        "bank_account",
        # Party related
        "party",
        "party_type",
        "party_name",
        "party_bank_account",
        "party_bank_account_no",
        "party_bank_ifsc",
        "party_upi_id",
        "contact_person",
        "contact_mobile",
        "contact_email",
        # RazorpayX Related
        "paid_amount",
        "razorpayx_account",
        "make_bank_online_payment",
        "razorpayx_payout_mode",
        "razorpayx_payout_desc",
        "razorpayx_payout_status",
        "razorpayx_pay_instantaneously",
        "razorpayx_payout_id",
        "razorpayx_payout_link_id",
    ]

    for field in payout_fields:
        if doc.get(field) != amended_from_doc.get(field):
            fieldname = _(doc.meta.get_label(field))
            msg = _("Field <strong>{0}</strong> cannot be changed.<br><br>").format(
                fieldname
            )
            msg += _(
                "The source Payment Entry <strong>{0}</strong> is processed via RazorPayX."
            ).format(get_link_to_form("Payment Entry", doc.amended_from))

            frappe.throw(
                title=_("Invalid Amendment"),
                msg=msg,
            )


### ACTIONS ###
def make_payout_with_razorpayx(doc) -> dict | None:
    if doc.docstatus != 1:
        return

    if not doc.razorpayx_account:
        return

    if doc.payment_type != "Pay":
        return

    if doc.razorpayx_payout_id or doc.razorpayx_payout_link_id:
        return

    if not doc.make_bank_online_payment or is_amended_pe_processed(doc):
        return

    return PayoutWithPaymentEntry(doc).make_payout()


def handle_payout_cancellation(doc):
    if not doc.razorpayx_account:
        return

    if not doc.make_bank_online_payment or is_payout_already_cancelled(doc):
        return

    if can_cancel_payout(doc) and should_auto_cancel_payout(doc.razorpayx_account):
        PayoutWithPaymentEntry(doc).cancel()


### UTILITY ###
def is_amended_pe_processed(doc) -> bool | int:
    """
    Check if the amended Payment Entry is processed via RazorPayX or not.

    :param doc: Payment Entry Document
    """
    if not doc.amended_from:
        return False

    return frappe.get_value(
        "Payment Entry", doc.amended_from, "make_bank_online_payment"
    )


def can_cancel_payout(doc) -> bool | int:
    """
    Check if the Payout can be cancelled or not.

    :param doc: Payment Entry Document
    """
    return doc.make_bank_online_payment and doc.razorpayx_payout_status.lower() in [
        PAYOUT_STATUS.NOT_INITIATED.value,
        PAYOUT_STATUS.QUEUED.value,
    ]


def is_payout_already_cancelled(doc) -> bool:
    """
    Check if the Payout is already cancelled or not.

    :param doc: Payment Entry Document
    """
    # TODO: Duplication in webhooks
    return doc.razorpayx_payout_status.lower() in [
        PAYOUT_STATUS.CANCELLED.value,
        PAYOUT_STATUS.REJECTED.value,
        PAYOUT_STATUS.FAILED.value,
    ]


### APIs ###
@frappe.whitelist()
def should_auto_cancel_payout(razorpayx_account: str) -> bool | int:
    """
    Check if the Payout should be auto cancelled or not.

    :param razorpayx_account: RazorPayX Account name
    """
    frappe.has_permission("Payment Entry", throw=True)

    return frappe.db.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE, razorpayx_account, "auto_cancel_payout"
    )


@frappe.whitelist()
def cancel_payout_and_payout_link(doctype: str, docname: str):
    frappe.has_permission("Payment Entry", throw=True)

    doc = frappe.get_cached_doc(doctype, docname)
    PayoutWithPaymentEntry(doc).cancel()


@frappe.whitelist()
def make_payout_with_payment_entry(docname: str, **kwargs):
    """
    Make Payout or Payout Link with Payment Entry.

    :param docname: Payment Entry name
    :param kwargs: Payout details

    """
    frappe.has_permission("Payment Entry", throw=True)
    frappe.has_permission(RAZORPAYX_INTEGRATION_DOCTYPE, throw=True)

    doc = frappe.get_cached_doc("Payment Entry", docname)

    kwargs.pop("cmd")
    doc.db_set(
        {
            "razorpayx_account": get_razorpayx_account(kwargs["bank_account"]),
            "make_bank_online_payment": 1,
            **kwargs,
        }
    )

    validate_online_payment_requirements(doc)
    response = make_payout_with_razorpayx(doc)

    if not response:
        doc.db_set("make_bank_online_payment", 0, update_modified=False)

    return response


# ! Important
# TODO: Change design ?
"""
Bank Account:

- In bank account there should be field for `Default Payment Mode` for that user.
- Other fields should be visible but not mandatory.

Payment Entry:

- When user selects `Party's Bank Account` default mode and other setting should be fetched.
- And PE's data must be matched with that. (Like user can't change UPI or contact details or bank account)
- At PE level user can select `Mode of Payment`.

- Why this?

- No need of multiple bank accounts
- More freedom to user at payment time, how to pay?
"""
