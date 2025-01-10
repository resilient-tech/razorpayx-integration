# TODO: validate if bank account is referenced in any transaction / payment entry.
# If yes, then do not allow to update/delete it.

import frappe
import requests
from frappe import _


#### Doc Events ####
def validate(doc, method=None):
    validate_bank_ifsc(doc)


def validate_bank_ifsc(doc, method=None):
    if not doc.branch_code or not doc.has_value_changed("branch_code"):
        return

    try:
        response = requests.get(f"https://ifsc.razorpay.com/{doc.branch_code}")
    except Exception:
        return

    if response.status_code != 200:
        frappe.throw(
            msg=_("Invalid Branch Code: <strong>{0}</strong>").format(doc.branch_code),
            title=_("Invalid Branch Code"),
        )
