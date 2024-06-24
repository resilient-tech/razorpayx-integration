# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from razorpayx_integration.constant import RAZORPAYX


class RazorPayXIntegrationSetting(Document):
    def validate(self):
        self.validate_bank_account()
        self.validate_api_credential()

    # ? unnecessary
    def validate_bank_account(self):
        bank_account_details = frappe.db.get_value(
            "Bank Account", self.bank_account, ["bank_account_no", "bank"]
        )

        if not bank_account_details:
            frappe.throw(
                msg=_("No details found for the selected Bank Account: {0}").format(
                    frappe.bold(self.bank_account)
                ),
                title=_("Invalid Bank Account"),
            )

        if (
            bank_account_details[0] != self.account_number
            or bank_account_details[1] != self.bank_name
        ):
            frappe.throw(
                msg=_(
                    "Given bank account details do not match the selected Bank Account: {0}"
                ).format(frappe.bold(self.bank_account)),
                title=_("Invalid Bank Account Details"),
            )

    # todo: validate API credential (Are actually razorpayx credentials or not?)
    def validate_api_credential(self):
        if not self.key_id or not self.key_secret:
            frappe.throw(
                msg=_("Please set {0} API credentials.").format(RAZORPAYX),
                title=_("API Credentials Are Missing"),
            )
