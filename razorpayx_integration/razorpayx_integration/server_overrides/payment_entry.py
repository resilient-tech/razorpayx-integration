from typing import Literal

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_details
from frappe.core.doctype.submission_queue.submission_queue import queue_submission
from frappe.utils import get_link_to_form
from frappe.utils.scheduler import is_scheduler_inactive

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE as INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.utils.validations import validate_ifsc_code
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYMENT_MODE_LIMIT,
    PAYOUT_CURRENCY,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.utils import (
    get_razorpayx_setting,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)
from razorpayx_integration.razorpayx_integration.utils.permission import (
    user_has_payout_permissions,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_user_payout_mode,
)

# TODO: Refactor Workflow make it more readable and remove duplicate code
# TODO: Remove extra docstring!
# TODO: Keep the function name more meaningful and consistent
# TODO: with the help of @smit_vora


#### CONSTANTS ####
PAYOUT_MODES = Literal["NEFT/RTGS", "UPI", "Link"]


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload("is_already_paid", is_already_paid(doc))

    doc.set_onload(
        "has_payout_permission",
        user_has_payout_permissions(
            payment_entries=doc.name,
            razorpayx_setting=doc.razorpayx_setting,
            throw=False,
        ),
    )

    if (
        doc.docstatus != 1
        or not doc.razorpayx_setting
        or not doc.make_bank_online_payment
    ):
        return

    doc.set_onload(
        "auto_cancel_payout_enabled",
        is_auto_cancel_payout_enabled(doc.razorpayx_setting),
    )


def validate(doc: PaymentEntry, method=None):
    set_integration_settings(doc)
    validate_if_already_paid(doc)

    if doc.flags.is_already_paid:
        return

    validate_payout_details(doc)


def before_submit(doc: PaymentEntry, method=None):
    # for bulk submission from client side or single submission without payment
    if (
        doc.make_bank_online_payment
        and not doc.flags.is_already_paid
        and not frappe.flags.authenticated_by_cron_job
        and not get_auth_id(doc)
    ):
        # PE is not authorized to make payout
        doc.make_bank_online_payment = 0

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


def on_submit(doc: PaymentEntry, method=None):
    # early return
    if not doc.make_bank_online_payment or not doc.razorpayx_setting:
        return

    make_payout_with_razorpayx(doc, auth_id=get_auth_id(doc))


def before_cancel(doc: PaymentEntry, method=None):
    # PE is cancelled by RazorPayX webhook or PE is cancelled when payout got cancelled
    if doc.flags.__canceled_by_rpx:
        return

    handle_payout_cancellation(doc)


### AUTHORIZATION ###
def get_auth_id(doc: PaymentEntry) -> str | None:
    """
    Get `auth_id` from Payment Entry onload.

    It is used to authorize the Payment Entry to make payout.

    :param doc: Payment Entry Document
    """
    onload = doc.get_onload() or frappe._dict()
    return onload.get("auth_id")


#### VALIDATIONS ####


def set_integration_settings(doc: PaymentEntry):
    setting = frappe.db.get_value(
        INTEGRATION_DOCTYPE, {"disabled": 0, "bank_account": doc.bank_account}
    )

    if setting:
        doc.integration_doctype = INTEGRATION_DOCTYPE
        doc.integration_docname = setting


def validate_if_already_paid(doc: PaymentEntry):
    """
    If the amended Payment Entry is processed via RazorPayX, then do not allow to change Payout Fields.

    :param doc: Payment Entry Document
    """
    if not doc.amended_from:
        return

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
        # Payout Related
        "paid_amount",
        "razorpayx_setting",
        "make_bank_online_payment",
        "razorpayx_payout_mode",
        "razorpayx_payout_desc",
        "razorpayx_payout_status",
        "razorpayx_pay_instantaneously",
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

    doc.flags.is_already_paid = True

    for field in payout_fields:
        if doc.get(field) != original_doc.get(field):
            msg = _("Field <strong>{0}</strong> cannot be changed.<br><br>").format(
                doc.meta.get_label(field)
            )
            msg += _(
                "The source Payment Entry <strong>{0}</strong> is processed via RazorPayX."
            ).format(get_link_to_form("Payment Entry", doc.amended_from))

            frappe.throw(
                title=_("Payout Details Cannot Be Changed"),
                msg=msg,
            )


def validate_payout_details(doc: PaymentEntry):
    """
    Validate Payout details of RazorPayX.

    If `RazorPayx Integration` is not found for the Company's Bank Account, then
    it will just return assuming other Integration is used to make payment.

    :param doc: Payment Entry
    """
    if not doc.make_bank_online_payment:
        return

    if not doc.bank_account:
        frappe.throw(
            msg=_("Company's Bank Account is mandatory to make payment."),
            title=_("Mandatory Field Missing"),
            exc=frappe.MandatoryError,
        )

    # Maybe other Integration is used to make payment instead of RazorPayX
    if doc.integration_doctype != INTEGRATION_DOCTYPE:
        return

    if not doc.reference_no:
        doc.reference_no = "*** UTR WILL BE SET AUTOMATICALLY ***"

    validate_bank_payout_mode(doc)
    validate_upi_payout_mode(doc)
    validate_link_payout_mode(doc)


def validate_bank_payout_mode(doc: PaymentEntry):
    """
    Validate Bank Payout Mode.

    - Validate party bank account no
    - Validate party bank IFSC code

    :param doc: Payment Entry Document
    """
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.BANK.value:
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

    validate_ifsc_code(doc.party_bank_ifsc)

    if (
        doc.razorpayx_pay_instantaneously
        and doc.paid_amount > PAYMENT_MODE_LIMIT.IMPS.value
    ):
        # why db_set? : if calls from API, then it will not update the value
        doc.db_set("razorpayx_pay_instantaneously", 0)


def validate_upi_payout_mode(doc: PaymentEntry):
    """
    Validate UPI Payout Mode.

    - validate party UPI ID

    :param doc: Payment Entry Document
    """
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.UPI.value:
        return

    if not (doc.party_upi_id and doc.party_bank_account):
        frappe.throw(
            msg=_(
                "Party's UPI ID is mandatory to make payment. Please set valid <strong>Party Bank Account</strong>."
            ),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )


def validate_link_payout_mode(doc: PaymentEntry):
    """
    Validate Link Payout Mode.

    - validate Contact's Mobile or Email
    - validate description

    :param doc: Payment Entry Document
    """
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.LINK.value:
        return

    if not (doc.contact_mobile or doc.contact_email):
        frappe.throw(
            msg=_(
                "Any one of Party's Mobile or Email is mandatory to make payout with link."
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

    # Validate email and contact is correct or not
    contact_details = get_contact_details(doc.contact_person)

    if doc.contact_mobile and doc.contact_mobile != contact_details.get(
        "contact_mobile"
    ):
        frappe.throw(
            msg=_(
                "Contact's Mobile <strong>{0}</strong> does not match with selected Contact."
            ).format(doc.contact_mobile),
            title=_("Invalid Mobile"),
        )

    if doc.contact_email and doc.contact_email != contact_details.get("contact_email"):
        frappe.throw(
            msg=_(
                "Contact's Email <strong>{0}</strong> does not match with selected Contact."
            ).format(doc.contact_email),
            title=_("Invalid Email"),
        )


### ACTIONS ###
# TODO: need to be refactor
# TODO: need to be more readable
# TODO: remove duplicate code
# TODO: with the help of @smit_vora
def make_payout_with_razorpayx(doc: PaymentEntry, auth_id: str | None = None):
    """
    Make Payout with RazorPayX Integration.

    :param doc: Payment Entry Document
    :param auth_id: Authentication ID (after otp or password verification)
    """
    if is_already_paid(doc):
        return

    if not can_make_payout(doc):
        frappe.throw(
            msg=_(
                "Payout cannot be made for this Payment Entry. Please check the payout details."
            ),
            title=_("Invalid Payment Entry"),
        )

    PayoutWithPaymentEntry(doc).make_payout(auth_id)


def handle_payout_cancellation(
    doc: PaymentEntry, *, auto_cancel: bool = False, throw: bool = False
):
    """
    Cancel payout and payout link if possible for the Payment Entry.

    Check the settings of RazorPayX Account to auto cancel the payout or not.

    :param doc: Payment Entry Document
    :param auto_cancel: Flag to auto cancel the payout is true or false
    :param throw: Throw error if Payout cannot be cancelled, otherwise just return
    """
    if not can_cancel_payout(doc):
        if throw:
            frappe.throw(
                title=_("Invalid Action"),
                msg=_("Payout cannot be cancelled."),
            )

        return

    if auto_cancel or is_auto_cancel_payout_enabled(doc.razorpayx_setting):
        PayoutWithPaymentEntry(doc).cancel()


### UTILITY ###
# TODO:? can set response in doc's flag
def is_already_paid(doc: PaymentEntry) -> bool | int:
    """
    Check if the original Payment Entry is processed via RazorPayX or not.

    :param doc: Payment Entry Document
    """
    if not doc.amended_from:
        return False

    return frappe.db.get_value(
        "Payment Entry", doc.amended_from, "make_bank_online_payment"
    )


def can_cancel_payout(doc: PaymentEntry) -> bool | int:
    """
    Check if the Payout can be cancelled or not.

    :param doc: Payment Entry Document
    """
    return (
        doc.razorpayx_payout_status.lower()
        in [
            PAYOUT_STATUS.NOT_INITIATED.value,
            PAYOUT_STATUS.QUEUED.value,
        ]
        and doc.razorpayx_setting
        and doc.make_bank_online_payment
    )


def can_make_payout(doc: PaymentEntry) -> bool:
    """
    Check if the Payout can be made or not.

    :param doc: Payment Entry Document
    """
    return (
        is_payout_in_inr(doc)
        and doc.docstatus == 1
        and doc.make_bank_online_payment
        and doc.razorpayx_setting
        and not doc.razorpayx_payout_id
        and not doc.razorpayx_payout_link_id
    )


def is_payout_in_inr(doc: PaymentEntry) -> bool:
    """
    Check if the base conditions are met to make payout or not.

    :param doc: Payment Entry Document
    """
    return (
        doc.payment_type == "Pay"
        and doc.paid_from_account_currency == PAYOUT_CURRENCY.INR.value
    )


def is_auto_cancel_payout_enabled(razorpayx_setting: str) -> bool | int:
    """
    Check if the Payout should be auto cancelled or not.

    :param razorpayx_setting: RazorPayX Integration Setting name
    """
    return frappe.db.get_value(
        INTEGRATION_DOCTYPE, razorpayx_setting, "auto_cancel_payout"
    )


### APIs ###
@frappe.whitelist()
def cancel_payout(docname: str, razorpayx_setting: str):
    """
    Cancel Payout or Payout Link for the Payment Entry.

    :param docname: Payment Entry name
    :param razorpayx_setting: RazorPayX Integration Setting name associated to company bank account
    """
    user_has_payout_permissions(
        docname,
        razorpayx_setting,
        pe_permission="cancel",
        throw=True,
    )

    doc = frappe.get_cached_doc("Payment Entry", docname)
    handle_payout_cancellation(doc, auto_cancel=True, throw=True)


@frappe.whitelist()
def make_payout_with_payment_entry(
    auth_id: str,
    docname: str,
    payout_mode: PAYOUT_MODES = USER_PAYOUT_MODE.LINK.value,
    **kwargs,
):
    """
    Make RazorPayX Payout or Payout Link with Payment Entry.

    :param auth_id: Authentication ID (after otp or password verification)
    :param docname: Payment Entry name
    :param payout_mode: Payout Mode (Bank, UPI, Link)
    """
    doc = frappe.get_doc("Payment Entry", docname)

    user_has_payout_permissions(docname, doc.razorpayx_setting, throw=True)

    # Set the fields to make payout
    doc.db_set(
        {
            "make_bank_online_payment": 1,
            # Party Details
            "party_bank_account": kwargs.get("party_bank_account"),
            "party_bank_account_no": kwargs.get("party_bank_account_no"),
            "party_bank_ifsc": kwargs.get("party_bank_ifsc"),
            "party_upi_id": kwargs.get("party_upi_id"),
            "contact_person": kwargs.get("contact_person"),
            "contact_mobile": kwargs.get("contact_mobile"),
            "contact_email": kwargs.get("contact_email"),
            # RazorPayX Details
            "razorpayx_payout_mode": payout_mode,
            "razorpayx_payout_desc": kwargs.get("razorpayx_payout_desc"),
            "razorpayx_pay_instantaneously": int(
                kwargs.get("razorpayx_pay_instantaneously", 0)
            ),
        }
    )

    validate_payout_details(doc)
    make_payout_with_razorpayx(doc, auth_id=auth_id)


@frappe.whitelist()
def bulk_pay_and_submit(
    auth_id: str, docnames: list[str] | str, task_id: str | None = None
):
    """
    Bulk pay and submit Payment Entries.

    :param auth_id: Authentication ID (after otp or password verification)
    :param docnames: List of Payment Entry names
    :param task_id: Task ID (realtime or background)

    ---
    Reference: [Frappe Bulk Submit/Cancel](https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/desk/doctype/bulk_update/bulk_update.py#L51)
    """
    user_has_payout_permissions(payment_entries=docnames, throw=True)

    if isinstance(docnames, str):
        docnames = frappe.parse_json(docnames)

    if len(docnames) < 20:
        return _bulk_pay_and_submit(auth_id, docnames, task_id)
    elif len(docnames) <= 500:
        frappe.msgprint(_("Bulk operation is enqueued in background."), alert=True)
        frappe.enqueue(
            _bulk_pay_and_submit,
            auth_id=auth_id,
            docnames=docnames,
            task_id=task_id,
            queue="short",
            timeout=1000,
        )
    else:
        frappe.throw(
            _("Bulk operations only support up to 500 documents."),
            title=_("Too Many Documents"),
        )


def _bulk_pay_and_submit(auth_id: str, docnames: list[str], task_id: str | None = None):
    """
    Bulk pay and submit Payment Entries.

    :param auth_id: Authentication ID (after otp or password verification)
    :param docnames: List of Payment Entry names
    :param task_id: Task ID (realtime or background)

    ---
    Reference: [Frappe Bulk Action](https://github.com/frappe/frappe/blob/3eda272bd61b1e73b74d30b1704d885a39c75d0c/frappe/desk/doctype/bulk_update/bulk_update.py#L73)
    """
    failed = []
    num_documents = len(docnames)

    for idx, docname in enumerate(docnames, 1):
        doc = frappe.get_doc("Payment Entry", docname)
        doc.set_onload("auth_id", auth_id)

        try:
            message = ""
            if doc.docstatus.is_draft():
                if doc.meta.queue_in_background and not is_scheduler_inactive():
                    queue_submission(doc, "submit")
                    message = _("Queuing {0} for Submission").format("Payment Entry")
                else:
                    doc.submit()
                    message = _("Submitting {0}").format("Payment Entry")
            else:
                failed.append(docname)

            frappe.db.commit()
            frappe.publish_progress(
                percent=idx / num_documents * 100,
                title=message,
                description=docname,
                task_id=task_id,
            )

        except Exception:
            failed.append(docname)
            frappe.db.rollback()

    return failed
