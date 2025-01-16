from typing import Literal

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_details
from frappe.utils import get_link_to_form

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE as INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.utils.validations import validate_ifsc_code
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


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload("disable_payout_fields", is_amended_pe_processed(doc))


def validate(doc: PaymentEntry, method=None):
    validate_amended_pe(doc)
    validate_payout_details(doc)


def before_submit(doc: PaymentEntry, method=None):
    if not (doc.make_bank_online_payment and doc.razorpayx_account):
        reset_razorpayx_fields(doc)


def on_submit(doc: PaymentEntry, method=None):
    make_payout_with_razorpayx(doc)


def before_cancel(doc: PaymentEntry, method=None):
    # PE is cancelled by RazorPayX webhook or PE is cancelled when payout got cancelled
    if doc.flags.__canceled_by_rpx:
        return

    handle_payout_cancellation(doc)


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
        doc.razorpayx_account = account


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

    if doc.party_bank_account:
        doc.razorpayx_payout_mode = doc.party_bank_details.payment_mode
    else:
        doc.razorpayx_payout_mode = USER_PAYOUT_MODE.LINK.value


def set_reference_no(doc: PaymentEntry):
    """
    Set Reference No for the Payment Entry if not set.

    :param doc: Payment Entry Document
    """
    if doc.reference_no:
        return

    doc.reference_no = "*** UTR WILL BE SET AUTOMATICALLY ***"


def reset_razorpayx_fields(doc: PaymentEntry):
    """
    Reset RazorPayX payout fields.

    :param doc: Payment Entry Document
    """
    fields = [
        "razorpayx_account",
        "razorpayx_payout_desc",
        "razorpayx_payout_id",
        "razorpayx_payout_link_id",
    ]

    for field in fields:
        doc.set(field, "")


### ACTIONS ###
def make_payout_with_razorpayx(doc: PaymentEntry, throw=False):
    """
    Make Payout with RazorPayX Integration.

    :param doc: Payment Entry Document
    :param throw: Throw error if Payout cannot be made, otherwise just return
    """
    if not can_make_payout(doc):
        if throw:
            frappe.throw(
                msg=_(
                    "Payout cannot be made for this Payment Entry. Please check the details."
                ),
                title=_("Invalid Payment Entry"),
            )

        return

    PayoutWithPaymentEntry(doc).make_payout()


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
        and not doc.razorpayx_payout_id
        and not doc.razorpayx_payout_link_id
        and not is_amended_pe_processed(doc)
    )


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
        razorpayx_account,
        docname,
        pe_permission="cancel",
        throw=True,
    )

    doc = frappe.get_cached_doc("Payment Entry", docname)
    handle_payout_cancellation(doc, auto_cancel=True, throw=True)


@frappe.whitelist()
# TODO: ? kwargs is good or not?
def make_payout_with_payment_entry(docname: str, razorpayx_account: str, **kwargs):
    """
    Make Payout or Payout Link with Payment Entry.

    :param docname: Payment Entry name
    :param razorpayx_account: RazorPayX Account name associated to company bank account
    """
    user_has_payout_permissions(razorpayx_account, docname, throw=True)

    doc = frappe.get_doc("Payment Entry", docname)
    doc.has_permission("submit")

    kwargs.pop("cmd")  # unwanted key

    # Set the fields to make payout
    doc.db_set(
        {
            "make_bank_online_payment": 1,
            **kwargs,
        }
    )

    validate_payout_details(doc, throw=True)
    make_payout_with_razorpayx(doc)


@frappe.whitelist()
def user_has_payout_permissions(
    razorpayx_account: str,
    payment_entry: str,
    *,
    pe_permission: Literal["submit", "cancel"] = "submit",
    throw: bool = False,
):
    """
    Check RazorPayX related permissions for the user.

    Permission Check:
    - Can access the integration doctypes
    - Can access particular RazorPayX Account
    - Can access particular Payment Entry

    :param razorpayx_account: RazorPayX Account name
    :param payment_entry: Payment Entry name
    :param pe_permission: Payment Entry Permission to check
    :param throw: Throw error if permission is not granted
    """
    return (
        frappe.has_permission(INTEGRATION_DOCTYPE, throw=throw)
        and frappe.has_permission(
            doctype=INTEGRATION_DOCTYPE,
            doc=razorpayx_account,
            throw=throw,
        )
        and frappe.has_permission(
            doctype="Payment Entry",
            doc=payment_entry,
            ptype=pe_permission,
            throw=throw,
        )
    )
