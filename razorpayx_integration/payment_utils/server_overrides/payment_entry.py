import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

from razorpayx_integration.payment_utils.auth import (
    run_before_payment_authentication as has_payout_permissions,
)
from razorpayx_integration.payment_utils.constants.payments import (
    TRANSFER_METHOD as PAYMENT_MODE,
)

BANK_MODES = [PAYMENT_MODE.IMPS.value, PAYMENT_MODE.NEFT.value, PAYMENT_MODE.RTGS.value]


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload(
        "has_payout_permission", has_payout_permissions(doc.name, throw=False)
    )


def validate(doc: PaymentEntry, method=None):
    if (
        not doc.make_bank_online_payment
        or not doc.integration_docname
        or not doc.integration_doctype
    ):
        return

    validate_payment_modes(doc, method)


def validate_payment_modes(doc: PaymentEntry, method=None):
    validate_bank_payment_mode(doc, method)
    validate_upi_payment_mode(doc, method)
    validate_link_payment_mode(doc, method)


def validate_bank_payment_mode(doc: PaymentEntry, method=None):
    if doc.payment_transfer_method not in BANK_MODES:
        return


def validate_upi_payment_mode(doc: PaymentEntry, method=None):
    pass


def validate_link_payment_mode(doc: PaymentEntry, method=None):
    pass
