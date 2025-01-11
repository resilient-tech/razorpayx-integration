# TODO: validate if bank account is referenced in any transaction / payment entry.
# If yes, then do not allow to update/delete it.

import frappe
import requests
from frappe import _

from razorpayx_integration.payment_utils.utils.validations import validate_ifsc_code


#### Doc Events ####
def validate(doc, method=None):
    pass
    # validate_branch_code(doc) # ! Other countries may have different branch codes format


def validate_branch_code(doc, method=None):
    if not doc.branch_code or not doc.has_value_changed("branch_code"):
        return

    validate_ifsc_code(doc.branch_code)
