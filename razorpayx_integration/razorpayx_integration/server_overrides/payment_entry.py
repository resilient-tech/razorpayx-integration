# TODO: Validations
# Workflow => Payment Entry => Choose Mode of Payment => Choose Party => Bank Account, Party Bank Account and Credit Account (Account Paid From) is autoset.
# 1. Validation should start from Company Bank account. Check RazorPayX Settings.
# 2. Does Mode of Payment Match? Does Credit Account Match? If not, Validate and Show Message.
# 3. Don't automatically show the Paying via RazorPayX description.
# 4. On submit => Pay => Update Refernce No => Update Remarks

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX, RAZORPAYX_SETTING_DOCTYPE
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_STATUS,
    RAZORPAYX_USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    make_payment_from_payment_entry,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_mode,
)


# TODO: process webhook data
def validate(doc, method=None):
    validate_mandatory_fields_for_payment(doc)
    validate_payout_mode(doc)
    validate_razorpayx_account(doc)
    validate_upi_id(doc)


def validate_mandatory_fields_for_payment(doc):
    if not doc.make_online_payment:
        return

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
    if not doc.make_online_payment:
        return

    validate_razorpayx_payout_mode(doc.razorpayx_payment_mode)

    if doc.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.BANK.value:
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

    elif doc.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.LINK.value:
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

    elif doc.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.UPI.value:
        if not doc.party_upi_id:
            frappe.throw(
                msg=_("Party's UPI ID is mandatory to make payment."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )


def validate_razorpayx_account(doc):
    if not doc.make_online_payment:
        return

    associated_razorpayx_account = frappe.get_value(
        RAZORPAYX_SETTING_DOCTYPE,
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
    if (
        not doc.make_online_payment
        or doc.razorpayx_payment_mode != RAZORPAYX_USER_PAYOUT_MODE.UPI.value
    ):
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


# TODO: enqueue it?
def on_submit(doc, method=None):
    make_online_payment(doc)


def make_online_payment(doc):
    if not doc.make_online_payment:
        return

    response = make_payment_from_payment_entry(doc)

    if not response:
        # TODO: ? what can be done
        return

    if payment_status := response.get("status"):
        doc.razorpayx_payment_status = payment_status


# ! IMPORTANT
# TODO: if on submit fails, also cancel PE
