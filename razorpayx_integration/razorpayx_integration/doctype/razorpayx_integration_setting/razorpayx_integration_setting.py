# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from razorpayx_integration.constant import RAZORPAYX


class RazorPayXIntegrationSetting(Document):
    def validate(self):
        # todo: verify customer_identifier is valid or not ??
        self.validate_api_credentials()

    # todo: validate API credential (Are actually razorpayx credentials or not?)
    def validate_api_credentials(self):
        if not self.key_id or not self.key_secret:
            frappe.throw(
                msg=_("Please set {0} API credentials.").format(RAZORPAYX),
                title=_("API Credentials Are Missing"),
            )

    @property
    def company(self):
        return frappe.db.get_value("Bank Account", self.bank_account, "company")

    @property
    def bank(self):
        return frappe.db.get_value("Bank Account", self.bank_account, "bank")
