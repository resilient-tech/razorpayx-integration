import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_details
from frappe.utils import get_link_to_form

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE
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
    validate_online_payment_requirements(doc)


def before_submit(doc: PaymentEntry, method=None):
    if not (doc.make_bank_online_payment and doc.razorpayx_account):
        reset_razorpayx_fields(doc)


def on_submit(doc: PaymentEntry, method=None):
    make_payout_with_razorpayx(doc)


def before_cancel(doc: PaymentEntry, method=None):
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


def validate_online_payment_requirements(doc: PaymentEntry):
    if not doc.make_bank_online_payment:
        return

    validate_razorpayx_account(doc)

    # Maybe other Integration is used
    if not doc.razorpayx_account:
        doc.make_bank_online_payment = 0
        return

    set_mandatory_payout_details(doc)
    validate_payout_details(doc)


# TODO: make it more simple?
def validate_razorpayx_account(doc: PaymentEntry, throw: bool = False):
    set_razorpayx_account(doc, throw)

    # Always throw error if account is disabled
    if doc.razorpayx_account and doc.razorpayx_account_details.disabled:
        frappe.throw(
            msg=_(
                "RazorpayX Account <strong>{0}</strong> is disabled. Please enable it first to use!"
            ).format(doc.razorpayx_account),
            title=_("Invalid RazorpayX Account"),
            exc=frappe.ValidationError,
        )


def validate_payout_details(doc: PaymentEntry):
    if doc.party_bank_account and doc.party_account_details.disabled:
        frappe.throw(
            msg=_("Party's Bank Account <strong>{0}</strong> is disabled.").format(
                doc.party_bank_account
            ),
            title=_("Invalid Bank Account"),
            exc=frappe.ValidationError,
        )

    validate_razorpayx_user_payout_mode(doc.razorpayx_payout_mode)

    validate_bank_payout_mode(doc)
    validate_upi_payout_mode(doc)
    validate_link_payout_mode(doc)


def validate_bank_payout_mode(doc: PaymentEntry):
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.BANK.value:
        return

    if doc.party_bank_account and doc.party_bank_account_no and doc.party_bank_ifsc:
        validate_ifsc_code(doc.party_bank_ifsc)
        return

    frappe.throw(
        msg=_(
            "Party's Bank Account Details is mandatory to make payment. Please set valid <strong>Party Bank Account</strong>."
        ),
        title=_("Mandatory Fields Missing"),
        exc=frappe.MandatoryError,
    )

    if doc.party_bank_account_no != doc.party_bank_details.account_no:
        frappe.throw(
            msg=_(
                "Party's Bank Account No <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_bank_account_no),
            title=_("Invalid Bank Account No"),
        )

    if doc.party_bank_ifsc != doc.party_bank_details.ifsc_code:
        frappe.throw(
            msg=_(
                "Party's Bank IFSC Code <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_bank_ifsc),
            title=_("Invalid Bank IFSC Code"),
        )


def validate_upi_payout_mode(doc: PaymentEntry):
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.UPI.value:
        return

    if doc.party_upi_id and doc.party_bank_account:
        return

    frappe.throw(
        msg=_(
            "Party's UPI ID is mandatory to make payment. Please set valid <strong>Party Bank Account</strong>."
        ),
        title=_("Mandatory Fields Missing"),
        exc=frappe.MandatoryError,
    )

    if doc.party_upi_id != doc.party_bank_details.upi_id:
        frappe.throw(
            msg=_(
                "Party's UPI ID <strong>{0}</strong> does not match with selected Party's Bank Account."
            ).format(doc.party_upi_id),
            title=_("Invalid UPI ID"),
        )


def validate_link_payout_mode(doc: PaymentEntry):
    if doc.razorpayx_payout_mode != USER_PAYOUT_MODE.LINK.value:
        return

    if not (doc.contact_mobile or doc.contact_email):
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

    # Validate email and contact is correct or not
    contact_details = get_contact_details(doc.contact_person)

    if doc.contact_mobile and doc.contact_mobile != contact_details.get("mobile_no"):
        frappe.throw(
            msg=_(
                "Contact's Mobile <strong>{0}</strong> does not match with selected Contact."
            ).format(doc.contact_mobile),
            title=_("Invalid Mobile"),
        )

    if doc.contact_email and doc.contact_email != contact_details.get("email_id"):
        frappe.throw(
            msg=_(
                "Contact's Email <strong>{0}</strong> does not match with selected Contact."
            ).format(doc.contact_email),
            title=_("Invalid Email"),
        )


#### EVENT'S HELPERS ####
# TODO: make it more simple?
def set_razorpayx_account(doc: PaymentEntry, throw: bool = False):
    if not doc.bank_account and throw:
        frappe.throw(
            msg=_("Bank Account is mandatory to make payment."),
            title=_("Mandatory Fields Missing"),
            exc=frappe.MandatoryError,
        )
    else:
        doc.razorpayx_account = ""
        return

    # Fetch RazorpayX Account based on Bank Account
    doc.razorpayx_account_details = get_razorpayx_account(
        identifier=doc.bank_account,
        search_by="bank_account",
        fields=["name", "disabled"],
    )

    if not doc.razorpayx_account_details and throw:
        frappe.throw(
            msg=_(
                "RazorPayX Account not found for Bank Account <strong>{0}</strong>."
            ).format(doc.bank_account),
            title=_("RazorPayX Account Not Found"),
            exc=frappe.ValidationError,
        )

    doc.razorpayx_account = (
        doc.razorpayx_account_details.name if doc.razorpayx_account_details else ""
    )


def set_mandatory_payout_details(doc: PaymentEntry):
    set_party_bank_details(doc)
    set_payout_mode(doc)
    set_reference_no(doc)


def set_party_bank_details(doc: PaymentEntry):
    doc.party_bank_details = frappe._dict()

    if (
        doc.party_bank_account
        and doc.razorpayx_payout_mode != USER_PAYOUT_MODE.LINK.value
    ):
        doc.party_bank_details = frappe.db.get_value(
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
    if doc.razorpayx_payout_mode:
        return

    if doc.party_bank_account:
        doc.razorpayx_payout_mode = doc.party_bank_details.payment_mode
    else:
        doc.razorpayx_payout_mode = USER_PAYOUT_MODE.LINK.value


def set_reference_no(doc: PaymentEntry):
    if doc.reference_no:
        return

    doc.reference_no = "*** UTR WILL BE SET AUTOMATICALLY ***"


def reset_razorpayx_fields(doc: PaymentEntry):
    fields = {
        "make_bank_online_payment": 0,
        "razorpayx_account": "",
        "razorpayx_payout_mode": USER_PAYOUT_MODE.LINK.value,
        "razorpayx_payout_desc": "",
        "razorpayx_payout_status": PAYOUT_STATUS.NOT_INITIATED.value.title(),
        "razorpayx_pay_instantaneously": 0,
    }

    for field, value in fields.items():
        doc[field] = value


### ACTIONS ###
def make_payout_with_razorpayx(doc: PaymentEntry, throw=False):
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


def handle_payout_cancellation(doc: PaymentEntry):
    if not doc.razorpayx_account:
        return

    if not doc.make_bank_online_payment or is_payout_already_cancelled(doc):
        return

    if can_cancel_payout(doc) and should_auto_cancel_payout(doc.razorpayx_account):
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
    return doc.make_bank_online_payment and doc.razorpayx_payout_status.lower() in [
        PAYOUT_STATUS.NOT_INITIATED.value,
        PAYOUT_STATUS.QUEUED.value,
    ]


def is_payout_already_cancelled(doc: PaymentEntry) -> bool:
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
# TODO: do not use kwargs use individual fields and validate them first!
def make_payout_with_payment_entry(docname: str, **kwargs):
    """
    Make Payout or Payout Link with Payment Entry.

    :param docname: Payment Entry name
    :param kwargs: Payout details

    """
    # Has role payment manager
    frappe.has_permission(RAZORPAYX_INTEGRATION_DOCTYPE, throw=True)

    doc = frappe.get_doc("Payment Entry", docname)
    # check razorpayx account doc permission ("read")
    doc.has_permission("submit")

    kwargs.pop("cmd")
    doc.db_set(
        {
            "make_bank_online_payment": 1,
            **kwargs,
        }
    )

    validate_online_payment_requirements(doc)
    response = make_payout_with_razorpayx(doc)

    if not response:
        doc.db_set("make_bank_online_payment", 0, update_modified=False)

    return response
