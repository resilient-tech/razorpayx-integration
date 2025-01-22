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
    PAYMENT_MODE_THRESHOLD,
    PAYOUT_CURRENCY,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.constants.roles import ROLE_PROFILE
from razorpayx_integration.razorpayx_integration.utils import (
    get_razorpayx_account,
)
from razorpayx_integration.razorpayx_integration.utils.payout import (
    PayoutWithPaymentEntry,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_user_payout_mode,
)


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload("amended_pe_processed", is_amended_pe_processed(doc))


def validate(doc: PaymentEntry, method=None):
    validate_amended_pe(doc)
    validate_payout_details(doc)


def before_submit(doc: PaymentEntry, method=None):
    # for bulk submission from client side or single submission without payment
    if (
        doc.make_bank_online_payment
        and not is_amended_pe_processed(doc)
        and not frappe.flags.authenticated_by_cron_job
        and not get_auth_id(doc)
    ):
        doc.set("make_bank_online_payment", 0)

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
        reset_razorpayx_fields(doc)


def on_submit(doc: PaymentEntry, method=None):
    # early return
    if not doc.make_bank_online_payment or not doc.razorpayx_account:
        return

    make_payout_with_razorpayx(doc, auth_id=get_auth_id(doc))


def before_cancel(doc: PaymentEntry, method=None):
    # PE is cancelled by RazorPayX webhook or PE is cancelled when payout got cancelled
    if doc.flags.__canceled_by_rpx:
        return

    handle_payout_cancellation(doc)


### AUTHORIZATION ###
def get_auth_id(doc: PaymentEntry):
    onload = doc.get_onload() or frappe._dict()
    return onload.get("auth_id")


#### VALIDATIONS ####
def validate_amended_pe(doc: PaymentEntry):
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

    amended_from_doc = frappe.db.get_value(
        "Payment Entry",
        doc.amended_from,
        payout_fields,
        as_dict=True,
    )

    if not amended_from_doc or not amended_from_doc.make_bank_online_payment:
        return

    for field in payout_fields:
        if doc.get(field) != amended_from_doc.get(field):
            msg = _("Field <strong>{0}</strong> cannot be changed.<br><br>").format(
                _(doc.meta.get_label(field))
            )
            msg += _(
                "The source Payment Entry <strong>{0}</strong> is processed via RazorPayX."
            ).format(get_link_to_form("Payment Entry", doc.amended_from))

            frappe.throw(
                title=_("Payout Details Cannot Be Changed"),
                msg=msg,
            )


def validate_payout_details(doc: PaymentEntry, throw=False):
    """
    Validate Payout details of RazorPayX.

    :param doc: Payment Entry
    :param throw: Throw error if Payout details are not valid otherwise just return
    """
    if not doc.make_bank_online_payment:
        return

    # TODO:  ?  here check base conditions like `Pay`,`Cash`,`INR` etc.

    validate_razorpayx_account(doc, throw=throw)

    # Maybe other Integration is used to make payment instead of RazorPayX
    if not doc.razorpayx_account:
        return

    set_missing_payout_details(doc)
    validate_party_bank_account(doc)
    validate_payout_modes(doc)


# TODO: make it more simple?
def validate_razorpayx_account(doc: PaymentEntry, throw: bool = False):
    """
    Validate RazorpayX Account.

    Also set the RazorpayX Account based on Company's Bank Account.

    :param doc: Payment Entry Document
    :param throw: Throw error if
    - Bank Account is not set
    - RazorPayX Account not found for Bank Account
    - RazorPayX Account is disabled
    """
    set_razorpayx_account(doc, throw)

    # Always throw error if account is disabled
    if doc.razorpayx_account and doc.razorpayx_account_details.get("disabled"):
        frappe.throw(
            msg=_(
                "RazorpayX Account <strong>{0}</strong> is disabled. Please enable it first to use!"
            ).format(doc.razorpayx_account),
            title=_("Invalid RazorpayX Account"),
        )


def validate_party_bank_account(doc: PaymentEntry):
    """
    Validate Party's Bank Account.

    :param doc: Payment Entry Document
    """

    if doc.party_bank_account and doc.party_bank_account_details.disabled:
        frappe.throw(
            msg=_("Party's Bank Account <strong>{0}</strong> is disabled.").format(
                doc.party_bank_account
            ),
            title=_("Invalid Bank Account"),
        )


def validate_payout_modes(doc: PaymentEntry):
    """
    Validate Payout Modes based on RazorPayX User Payout Mode.

    - Bank Payout Mode
    - UPI Payout Mode
    - Link Payout Mode

    :param doc: Payment Entry Document
    """
    validate_razorpayx_user_payout_mode(doc.razorpayx_payout_mode)

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

    if doc.party_bank_account_no != doc.party_bank_account_details.account_no:
        frappe.throw(
            msg=_(
                "Party's Bank Account No <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_bank_account_no),
            title=_("Invalid Bank Account No"),
        )

    if doc.party_bank_ifsc != doc.party_bank_account_details.ifsc_code:
        frappe.throw(
            msg=_(
                "Party's Bank IFSC Code <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_bank_ifsc),
            title=_("Invalid Bank IFSC Code"),
        )

    if (
        doc.razorpayx_pay_instantaneously
        and doc.paid_amount > PAYMENT_MODE_THRESHOLD.IMPS.value
    ):
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

    if doc.party_upi_id != doc.party_bank_account_details.upi_id:
        frappe.throw(
            msg=_(
                "Party's UPI ID <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_upi_id),
            title=_("Invalid UPI ID"),
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


#### EVENT'S HELPERS ####
# TODO: make it more simple?
def set_razorpayx_account(doc: PaymentEntry, throw: bool = False):
    """
    Set RazorPayX Account based on Company's Bank Account.

    :param doc: Payment Entry Document
    :param throw: Throw error if
    - Bank Account is not set
    - RazorPayX Account not found for Bank Account
    """
    doc.razorpayx_account = ""

    if not doc.bank_account:
        if throw:
            frappe.throw(
                msg=_("Bank Account is mandatory to make payment."),
                title=_("Mandatory Fields Missing"),
                exc=frappe.MandatoryError,
            )

        return

    # Fetch RazorpayX Account based on Bank Account
    doc.razorpayx_account_details = (
        get_razorpayx_account(
            identifier=doc.bank_account,
            search_by="bank_account",
            fields=["name", "disabled"],
        )
        or {}
    )

    if not doc.razorpayx_account_details and throw:
        frappe.throw(
            msg=_(
                "RazorPayX Account not found for Bank Account <strong>{0}</strong>."
            ).format(doc.bank_account),
            title=_("RazorPayX Account Not Found"),
            exc=frappe.ValidationError,
        )
    elif account := doc.razorpayx_account_details.get("name"):
        doc.db_set("razorpayx_account", account)


def set_missing_payout_details(doc: PaymentEntry):
    """
    Set missing Payout details of RazorPayX.

    - Party Bank Details
    - Payout Mode
    - Reference No

    :param doc: Payment Entry Document
    """
    set_party_bank_details(doc)
    set_payout_mode(doc)
    set_reference_no(doc)


def set_party_bank_details(doc: PaymentEntry):
    """
    Setting party's bank details to `party_bank_details`.

    Note: It is a not an actual field, it is temporary stored for validation.
    """
    doc.party_bank_account_details = frappe._dict()

    if (
        doc.party_bank_account
        and doc.razorpayx_payout_mode != USER_PAYOUT_MODE.LINK.value
    ):
        doc.party_bank_account_details = frappe.db.get_value(
            "Bank Account",
            doc.party_bank_account,
            [
                "branch_code as ifsc_code",
                "bank_account_no as account_no",
                "upi_id",
                "online_payment_mode as payment_mode",
                "disabled",
            ],
            as_dict=True,
        )


def set_payout_mode(doc: PaymentEntry):
    """
    Setting RazorPayX payout mode if not set.

    - If not set, then set based on Party Bank Details.
    - If Party Bank Details not set, then set to LINK mode.

    :param doc: Payment Entry Document
    """
    if doc.razorpayx_payout_mode:
        return

    def get_mode():
        if doc.party_bank_account:
            return doc.party_bank_details.payment_mode

        return USER_PAYOUT_MODE.LINK

    doc.db_set("razorpayx_payout_mode", get_mode())


def set_reference_no(doc: PaymentEntry):
    """
    Set Reference No for the Payment Entry if not set.

    :param doc: Payment Entry Document
    """
    if doc.reference_no:
        return

    doc.db_set("reference_no", "*** UTR WILL BE SET AUTOMATICALLY ***")


def reset_razorpayx_fields(doc: PaymentEntry):
    """
    Reset RazorPayX payout fields.

    :param doc: Payment Entry Document

    ---
    Note: Account does not reset because it is based on Bank Account.
    """
    fields = [
        # "razorpayx_account",
        "razorpayx_payout_desc",
        "razorpayx_payout_id",
        "razorpayx_payout_link_id",
    ]

    for field in fields:
        doc.set(field, "")


### ACTIONS ###
def make_payout_with_razorpayx(doc: PaymentEntry, auth_id: str | None = None):
    """
    Make Payout with RazorPayX Integration.

    :param doc: Payment Entry Document
    :param auth_id: Authentication ID (after otp or password verification)
    """
    if is_amended_pe_processed(doc):
        return

    if not can_make_payout(doc):
        frappe.throw(
            msg=_(
                "Payout cannot be made for this Payment Entry. Please check the details."
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

    if auto_cancel or should_auto_cancel_payout(doc.razorpayx_account):
        PayoutWithPaymentEntry(doc).cancel()


### UTILITY ###
def is_amended_pe_processed(doc: PaymentEntry) -> bool | int:
    """
    Check if the amended Payment Entry is processed via RazorPayX or not.

    :param doc: Payment Entry Document
    """
    if not doc.amended_from:
        return False

    return frappe.db.get_value(
        doctype="Payment Entry",
        filters=doc.amended_from,
        fieldname="make_bank_online_payment",
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
        and doc.razorpayx_account
        and doc.make_bank_online_payment
    )


def can_make_payout(doc: PaymentEntry) -> bool:
    """
    Check if the Payout can be made or not.

    :param doc: Payment Entry Document
    """
    return (
        doc.docstatus == 1
        and doc.payment_type == "Pay"
        and doc.make_bank_online_payment
        and doc.razorpayx_account
        and doc.mode_of_payment != "Cash"
        and doc.paid_from_account_currency == PAYOUT_CURRENCY.INR.value
        and not doc.razorpayx_payout_id
        and not doc.razorpayx_payout_link_id
    )


# TODO: concern with @smit_vora
def user_has_payout_permissions(
    payment_entry: str | list[str] | None = None,
    razorpayx_account: str | None = None,
    *,
    pe_permission: Literal["submit", "cancel"] = "submit",
    throw: bool = False,
):
    """
    Check RazorPayX related permissions for the user.

    Permission Check:
    - Has a role of Payout Authorizer
    - Can access particular Payment Entry
    - Can access particular RazorPayX Account (if provided)

    :param payment_entry: Payment Entry name
    :param razorpayx_account: RazorPayX Account name
    :param pe_permission: Payment Entry Permission to check
    :param throw: Throw error if permission is not granted
    """
    # this role have permission to read integration settings and submission/cancellation of payment entry
    has_role = ROLE_PROFILE.PAYOUT_AUTHORIZER.value in frappe.get_roles()

    if not has_role and throw:
        frappe.throw(
            title=_("Insufficient Permissions"),
            msg=_("You do not have permission to make payout."),
            exc=frappe.PermissionError,
        )

    has_pe_permission = frappe.has_permission(
        doctype="Payment Entry",
        doc=payment_entry,
        ptype=pe_permission,
        throw=throw,
    )

    has_razorpayx_permission = frappe.has_permission(
        doctype=INTEGRATION_DOCTYPE,
        doc=razorpayx_account,
        throw=throw,
    )

    return has_role and has_pe_permission and has_razorpayx_permission


### APIs ###
@frappe.whitelist()
# TODO: permissions ?!
def should_auto_cancel_payout(razorpayx_account: str) -> bool | int:
    """
    Check if the Payout should be auto cancelled or not.

    :param razorpayx_account: RazorPayX Account name
    """
    frappe.has_permission("Payment Entry", throw=True)

    return frappe.db.get_value(
        INTEGRATION_DOCTYPE, razorpayx_account, "auto_cancel_payout"
    )


@frappe.whitelist()
def cancel_payout(docname: str, razorpayx_account: str):
    """
    Cancel Payout or Payout Link for the Payment Entry.

    :param docname: Payment Entry name
    :param razorpayx_account: RazorPayX Account name associated to company bank account
    """
    user_has_payout_permissions(
        docname,
        razorpayx_account,
        pe_permission="cancel",
        throw=True,
    )

    doc = frappe.get_cached_doc("Payment Entry", docname)
    handle_payout_cancellation(doc, auto_cancel=True, throw=True)


@frappe.whitelist()
# TODO: ? kwargs is good or not?
def make_payout_with_payment_entry(
    auth_id: str, docname: str, razorpayx_account: str, **kwargs
):
    """
    Make Payout or Payout Link with Payment Entry.

    :param auth_id: Authentication ID (after otp or password verification)
    :param docname: Payment Entry name
    :param razorpayx_account: RazorPayX Account name associated to company bank account
    """
    user_has_payout_permissions(docname, razorpayx_account, throw=True)

    doc = frappe.get_doc("Payment Entry", docname)

    kwargs.pop("cmd")  # unwanted key

    # Set the fields to make payout
    doc.db_set(
        {
            "make_bank_online_payment": 1,
            **kwargs,
        }
    )

    validate_payout_details(doc, throw=True)
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
    user_has_payout_permissions(throw=True)

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
