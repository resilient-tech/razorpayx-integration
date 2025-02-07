import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

from razorpayx_integration.payment_utils.auth import (
    run_before_payment_authentication as has_payout_permissions,
)


#### DOC EVENTS ####
def onload(doc: PaymentEntry, method=None):
    doc.set_onload(
        "has_payout_permission", has_payout_permissions(doc.name, throw=False)
    )
