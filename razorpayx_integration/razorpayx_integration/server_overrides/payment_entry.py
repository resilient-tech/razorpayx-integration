# TODO: Validations
# Workflow => Payment Entry => Choose Mode of Payment => Choose Party => Bank Account, Party Bank Account and Credit Account (Account Paid From) is autoset.
# 1. Validation should start from Company Bank account. Check RazorPayX Settings.
# 2. Does Mode of Payment Match? Does Credit Account Match? If not, Validate and Show Message.
# 3. Don't automatically show the Paying via RazorPayX description.
# 4. On submit => Pay => Update Refernce No => Update Remarks

import frappe
from frappe import _
from frappe.utils import get_link_to_form

from razorpayx_integration.constants import RAZORPAYX, RAZORPAYX_INTEGRATION_DOCTYPE
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_LINK_STATUS,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_description,
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
    validate_online_payment_requirements(doc)


def on_submit(doc, method=None):
    make_payout_with_razorpayx(doc)


def on_cancel(doc, method=None):
    handle_payout_cancellation(doc)


#### VALIDATIONS ####
def validate_online_payment_requirements(doc):
    # Validation for amended details to be same of processed payout
    validate_amended_details(doc)

    # Validation for user to make payment
    if not doc.make_bank_online_payment:
        return

    validate_mandatory_fields_for_payment(doc)
    validate_payout_mode(doc)
    validate_razorpayx_account(doc)
    validate_upi_id(doc)

    if doc.razorpayx_payout_desc:
        validate_razorpayx_payout_description(doc.razorpayx_payout_desc)


def validate_mandatory_fields_for_payment(doc):
    if doc.bank_account and not doc.razorpayx_account:
        frappe.throw(
            msg=_("{0} Account not found for bank account <strong>{1}</strong>").format(
                RAZORPAYX,
                doc.bank_account,
            ),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )

    if not doc.party_type or not doc.party:
        frappe.throw(
            msg=_("Party is mandatory to make payment."),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )


def validate_payout_mode(doc):
    validate_razorpayx_user_payout_mode(doc.razorpayx_payout_mode)

    if doc.razorpayx_payout_mode == USER_PAYOUT_MODE.BANK.value:
        # TODO: also fetch `IFSC` and `Account Number` and check
        if not doc.party_bank_account:
            frappe.throw(
                msg=_("Party's Bank Account is mandatory to make payment."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

        if not doc.bank_account:
            frappe.throw(
                msg=_("Company's Bank Account is mandatory to make payment."),
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


def validate_razorpayx_account(doc):
    associated_razorpayx_account = frappe.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"bank_account": doc.bank_account},
        "name",
    )

    if not associated_razorpayx_account:
        frappe.throw(
            msg=_("{0} Account not found for bank account <strong>{1}</strong>").format(
                RAZORPAYX, doc.bank_account
            ),
            title=_("Invalid Company Bank Account"),
            exc=frappe.ValidationError,
        )

    if associated_razorpayx_account != doc.razorpayx_account:
        frappe.throw(
            msg=_(
                "Company Bank Account <strong>{0}</strong> is not associated with {1} Account <strong>{2}</strong>"
            ).format(doc.bank_account, RAZORPAYX, doc.razorpayx_account),
            title=_("Invalid Company Bank Account"),
            exc=frappe.ValidationError,
        )


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

    if associated_upi_id != doc.party_upi_id:
        frappe.throw(
            msg=_(
                "Party Bank Account <strong>{0}</strong> is not associated with UPI ID <strong>{1}</strong>"
            ).format(doc.party_bank_account, doc.party_upi_id),
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
# TODO: enqueue it?
def make_payout_with_razorpayx(doc):
    if doc.doctype != "Payment Entry":
        frappe.throw(
            title=_("Invalid DocType"),
            msg=_("DocType is not <strong>Payment Entry</strong>").format(doc.doctype),
        )

    if not doc.make_bank_online_payment or is_amended_pe_processed(doc):
        return

    PayoutWithPaymentEntry(doc).make_payout()


def handle_payout_cancellation(doc):
    # TODO: cancel payout
    pass


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
