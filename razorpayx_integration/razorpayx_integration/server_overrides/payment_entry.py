from typing import Literal

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form
from payment_integration_utils.payment_integration_utils.constants.payments import (
    TRANSFER_METHOD,
)
from payment_integration_utils.payment_integration_utils.server_overrides.doctype.payment_entry import (
    validate_transfer_methods,
)
from payment_integration_utils.payment_integration_utils.utils.auth import (
    run_before_payment_authentication as has_payment_permissions,
)

from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_CURRENCY,
)
from razorpayx_integration.razorpayx_integration.utils import (
    is_already_paid,
    is_auto_cancel_payout_enabled,
    is_auto_pay_enabled,
    is_payout_via_razorpayx,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)

#### CONSTANTS ####
TRANSFER_METHODS = Literal["NEFT", "RTGS", "IMPS", "UPI", "Link"]
UTR_PLACEHOLDER = "*** UTR WILL BE SET AUTOMATICALLY ***"


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    if doc.docstatus == 1 and is_payout_via_razorpayx(doc):
        doc.set_onload(
            "auto_cancel_payout_enabled",
            is_auto_cancel_payout_enabled(doc.integration_docname),
        )


def validate(doc: PaymentEntry, method=None):
    validate_if_already_paid(doc)

    if doc.flags._is_already_paid:
        return

    set_integration_settings(doc)
    validate_payout_details(doc)


def before_submit(doc: PaymentEntry, method=None):
    # for bulk submission from client side or single submission without payment
    if should_uncheck_make_bank_online_payment(doc):
        # PE is not authorized to make payout or auto pay is disabled
        doc.make_bank_online_payment = 0

        if frappe.flags.authenticated_by_cron_job:
            return

        # Show single alert message only
        alert_msg = _("Please make payout manually after Payment Entry submission.")
        alert_sent = False

        for message in frappe.message_log:
            if alert_msg in message.get("message"):
                alert_sent = True
                break

        if not alert_sent:
            frappe.msgprint(msg=alert_msg, alert=True)

    if not doc.make_bank_online_payment:
        # Reset payout description if not making payout
        doc.razorpayx_payout_desc = ""


def should_uncheck_make_bank_online_payment(doc: PaymentEntry) -> bool:
    should_uncheck_payment_flag = (
        not is_auto_pay_enabled(doc.integration_docname)
        if frappe.flags.authenticated_by_cron_job
        else not doc.flags._is_already_paid and not get_auth_id(doc)
    )

    return is_payout_via_razorpayx(doc) and should_uncheck_payment_flag


def on_submit(doc: PaymentEntry, method=None):
    if not is_payout_via_razorpayx(doc):
        return

    PayoutWithPaymentEntry(doc).make(get_auth_id(doc))


def before_cancel(doc: PaymentEntry, method=None):
    # PE is cancelled by RazorpayX webhook or PE is cancelled when payout got cancelled
    if not is_payout_via_razorpayx(doc) or doc.flags.__canceled_by_rpx:
        return

    PayoutWithPaymentEntry(doc).cancel()


### AUTHORIZATION ###
def get_auth_id(doc: PaymentEntry) -> str | None:
    """
    Get `auth_id` from Payment Entry onload.

    It is used to authorize the Payment Entry to make payout.
    """
    onload = doc.get_onload() or frappe._dict()
    return onload.get("auth_id")


#### VALIDATIONS ####
def set_integration_settings(doc: PaymentEntry):
    if doc.paid_from_account_currency != PAYOUT_CURRENCY.INR.value:
        if doc.integration_doctype == RAZORPAYX_SETTING:
            doc.integration_doctype = ""
            doc.integration_docname = ""

        return

    if setting := frappe.db.get_value(
        RAZORPAYX_SETTING, {"disabled": 0, "bank_account": doc.bank_account}
    ):
        doc.integration_doctype = RAZORPAYX_SETTING
        doc.integration_docname = setting


def validate_if_already_paid(doc: PaymentEntry):
    if not doc.amended_from:
        return

    payout_fields = [
        # Common
        "payment_type",
        "bank_account",
        # Party
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
        # Integration
        "integration_doctype",
        "integration_docname",
        # Payout
        "paid_amount",
        "make_bank_online_payment",
        "payment_transfer_method",
        "razorpayx_payout_desc",
        "razorpayx_payout_status",
        "razorpayx_payout_id",
        "razorpayx_payout_link_id",
        "reference_no",
    ]

    original_doc = frappe.db.get_value(
        "Payment Entry",
        doc.amended_from,
        payout_fields,
        as_dict=True,
    )

    if not original_doc or not original_doc.make_bank_online_payment:
        return

    # used in next actions and validations
    doc.flags._is_already_paid = True

    for field in payout_fields:
        if doc.get(field) != original_doc.get(field):
            msg = _("Field <strong>{0}</strong> cannot be changed.<br><br>").format(
                doc.meta.get_label(field)
            )
            msg += _(
                "The source Payment Entry <strong>{0}</strong> is processed via RazorpayX."
            ).format(get_link_to_form("Payment Entry", doc.amended_from))

            frappe.throw(
                title=_("Payout Details Cannot Be Changed"),
                msg=msg,
            )


def validate_payout_details(doc: PaymentEntry):
    if not doc.make_bank_online_payment or doc.integration_doctype != RAZORPAYX_SETTING:
        return

    if not doc.bank_account:
        frappe.throw(
            msg=_("Company's Bank Account is mandatory to make payment."),
            title=_("Mandatory Field Missing"),
            exc=frappe.MandatoryError,
        )

    if not doc.reference_no or doc.docstatus == 0:
        doc.reference_no = UTR_PLACEHOLDER

    if (
        doc.payment_transfer_method == TRANSFER_METHOD.LINK.value
        and not doc.razorpayx_payout_desc
    ):
        frappe.throw(
            msg=_("Payout Description is mandatory to make Payout Link."),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )


### APIs ###
@frappe.whitelist()
def make_payout_with_razorpayx(
    auth_id: str,
    docname: str,
    transfer_method: TRANSFER_METHODS = TRANSFER_METHOD.LINK.value,
    **kwargs,
):
    """
    Make RazorpayX Payout or Payout Link with Payment Entry.

    :param auth_id: Authentication ID (after otp or password verification)
    :param docname: Payment Entry name
    :param transfer_method: Transfer method to make payout with (NEFT, RTGS, IMPS, UPI, Link)
    :param kwargs: Payout Details
    """
    has_payment_permissions(docname, throw=True)
    doc = frappe.get_doc("Payment Entry", docname)

    if doc.make_bank_online_payment:
        frappe.msgprint(
            msg=_(
                "Payout for <strong>{0}</strong> is already in <strong>{1}</strong> state"
            ).format(docname, doc.razorpayx_payout_status),
            alert=True,
        )

        return

    # Set the fields to make payout
    doc.db_set(
        {
            "make_bank_online_payment": 1,
            "payment_transfer_method": transfer_method,
            # Party
            "party_bank_account": kwargs.get("party_bank_account"),
            "party_bank_account_no": kwargs.get("party_bank_account_no"),
            "party_bank_ifsc": kwargs.get("party_bank_ifsc"),
            "party_upi_id": kwargs.get("party_upi_id"),
            "contact_person": kwargs.get("contact_person"),
            "contact_mobile": kwargs.get("contact_mobile"),
            "contact_email": kwargs.get("contact_email"),
            # RazorpayX
            "razorpayx_payout_desc": kwargs.get("razorpayx_payout_desc"),
            # ERPNext
            "reference_no": UTR_PLACEHOLDER,
        }
    )

    validate_transfer_methods(doc)
    validate_payout_details(doc)
    PayoutWithPaymentEntry(doc).make(auth_id)


@frappe.whitelist()
def mark_payout_for_cancellation(docname: str, cancel: bool | int):
    """
    Marking Payment Entry's payout or payout link for cancellation.

    Saving in cache to remember the action.

    :param docname: Payment Entry name.
    :param cancel: Cancel or not.
    """

    frappe.has_permission("Payment Entry", "cancel", doc=docname, throw=True)

    setting = frappe.db.get_value("Payment Entry", docname, "integration_docname")
    frappe.has_permission(RAZORPAYX_SETTING, doc=setting, throw=True)

    key = PayoutWithPaymentEntry.get_cancel_payout_key(docname)
    value = "True" if cancel else "False"

    frappe.cache.set(key, value, 100)
