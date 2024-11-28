# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from razorpayx_integration.constants import RAZORPAYX


class RazorPayXIntegrationSetting(Document):
    def validate(self):
        self.validate_api_credentials()

    # todo: validate API credential (Are actually razorpayx credentials or not?)
    def validate_api_credentials(self):
        if not self.key_id or not self.key_secret:
            frappe.throw(
                msg=_("Please set {0} API credentials.").format(RAZORPAYX),
                title=_("API Credentials Are Missing"),
            )


# Time for creation and payment with checkbox (description) for payment entry.
# Payout settings. To determine which invoices to pay.
# 1. Payment Entry Creation: By Party / By Invoice
# 2. Sequence: By Posting Date / By Due Date: (relevant for insufficent funds)
# 3. Enqueue payout if insufficent funds. If this is not checked, don't submit the payment entry as long as funds are not available.
# Documentation HTML. RTGS / NEFT.
