import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form

from razorpayx_integration.razorpayx_integration.apis.payout import (
    RazorPayXCompositePayout,
    RazorPayXLinkPayout,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_STATUS,
    RAZORPAYX_USER_PAYOUT_MODE,
)


@frappe.whitelist()
def make_payout(data):
    pass


# Identify transactions to pay.
# Create a payment entry.

# TODO: make more efficient secure and reliable


def make_payment_from_payment_entry(payment_entry: PaymentEntry):
    """
    Make RazorPayX payment from payment entry
    """

    validate_payment_prerequisite(payment_entry)

    def pay_to_bank_account():
        composite_payout = RazorPayXCompositePayout(payment_entry.razorpayx_account)

        request = get_mapped_request(payment_entry)
        response = composite_payout.create_with_bank_account(
            request, payment_entry.razorpayx_pay_instantaneously
        )

        return response

    def pay_to_upi():
        composite_payout = RazorPayXCompositePayout(payment_entry.razorpayx_account)

        request = get_mapped_request(payment_entry)
        response = composite_payout.create_with_vpa(request)

        return response

    def pay_via_link():
        link_payout = RazorPayXLinkPayout(payment_entry.razorpayx_account)

        request = get_mapped_request(payment_entry)
        response = link_payout.create_with_contact_details(request)

        return response

    # Create RazorPayX Payout
    if payment_entry.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.LINK.value:
        return pay_via_link()
    elif payment_entry.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.UPI.value:
        return pay_to_upi()
    elif payment_entry.razorpayx_payment_mode == RAZORPAYX_USER_PAYOUT_MODE.BANK.value:
        return pay_to_bank_account()
    else:
        frappe.throw(
            msg=_(
                "Invalid Payment Mode <strong>{0}</strong> for Payment Entry <strong>{1}</strong>"
            ).format(payment_entry.razorpayx_payment_mode, payment_entry.name),
            title=_("Invalid Payment Mode"),
            exc=frappe.ValidationError,
        )


def validate_payment_prerequisite(payment_entry: PaymentEntry):
    if (
        payment_entry.razorpayx_payment_status
        != RAZORPAYX_PAYOUT_STATUS.NOT_INITIATED.value.title()
    ):
        frappe.throw(
            msg=_(
                "Payment Entry <strong>{0}</strong> is already initiated for payment."
            ).format(get_link_to_form("Payment Entry", payment_entry.name)),
            title=_("Invalid Payment Entry"),
            exc=frappe.ValidationError,
        )

    if payment_entry.docstatus != 1:
        frappe.throw(
            msg=_(
                "To make payment, Payment Entry must be submitted! <br> Please submit <strong>{0}</strong>"
            ).format(get_link_to_form("Payment Entry", payment_entry.name)),
            title=_("Invalid Payment Entry"),
            exc=frappe.ValidationError,
        )

    if payment_entry.payment_type != "Pay":
        frappe.throw(
            msg=_(
                "Payment Entry <strong>{0}</strong> is not a payment entry to pay."
            ).format(payment_entry.name),
            title=_("Invalid Payment Entry"),
            exc=frappe.ValidationError,
        )

    if not payment_entry.make_online_payment:
        frappe.throw(
            msg=_(
                "Online Payment is not enabled for Payment Entry <strong>{0}</strong>"
            ).format(get_link_to_form("Payment Entry", payment_entry.name)),
            title=_("Invalid Payment Entry"),
            exc=frappe.ValidationError,
        )


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
            "source_type": payment_entry.doctype,
            "source_name": payment_entry.name,
        }
    )
