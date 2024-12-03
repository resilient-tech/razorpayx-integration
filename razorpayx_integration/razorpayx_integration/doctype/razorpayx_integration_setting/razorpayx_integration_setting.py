# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from razorpayx_integration.constants import RAZORPAYX

# TODO: add documentation tab to the doctype
# TODO: Payout settings implementation


class RazorPayXIntegrationSetting(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        account_number: DF.Data | None
        after_payment_template: DF.Link | None
        auto_generate_entries: DF.Check
        automatic_mode: DF.Link | None
        balance: DF.Currency
        bank: DF.Link | None
        bank_account: DF.Link
        before_payment_template: DF.Link | None
        company: DF.Link | None
        company_account: DF.Link | None
        disabled: DF.Check
        enable_automatic_payments: DF.Check
        ifsc_code: DF.Data | None
        invoice_level_email_template: DF.Link | None
        key_authorized: DF.Check
        key_id: DF.Data
        key_secret: DF.Password
        last_synced: DF.Datetime | None
        manual_mode: DF.Link | None
        order_to_pay: DF.Literal["Due Date", "Posting Date"]
        party_level_email_template: DF.Link | None
        pay_on_friday: DF.Check
        pay_on_monday: DF.Check
        pay_on_saturday: DF.Check
        pay_on_sunday: DF.Check
        pay_on_thursday: DF.Check
        pay_on_tuesday: DF.Check
        pay_on_wednesday: DF.Check
        payment_threshold: DF.Currency
        payouts_by: DF.Literal["By Invoices", "By Party"]
        reponsible_email: DF.Data | None
        webhook_secret: DF.Password | None

    # end: auto-generated types
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
