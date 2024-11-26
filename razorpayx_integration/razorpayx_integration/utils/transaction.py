from typing import Optional

import frappe
from frappe.utils import DateTimeLikeObject, now_datetime

from razorpayx_integration.constants import (
    BANK_TRANSACTION_DOCTYPE,
    RAZORPAYX_SETTING_DOCTYPE,
)
from razorpayx_integration.razorpayx_integration.apis.transaction import (
    RazorPayXTransaction,
)
from razorpayx_integration.utils import get_str_datetime_from_epoch, paisa_to_rupees


# todo: this file need to be refactor and optimize
@frappe.whitelist()
def sync_bank_transactions(bank_account: str, from_date: DateTimeLikeObject):
    frappe.has_permission(RAZORPAYX_SETTING_DOCTYPE, bank_account, throw=True)
    frappe.has_permission(BANK_TRANSACTION_DOCTYPE, throw=True)

    return sync_razorpayx_bank_transactions(
        bank_account, from_date
    )  # ? how to handle error properly


def sync_razorpayx_bank_transactions(
    account: str,
    from_date: DateTimeLikeObject,
    to_date: Optional[DateTimeLikeObject] = None,
):
    try:
        # getting all transactions from razorpayx according to date range
        razorpayx_transactions = get_razorpayx_transactions(account, from_date, to_date)

        # get existing transaction ids
        existing_transactions = get_existing_transactions(account)
        # saving transactions in Bank Transaction
        for transaction in razorpayx_transactions:
            try:
                if transaction.get("id") in existing_transactions:
                    continue

                doc = get_mapped_razorpayx_transaction(
                    transaction, bank_account=account
                )

                frappe.get_doc(doc).insert()

            except KeyError:
                frappe.log_error(
                    message=("Transaction Data: \n {0} \n\n {1}").format(
                        frappe.as_json(transaction, indent=4),
                        frappe.get_traceback(),
                    ),
                    title="Key Missing in Transaction Data",
                )
                return

            except Exception:
                frappe.log_error(
                    message=("Transaction Data: \n {0} \n\n {1}").format(
                        frappe.as_json(transaction, indent=4),
                        frappe.get_traceback(),
                    ),
                    title=("Failed to Save Transaction: {0}").format(
                        transaction.get("id")
                    ),
                )
                continue

        # set last sync field in `RazorPayX Integration Settings`
        frappe.db.set_value(
            RAZORPAYX_SETTING_DOCTYPE, account, "last_synced", now_datetime()
        )

        return True
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=("Failed to Sync RazorPayX Transactions for Account: {0}").format(
                account
            ),
        )


def get_razorpayx_transactions(
    account: str,
    from_date: DateTimeLikeObject,
    to_date: Optional[DateTimeLikeObject] = None,
):
    filters = {"from": from_date}

    if to_date:
        filters["to"] = to_date

    return RazorPayXTransaction(account).get_all(filters=filters)


# ? need more filters
# ? make more efficient by using ignore duplicates
def get_existing_transactions(bank_account: str):
    return frappe.get_all(
        BANK_TRANSACTION_DOCTYPE,
        fields="transaction_id",
        filters={"bank_account": bank_account},
        pluck="transaction_id",
    )


def get_mapped_razorpayx_transaction(transaction: dict, **kwargs) -> dict:
    """
    Map `RazorPayX` transaction response with `Bank Transaction` DocFiled.

    :param transaction: transaction dict of `RazorPayX`.
    :return: map dict of `Bank Transaction` DocFields.
    """

    def format_notes(notes):
        if isinstance(notes, dict):
            return "\n".join(notes.values())
        elif isinstance(notes, (list, tuple)):
            return "\n".join(notes)
        return notes

    mapped_transaction = {
        "doctype": BANK_TRANSACTION_DOCTYPE,
        "transaction_id": transaction["id"],
        "date": get_str_datetime_from_epoch(transaction["created_at"]),
        "deposit": paisa_to_rupees(transaction["credit"]),
        "withdrawal": paisa_to_rupees(transaction["debit"]),
        "closing_balance": paisa_to_rupees(transaction["balance"]),
        "currency": transaction["currency"],
        "transaction_type": transaction["source"].get("mode", ""),
        "description": format_notes(transaction["source"].get("notes", "")),
    }

    if bank_account := kwargs.get("bank_account"):
        mapped_transaction["bank_account"] = bank_account

    if reference_number := transaction["source"].get("bank_reference"):
        mapped_transaction["reference_number"] = reference_number
    else:
        if utr := transaction["source"].get("utr"):
            mapped_transaction["reference_number"] = utr

    return mapped_transaction
