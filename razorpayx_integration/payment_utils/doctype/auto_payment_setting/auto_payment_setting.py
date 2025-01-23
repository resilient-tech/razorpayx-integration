# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

# Auto Payment Setting
# Payouts not required
# validate one setting per company is enabled
# Single


class AutoPaymentSetting(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        auto_generate_entries: DF.Check
        auto_generate_report: DF.Link | None
        auto_submit_report: DF.Link | None
        automate_on_friday: DF.Check
        automate_on_monday: DF.Check
        automate_on_saturday: DF.Check
        automate_on_sunday: DF.Check
        automate_on_thursday: DF.Check
        automate_on_tuesday: DF.Check
        automate_on_wednesday: DF.Check
        bank_account: DF.Link
        company: DF.Link | None
        disabled: DF.Check
        enable_automatic_payments: DF.Check
        payment_threshold: DF.Currency
    # end: auto-generated types

    pass
