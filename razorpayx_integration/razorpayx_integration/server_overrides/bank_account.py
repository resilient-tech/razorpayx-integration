# TODO: validate if bank account is referenced in any transaction / payment entry. If yes, then do not allow to update/delete it. Error: Create a new bank account and make it default and disable this account.

from erpnext.accounts.doctype.bank_account.bank_account import (
    BankAccount as _BankAccount,
)

from razorpayx_integration.constants.workflows import WORKFLOW_STATES


# TODO: reset payment details if `is_company_account` is checked ?
# TODO: after `Rejected` / `Approved` workflow state, make form read-only ?
# TODO: fetch mobile number and email to `party_contact` and `party_email` respectively
class BankAccount(_BankAccount):
    def validate(self):
        if hasattr(_BankAccount, "validate"):
            super().validate()

        self.toggle_is_default()

    def toggle_is_default(self):
        """
        Make the `Bank Account` default based on workflow state.

        - Rejected: Make the `Bank Account` non-default
        - Approved: Make the `Bank Account` default
        """
        if self.workflow_state == WORKFLOW_STATES["Rejected"][0]:
            self.is_default = 0
        elif self.workflow_state == WORKFLOW_STATES["Approved"][0]:
            self.is_default = 1
