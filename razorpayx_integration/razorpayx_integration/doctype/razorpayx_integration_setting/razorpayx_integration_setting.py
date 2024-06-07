# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RazorPayXIntegrationSetting(Document):
    def before_save(self):
        account_no, self.bank_name = frappe.db.get_value(
            "Bank Account", self.bank_account, ["bank_account_no", "bank"]
        )

        if not account_no:
            frappe.throw(
                msg=_(
                    "Please set <em>Account Number</em> in <strong>Bank Account</strong>."
                ),
                title=_("Account Number Is Missing"),
            )
        self.account_number = account_no

    # todo: validate API credential
    def validate_api_credential(self):
        if not self.key_id or not self.key_secret:
            frappe.throw(
                msg=_("Please set RazorPayX API credentials."),
                title=_("API Credentials Are Missing"),
            )
