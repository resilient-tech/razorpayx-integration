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


######### PROCESSOR #########
class RazorpayBankTransaction:
    def __init__(
        self,
        razorpayx_setting: str,
        from_date: DateTimeLikeObject | None = None,
        to_date: DateTimeLikeObject | None = None,
        *,
        bank_account: str | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ):
        self.razorpayx_setting = razorpayx_setting
        self.from_date = from_date
        self.to_date = to_date
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        self.set_bank_account(bank_account)

    def set_bank_account(self, bank_account: str | None = None):
        if not bank_account:
            bank_account = frappe.db.get_value(
                doctype=INTEGRATION_DOCTYPE,
                filters=self.razorpayx_setting,
                fieldname="bank_account",
            )

        if not bank_account:
            frappe.throw(
                msg=_(
                    "Company Bank Account not found for RazorPayX Integration Setting <strong>{0}</strong>"
                ).format(self.razorpayx_setting),
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
        Fetching Bank Transactions from RazorPayX API.
        """
        try:
            return RazorPayXTransaction(self.razorpayx_setting).get_all(
                from_date=self.from_date,
                to_date=self.to_date,
                source_doctype=self.source_doctype,
                source_docname=self.source_docname,
            )

        except Exception:
            frappe.log_error(
                title=(
                    f"Failed to Fetch RazorPayX Transactions for Setting: {self.razorpayx_setting}"
                ),
                message=frappe.get_traceback(),
                reference_doctype=INTEGRATION_DOCTYPE,
                reference_name=self.razorpayx_setting,
            )

    def get_existing_transactions(self, transactions: list[str]) -> set[str]:
        """
        Get existing bank account transactions from the ERPNext database.

        :param transactions: List of transactions from RazorPayX API.
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
        Map RazorPayX transaction to ERPNext's Bank Transaction.

        :param transaction: RazorPayX Transaction
        """

        def format_notes(source):
            # TODO: Needs description of payout/bank transfer or other transactions
            notes = source.get("notes")

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
            "transaction_type": source.get("mode"),
            "description": format_notes(source),
            "reference_number": source.get("utr") or source.get("bank_reference"),
        }

        # auto reconciliation
        self.set_matching_payment_entry(mapped, source)

        return mapped

    def set_matching_payment_entry(self, mapped: dict, source: dict | None = None):
        """
        Setting matching Payment Entry for the Bank Reconciliation.

        :param mapped: Mapped Bank Transaction
        :param source: Source of the transaction (In transaction response)
        """
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
                "payment_entry": payment_entry.name,
                "allocated_amount": payment_entry.paid_amount,
            }
        ]

    # TODO: can use bulk insert?
    def create(self, mapped_transaction: dict):
        """
        Create Bank Transaction in the ERPNext.

        :param mapped_transaction: Mapped Bank Transaction
        """
        return frappe.get_doc(mapped_transaction).insert()


######### APIs #########
@frappe.whitelist()
def sync_transactions_for_reconcile(
    bank_account: str, razorpayx_setting: str | None = None
):
    """
    Sync RazorPayX bank account transactions.

    Syncs from the last sync date to the current date.

    If last sync date is not set, it will sync all transactions.

    :param bank_account: Company Bank Account
    :param razorpayx_setting: RazorPayX Integration Setting
    """
    BRT = "Bank Reconciliation Tool"
    frappe.has_permission(BRT, throw=True)

    if not razorpayx_setting:
        razorpayx_setting = frappe.db.get_value(
            INTEGRATION_DOCTYPE, {"bank_account": bank_account, "disabled": 0}
        )

    if not razorpayx_setting:
        frappe.throw(
            _(
                "RazorPayX Integration Setting not found for Bank Account <strong>{0}</strong>"
            ).format(bank_account)
        )

    RazorpayBankTransaction(
        razorpayx_setting,
        bank_account=bank_account,
        source_docname=BRT,
        source_doctype=BRT,
    ).sync()


# TODO: we need to enqueue this or not!!
@frappe.whitelist()
def sync_razorpayx_transactions(
    razorpayx_setting: str,
    from_date: DateTimeLikeObject,
    to_date: DateTimeLikeObject,
    bank_account: str | None = None,
):
    """
    Sync RazorPayX bank account transactions.

    :param razorpayx_setting: RazorPayX Integration Setting which has the bank account.
    :param from_date: Start Date
    :param to_date: End Date
    :param bank_account: Company Bank Account
    """
    frappe.has_permission(INTEGRATION_DOCTYPE, throw=True)

    RazorpayBankTransaction(
        razorpayx_setting,
        from_date,
        to_date,
        bank_account=bank_account,
        source_doctype=INTEGRATION_DOCTYPE,
        source_docname=razorpayx_setting,
    ).sync()


def sync_transactions_periodically():
    """
    Sync all enabled RazorPayX bank account transactions.

    Called by scheduler.
    """
    today = getdate()

    settings = frappe.get_all(
        doctype=INTEGRATION_DOCTYPE,
        filters={"disabled": 0},
        fields=["name", "bank_account"],
    )

    if not settings:
        return

    for setting in settings:
        RazorpayBankTransaction(setting.name, bank_account=setting.bank_account).sync()

    # update last sync date
    frappe.db.set_value(
        INTEGRATION_DOCTYPE,
        {"name": ("in", {setting.name for setting in settings})},
        "last_sync_on",
        today,
    )
