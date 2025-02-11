import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import fmt_money

from razorpayx_integration.payment_utils.auth import (
    run_before_payment_authentication as has_payment_permissions,
)
from razorpayx_integration.payment_utils.constants.payments import (
    TRANSFER_METHOD as PAYMENT_METHOD,
)
from razorpayx_integration.payment_utils.utils.validation import validate_ifsc_code

BANK_METHOD = [
    PAYMENT_METHOD.IMPS.value,
    PAYMENT_METHOD.NEFT.value,
    PAYMENT_METHOD.RTGS.value,
]


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload(
        "has_payment_permission", has_payment_permissions(doc.name, throw=False)
    )


def validate(doc: PaymentEntry, method=None):
    if not (
        doc.make_bank_online_payment
        and not doc.integration_docname
        and not doc.integration_doctype
    ):
        return

    validate_transfer_methods(doc, method)


def validate_transfer_methods(doc: PaymentEntry, method=None):
    validate_bank_payment_method(doc)
    validate_upi_payment_method(doc)
    validate_link_payment_method(doc)


def validate_bank_payment_method(doc: PaymentEntry):
    if doc.payment_transfer_method not in BANK_METHOD:
        return

    if not (
        doc.party_bank_account and doc.party_bank_account_no and doc.party_bank_ifsc
    ):
        frappe.throw(
            msg=_(
                "Party's Bank Account Details is mandatory to make payment. Please set valid <strong>Party Bank Account</strong>."
            ),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )

    validate_ifsc_code(doc.party_bank_ifsc, throw=True)

    if (
        doc.payment_transfer_method == PAYMENT_METHOD.IMPS.value
        and doc.paid_amount > 5_00_000
    ):
        frappe.throw(
            msg=_(
                "<strong>IMPS</strong> transfer limit is {0}. Please use <strong>RTGS/NEFT</strong> for higher amount."
            ).format(fmt_money(5_00_000, currency="INR")),
            title=_("Payment Limit Exceeded"),
            exc=frappe.ValidationError,
        )

    if (
        doc.payment_transfer_method == PAYMENT_METHOD.RTGS.value
        and doc.paid_amount < 2_00_000
    ):
        frappe.throw(
            msg=_(
                "<strong>RTGS</strong> transfer minimum amount is {0}. Please use <strong>NEFT/IMPS</strong> for lower amount."
            ).format(fmt_money(2_00_000, currency="INR")),
            title=_("Insufficient Payment Amount"),
            exc=frappe.ValidationError,
        )


def validate_upi_payment_method(doc: PaymentEntry):
    if doc.payment_transfer_method != PAYMENT_METHOD.UPI.value:
        return

    if not (doc.party_upi_id and doc.party_bank_account):
        frappe.throw(
            msg=_(
                "Party's UPI ID is mandatory to make payment. Please set valid <strong>Party Bank Account</strong>."
            ),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )


def validate_link_payment_method(doc: PaymentEntry):
    if doc.payment_transfer_method != PAYMENT_METHOD.LINK.value:
        return

    if doc.party_type != "Employee" and not doc.contact_person:
        frappe.throw(
            msg=_("Contact Person is mandatory to make payment with link."),
            title=_("Mandatory Field Missing"),
            exc=frappe.MandatoryError,
        )

    # get contact details of party
    contact_details = get_party_contact_details(doc)
    party_mobile = contact_details["contact_mobile"]
    party_email = contact_details["contact_email"]

    if (
        not doc.contact_email
        and not doc.contact_mobile
        and (party_email or party_mobile)
    ):
        # why db_set? : if calls from API, then it will not update the value without db_set
        doc.db_set({"contact_email": party_email, "contact_mobile": party_mobile})

    if not party_email and not party_mobile:
        if doc.party_type == "Employee":
            msg = _(
                "Set Employee's Mobile or Preferred Email to make payment with link."
            )
        else:
            msg = _("Set valid Contact to make payment with link.")

        frappe.throw(
            msg=msg,
            title=_("Contact Details Missing"),
            exc=frappe.MandatoryError,
        )

    if doc.contact_mobile and doc.contact_mobile != party_mobile:
        frappe.throw(
            msg=_("Mobile Number does not match with Party's Mobile Number"),
            title=_("Invalid Mobile Number"),
        )

    if doc.contact_email and doc.contact_email != party_email:
        frappe.throw(
            msg=_("Email ID does not match with Party's Email ID"),
            title=_("Invalid Email ID"),
        )


def get_party_contact_details(doc: PaymentEntry) -> dict | None:
    """
    Get Party's contact details as Payment Entry's contact fields.

    - Mobile Number
    - Email ID
    """
    if doc.party_type == "Employee":
        return frappe.get_value(
            "Employee",
            doc.party,
            ["cell_number as contact_mobile", "prefered_email as contact_email"],
            as_dict=True,
        )

    return frappe.get_value(
        "Contact",
        doc.contact_person,
        ["mobile_no as contact_mobile", "email_id as contact_email"],
        as_dict=True,
    )
