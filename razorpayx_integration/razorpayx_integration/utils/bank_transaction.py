from typing import Literal

import frappe
from frappe import _
from frappe.utils import DateTimeLikeObject, getdate
from payment_integration_utils.payment_integration_utils.constants.enums import BaseEnum
from payment_integration_utils.payment_integration_utils.utils import (
    get_str_datetime_from_epoch,
    paisa_to_rupees,
)

from razorpayx_integration.constants import RAZORPAYX_CONFIG
from razorpayx_integration.razorpayx_integration.apis.transaction import (
    RazorpayXTransaction,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import PAYOUT_FROM
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    TRANSACTION_TYPE as ENTITY,
)
from razorpayx_integration.razorpayx_integration.utils import get_payouts_made_from


######### PROCESSOR #########
class RazorpayXBankTransaction:
    def __init__(
        self,
        razorpayx_config: str,
        from_date: DateTimeLikeObject | None = None,
        to_date: DateTimeLikeObject | None = None,
        *,
        bank_account: str | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ):
        self.razorpayx_config = razorpayx_config
        self.from_date = from_date
        self.to_date = to_date
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        self.set_bank_account(bank_account)

    def set_bank_account(self, bank_account: str | None = None):
        if not bank_account:
            bank_account = frappe.db.get_value(
                doctype=RAZORPAYX_CONFIG,
                filters=self.razorpayx_config,
                fieldname="bank_account",
            )

        if not bank_account:
            frappe.throw(
                msg=_(
                    "Company Bank Account not found for RazorpayX Configuration <strong>{0}</strong>"
                ).format(self.razorpayx_config),
                title=_("Company Bank Account Not Found"),
            )

        self.bank_account = bank_account

    def sync(self):
        transactions = self.fetch_transactions()

        if not transactions:
            return

        existing_transactions = self.get_existing_transactions(transactions)

        for transaction in transactions:
            if transaction["id"] in existing_transactions:
                continue

            self.create(self.map(transaction))

    def fetch_transactions(self) -> list[dict] | None:
        """
        Fetching Bank Transactions from RazorpayX API.
        """
        try:
            return RazorpayXTransaction(self.razorpayx_config).get_all(
                from_date=self.from_date,
                to_date=self.to_date,
                source_doctype=self.source_doctype,
                source_docname=self.source_docname,
            )

        except Exception:
            frappe.log_error(
                title=(
                    f"Failed to Fetch RazorpayX Transactions for Config: {self.razorpayx_config}"
                ),
                message=frappe.get_traceback(),
                reference_doctype=RAZORPAYX_CONFIG,
                reference_name=self.razorpayx_config,
            )

    def get_existing_transactions(self, transactions: list[str]) -> set[str]:
        """
        Get existing bank account transactions from the ERPNext database.

        :param transactions: List of transactions from RazorpayX API.
        """
        return set(
            frappe.get_all(
                "Bank Transaction",
                filters={
                    "bank_account": self.bank_account,
                    "transaction_id": (
                        "in",
                        {transaction["id"] for transaction in transactions},
                    ),
                },
                pluck="transaction_id",
            )
        )

    def map(self, transaction: dict):
        """
        Map RazorpayX transaction to ERPNext's Bank Transaction.

        :param transaction: RazorpayX Transaction
        """

        def get_description(source: dict) -> str | None:
            # TODO: Needs description of payout/bank transfer or other transactions
            notes = source.get("notes") or {}

            if not notes:
                return

            description = ""
            source_doctype = notes.get("source_doctype")
            source_docname = notes.get("source_docname")

            if source_doctype and source_docname:
                description = f"{source_doctype}: {source_docname}"

            if desc := notes.get("description"):
                description += f"\nNarration: {desc}"

            if not description:
                description = "\n".join(notes.values())

            return description

        # Some transactions do not have source
        source = transaction.get("source") or {}

        mapped = {
            "doctype": "Bank Transaction",
            "bank_account": self.bank_account,
            "transaction_id": transaction["id"],
            "date": get_str_datetime_from_epoch(transaction["created_at"]),
            "deposit": paisa_to_rupees(transaction["credit"]),
            "withdrawal": paisa_to_rupees(transaction["debit"]),
            "closing_balance": paisa_to_rupees(transaction["balance"]),
            "currency": transaction["currency"],
            "transaction_type": source.get("mode"),
            "description": get_description(source),
            "reference_number": source.get("utr") or source.get("bank_reference"),
        }

        # auto reconciliation
        # TODO: fees deduction at the end of the day is not handled
        mapped["payment_entries"] = []
        self.set_matching_payment_entry(mapped, source)
        self.set_matching_journal_entry(mapped, source)

        return mapped

    def set_matching_payment_entry(self, mapped: dict, source: dict | None = None):
        """
        Setting matching Payment Entry for the Bank Reconciliation.

        :param mapped: Mapped Bank Transaction
        :param source: Source of the transaction (In transaction response)

        ---
        Note:
        - Payment Entry will be find by `Payout ID` or `UTR`.
        - For `reversal` entity it returns without finding PE.
        """
        if not source or source.get("entity") == ENTITY.REVERSAL.value:
            return

        def get_payment_entry(**filters):
            # TODO: confirm company or bank account
            return frappe.db.get_value(
                "Payment Entry",
                {
                    "docstatus": 1,
                    "clearance_date": ["is", "not set"],
                    **filters,
                },
                fieldname=["name", "paid_amount"],
                order_by="creation desc",  # to get latest
                as_dict=True,
            )

        payment_entry = None

        # reconciliation with payout_id or bank_reference
        if source.get("entity") == ENTITY.PAYOUT.value:
            payment_entry = get_payment_entry(razorpayx_payout_id=source["id"])
        elif source.get("entity") == ENTITY.BANK_TRANSFER.value:
            payment_entry = get_payment_entry(reference_no=source["bank_reference"])

        # reconciliation with reference number (UTR)
        if not payment_entry and source.get("utr"):
            payment_entry = get_payment_entry(reference_no=mapped["reference_number"])

        if not payment_entry:
            return

        mapped["payment_entries"].append(
            {
                "payment_document": "Payment Entry",
                "payment_entry": payment_entry.name,
                "allocated_amount": payment_entry.paid_amount,
            }
        )

    def set_matching_journal_entry(self, mapped: dict, source: dict | None = None):
        """
        Setting matching Journal Entry for the Bank Reconciliation.

        :param mapped: Mapped Bank Transaction
        :param source: Source of the transaction (In transaction response)

        ---
        Note:
            - For reversal, two transactions will be created.
                - simple transaction with reversal id
                - payout reversal transaction with payout id
            - JE created only when payout processed or reversed
            - JE will be find by  `Payout ID` or `Reversal ID` or `UTR` or `Bank Reference`.
        """
        if not source:
            return

        payouts_from = get_payouts_made_from(self.razorpayx_config)

        def get_journal_entry(
            check_no: str,
            reversal_of: Literal["set", "not set"],
        ) -> dict | None:
            return frappe.db.get_value(
                "Journal Entry",
                {
                    "is_system_generated": 1,
                    "docstatus": 1,
                    "difference": 0,
                    "cheque_no": check_no,
                    "reversal_of": ["is", reversal_of],
                },
                fieldname=["name", "total_debit"],
                as_dict=True,
            )

        def is_current_account_payout() -> bool:
            return payouts_from == PAYOUT_FROM.CURRENT_ACCOUNT.value

        entity = source.get("entity")

        # for current account payouts, fees will not be deducted immediately but JE will be created
        if entity == ENTITY.PAYOUT.value and is_current_account_payout():
            return

        # get cheque no to fetch JE
        cheque_no = ""

        if entity in [ENTITY.PAYOUT.value, ENTITY.REVERSAL.value]:
            cheque_no = source.get("id")
        elif entity == ENTITY.BANK_TRANSFER.value:
            cheque_no = source.get("bank_reference")
        else:
            cheque_no = source.get("utr")

        if not cheque_no:
            return

        # finding Fees JE or Payout Reversal JE with `cheque_no`
        # Note: for fees `check_no` is payout_id and for reversal `check_no` is reversal_id
        journal_entry = get_journal_entry(cheque_no, "not set")

        if journal_entry:
            mapped["payment_entries"].append(
                {
                    "payment_document": "Journal Entry",
                    "payment_entry": journal_entry.name,
                    "allocated_amount": journal_entry.total_debit,
                }
            )

        if entity != "reversal" or is_current_account_payout():
            return

        # get fees reversal JE (Only for RazorpayX Lite)
        fees_reversal_je = get_journal_entry(cheque_no, "set")

        if not fees_reversal_je:
            return

        mapped["payment_entries"].append(
            {
                "payment_document": "Journal Entry",
                "payment_entry": fees_reversal_je.name,
                "allocated_amount": fees_reversal_je.total_debit,
            }
        )

    # TODO: can use bulk insert?
    def create(self, mapped_transaction: dict):
        """
        Create Bank Transaction in the ERPNext.

        :param mapped_transaction: Mapped Bank Transaction
        """
        return (
            frappe.get_doc(mapped_transaction).insert(ignore_permissions=True).submit()
        )


######### APIs #########
@frappe.whitelist()
def sync_transactions_for_reconcile(
    bank_account: str, razorpayx_config: str | None = None
):
    """
    Sync RazorpayX bank account transactions.

    Syncs from the last sync date to the current date.

    If last sync date is not set, it will sync all transactions.

    :param bank_account: Company Bank Account
    :param razorpayx_config: RazorpayX Configuration
    """
    BRT = "Bank Reconciliation Tool"
    frappe.has_permission(BRT, throw=True)

    if not razorpayx_config:
        razorpayx_config = frappe.db.get_value(
            RAZORPAYX_CONFIG, {"bank_account": bank_account, "disabled": 0}
        )

    if not razorpayx_config:
        frappe.throw(
            _(
                "RazorpayX Configuration not found for Bank Account <strong>{0}</strong>"
            ).format(bank_account)
        )

    RazorpayXBankTransaction(
        razorpayx_config,
        bank_account=bank_account,
        source_docname=BRT,
        source_doctype=BRT,
    ).sync()


# TODO: we need to enqueue this or not!!
@frappe.whitelist()
def sync_bank_transactions_with_razorpayx(
    razorpayx_config: str,
    from_date: DateTimeLikeObject,
    to_date: DateTimeLikeObject,
    bank_account: str | None = None,
):
    """
    Sync RazorpayX bank account transactions.

    :param razorpayx_config: RazorpayX Configuration which has the bank account.
    :param from_date: Start Date
    :param to_date: End Date
    :param bank_account: Company Bank Account
    """
    frappe.has_permission(RAZORPAYX_CONFIG, throw=True)

    RazorpayXBankTransaction(
        razorpayx_config,
        from_date,
        to_date,
        bank_account=bank_account,
        source_doctype=RAZORPAYX_CONFIG,
        source_docname=razorpayx_config,
    ).sync()


def sync_transactions_periodically():
    """
    Sync all enabled RazorpayX bank account transactions.

    Called by scheduler.
    """
    today = getdate()

    configs = frappe.get_all(
        doctype=RAZORPAYX_CONFIG,
        filters={"disabled": 0},
        fields=["name", "bank_account"],
    )

    if not configs:
        return

    for config in configs:
        RazorpayXBankTransaction(config.name, bank_account=config.bank_account).sync()

    # update last sync date
    frappe.db.set_value(
        RAZORPAYX_CONFIG,
        {"name": ("in", {config.name for config in configs})},
        "last_sync_on",
        today,
    )
