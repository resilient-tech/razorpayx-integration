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
        auto_submit_entries: DF.Check
        auto_submit_report: DF.Link | None
        automate_on_friday: DF.Check
        automate_on_monday: DF.Check
        automate_on_saturday: DF.Check
        automate_on_sunday: DF.Check
        automate_on_thursday: DF.Check
        automate_on_tuesday: DF.Check
        automate_on_wednesday: DF.Check
        bank_account: DF.Link
        claim_early_payment_discount: DF.Check
        company: DF.Link | None
        disabled: DF.Check
        exclude_foreign_currency_invoices: DF.Check
        ignore_blocked_invoices: DF.Check
        ignore_blocked_suppliers: DF.Check
        limit_payment_to_outstanding: DF.Check
        payment_threshold: DF.Currency
    # end: auto-generated types

    pass
