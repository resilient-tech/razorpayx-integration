# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PaymentSetting(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        auto_generate_entries: DF.Check
        automate_on_friday: DF.Check
        automate_on_monday: DF.Check
        automate_on_saturday: DF.Check
        automate_on_sunday: DF.Check
        automate_on_thursday: DF.Check
        automate_on_tuesday: DF.Check
        automate_on_wednesday: DF.Check
        balance: DF.Currency
        bank_account: DF.Link
        company: DF.Link | None
        disabled: DF.Check
        enable_automatic_payments: DF.Check
        order_to_pay: DF.Literal["Due Date", "Posting Date"]
        payment_success_template: DF.Link | None
        payment_threshold: DF.Currency
        payouts_by: DF.Literal["Invoices", "Party"]
        report_after_auto_payments: DF.Link | None
        report_before_auto_payments: DF.Link | None
    # end: auto-generated types
    pass
