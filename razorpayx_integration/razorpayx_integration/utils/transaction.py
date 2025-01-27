import frappe
from frappe import _
from frappe.utils import DateTimeLikeObject, getdate

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE as INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.utils import (
    get_str_datetime_from_epoch,
    paisa_to_rupees,
)
from razorpayx_integration.razorpayx_integration.apis.transaction import (
    RazorPayXTransaction,
)


@frappe.whitelist()
def sync_transactions_for_reconcile(bank_account: str):
    """
    Sync RazorPayX bank account transactions.

    Syncs from the last sync date to the current date.

    If last sync date is not set, it will sync all transactions.

    :param bank_account: Company Bank Account
    """
    BRT = "Bank Reconciliation Tool"
    frappe.has_permission(BRT, throw=True)

    razorpayx_setting = frappe.db.get_value(
        INTEGRATION_DOCTYPE, {"bank_account": bank_account}
    )

    if not razorpayx_setting:
        frappe.throw(
            _("RazorPayX Integration Setting not found for Bank Account {0}").format(
                bank_account
            )
        )

    RazorpayBankTransaction(
        razorpayx_setting, source_docname=BRT, source_doctype=BRT
    ).sync()


# TODO: we need to enqueue this or not!!
@frappe.whitelist()
def sync_razorpayx_transactions(
    razorpayx_setting: str, from_date: DateTimeLikeObject, to_date: DateTimeLikeObject
):
    """
    Sync bank transactions for the given RazorPayX account.

    :param razorpayx_setting: RazorPayX Integration Setting which has the bank account.
    :param from_date: Start Date
    :param to_date: End Date
    """
    frappe.has_permission(INTEGRATION_DOCTYPE, throw=True)

    RazorpayBankTransaction(
        razorpayx_setting,
        from_date,
        to_date,
        source_doctype=INTEGRATION_DOCTYPE,
        source_docname=razorpayx_setting,
    ).sync()


def sync_transactions_periodically():
    """
    Sync all enabled RazorPayX bank account transactions.

    Called by scheduler.
    """
    today = getdate()

    for setting in frappe.get_all(
        INTEGRATION_DOCTYPE, filters={"disabled": 0}, fields=["name"]
    ):
        RazorpayBankTransaction(setting["name"]).sync()

        frappe.db.set_value(INTEGRATION_DOCTYPE, setting["name"], "last_sync_on", today)


class RazorpayBankTransaction:
    def __init__(
        self,
        razorpayx_setting: str,
        from_date: DateTimeLikeObject | None = None,
        to_date: DateTimeLikeObject | None = None,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ):
        self.razorpayx_setting = razorpayx_setting
        self.from_date = from_date
        self.to_date = to_date
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        self.bank_account = frappe.db.get_value(
            INTEGRATION_DOCTYPE, razorpayx_setting, "bank_account"
        )

    def sync(self):
        transactions = self.fetch_transactions()

        if not transactions:
            return

        existing_transactions = self.get_existing_transactions(transactions)

        for transaction in transactions:
            if transaction["id"] in existing_transactions:
                continue

            self.create(self.map(transaction))

    def fetch_transactions(self):
        try:
            return RazorPayXTransaction(self.razorpayx_setting).get_all(
                from_date=self.from_date,
                to_date=self.to_date,
                source_doctype=self.source_doctype,
                source_docname=self.source_docname,
            )

        except Exception:
            frappe.log_error(
                message=frappe.get_traceback(),
                title=(
                    f"Failed to Fetch RazorPayX Transactions for Account: {self.razorpayx_setting}"
                ),
            )

    def get_existing_transactions(self, transactions: list):
        transaction_ids = [transaction["id"] for transaction in transactions]

        return set(
            frappe.get_all(
                "Bank Transaction",
                filters={
                    "bank_account": self.bank_account,
                    "transaction_id": ("in", transaction_ids),
                },
                pluck="transaction_id",
            )
        )

    def map(self, transaction: dict):
        def format_notes(notes):
            # TODO: notes for external transactions
            if isinstance(notes, dict):
                return "\n".join(notes.values())
            elif isinstance(notes, list | tuple):
                return "\n".join(notes)
            return notes

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
            "transaction_type": source.get("mode", ""),
            "description": format_notes(source.get("notes", "")),
            "reference_number": source.get("utr") or source.get("bank_reference"),
        }

        # auto reconciliation
        self.set_matching_payment_entry(mapped, source)

        return mapped

    def set_matching_payment_entry(self, mapped: dict, source: dict | None = None):
        if not source:
            return

        def get_payment_entry(**filters):
            # TODO: confirm company or bank account
            return frappe.db.get_value(
                "Payment Entry",
                {"docstatus": 1, "clearance_date": ["is", "not set"], **filters},
                fieldname=["name", "paid_amount"],
                as_dict=True,
            )

        payment_entry = None

        # reconciliation with payout_id
        if source.get("entity") == "payout":
            payment_entry = get_payment_entry(razorpayx_payout_id=source["id"])

        # reconciliation with reference number
        if not payment_entry and source.get("utr"):
            payment_entry = get_payment_entry(reference_no=mapped["reference_number"])

        if not payment_entry:
            return

        mapped["payment_entries"] = [
            {
                "payment_document": "Payment Entry",
                "payment_entry": payment_entry["name"],
                "allocated_amount": payment_entry["paid_amount"],
            }
        ]

    def create(self, mapped_transaction: dict):
        return frappe.get_doc(mapped_transaction).insert()
