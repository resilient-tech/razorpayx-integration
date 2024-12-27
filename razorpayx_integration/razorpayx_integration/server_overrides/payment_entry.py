# TODO: Validations
# Workflow => Payment Entry => Choose Mode of Payment => Choose Party => Bank Account, Party Bank Account and Credit Account (Account Paid From) is autoset.
# 1. Validation should start from Company Bank account. Check RazorPayX Settings.
# 2. Does Mode of Payment Match? Does Credit Account Match? If not, Validate and Show Message.
# 3. Don't automatically show the Paying via RazorPayX description.
# 4. On submit => Pay => Update Refernce No => Update Remarks

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX, RAZORPAYX_INTEGRATION_DOCTYPE
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_description,
    validate_razorpayx_user_payout_mode,
)


# TODO:  also validate IFSC code? (Must be 11 chars or some API)
def validate(doc, method=None):
    validate_online_payment_requirements(doc)


def validate_online_payment_requirements(doc):
    if not doc.make_online_payment:
        return

    validate_mandatory_fields_for_payment(doc)
    validate_payout_mode(doc)
    validate_razorpayx_account(doc)
    validate_upi_id(doc)

    if doc.razorpayx_payment_desc:
        validate_razorpayx_payout_description(doc.razorpayx_payment_desc)


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
    validate_razorpayx_user_payout_mode(doc.razorpayx_payment_mode)

    if doc.razorpayx_payment_mode == USER_PAYOUT_MODE.BANK.value:
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

    elif doc.razorpayx_payment_mode == USER_PAYOUT_MODE.LINK.value:
        if not doc.contact_mobile or not doc.contact_email:
            frappe.throw(
                msg=_(
                    "Any one of Contact's Mobile or  Email is mandatory to make payment with Link."
                ),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

        if not doc.razorpayx_payment_desc:
            frappe.throw(
                msg=_("Payment Description is mandatory to make payment with Link."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

    elif doc.razorpayx_payment_mode == USER_PAYOUT_MODE.UPI.value:
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
    if doc.razorpayx_payment_mode != USER_PAYOUT_MODE.UPI.value:
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


def on_submit(doc, method=None):
    make_payout(doc)


# TODO: enqueue it?
def make_payout(doc):
    PayoutWithPaymentEntry(doc).make_payout()


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
