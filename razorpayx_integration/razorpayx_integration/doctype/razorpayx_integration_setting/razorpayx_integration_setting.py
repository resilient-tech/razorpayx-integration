# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from razorpayx_integration.constants import RAZORPAYX
from razorpayx_integration.payment_utils.constants.workflows import WORKFLOW_STATE


class RazorPayXIntegrationSetting(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        account_id: DF.Data
        account_number: DF.Data | None
        auto_cancel_payout: DF.Check
        balance: DF.Currency
        bank: DF.Link | None
        bank_account: DF.Link
        company: DF.Link | None
        company_account: DF.Link | None
        disabled: DF.Check
        ifsc_code: DF.Data | None
        key_id: DF.Data
        key_secret: DF.Password
        payment_success_template: DF.Link | None
        webhook_secret: DF.Password | None

    # end: auto-generated types
    def validate(self):
        self.validate_api_credentials()
        self.validate_bank_account()

    def validate_api_credentials(self):
        if not self.key_id or not self.key_secret:
            frappe.throw(
                msg=_("Please set {0} API credentials.").format(RAZORPAYX),
                title=_("API Credentials Are Missing"),
            )

        # TODO: use details to fetch account statement for one day and check if it is working.

    def validate_bank_account(self):
        if not self.bank_account:
            frappe.throw(
                msg=_("Please set Bank Account."),
                title=_("Bank Account Is Missing"),
            )

        bank_account = frappe.get_value(
            "Bank Account",
            self.bank_account,
            ["disabled", "razorpayx_workflow_state", "is_company_account"],
            as_dict=True,
        )

        if not bank_account:
            frappe.throw(
                msg=_("Bank Account not found."),
                title=_("Invalid Bank Account"),
            )

        # ! ERROR: Maybe fails
        # if (
        #     bank_account.razorpayx_workflow_state
        #     and bank_account.razorpayx_workflow_state != WORKFLOW_STATE.APPROVED.value
        # ):
        #     frappe.throw(
        #         msg=_("Bank Account is not approved. Please approve it first."),
        #         title=_("Invalid Bank Account"),
        #     )

        if bank_account.disabled:
            frappe.throw(
                msg=_("Bank Account is disabled. Please enable it first."),
                title=_("Invalid Bank Account"),
            )

        if not bank_account.is_company_account:
            frappe.throw(
                msg=_("Bank Account is not a company's bank account."),
                title=_("Invalid Bank Account"),
            )


# Time for creation and payment with checkbox (description) for payment entry.
# Payout settings. To determine which invoices to pay.
# 1. Payment Entry Creation: By Party / By Invoice
# 2. Sequence: By Posting Date / By Due Date: (relevant for insufficent funds)
# 3. Enqueue payout if insufficent funds. If this is not checked, don't submit the payment entry as long as funds are not available.
# Documentation HTML. RTGS / NEFT.
