"""
Fetch Daily Transactions from RazorPayX and save it in ERPNext.
"""

# TODO: move to razorpayx_integration/razorpayx_integration/utils/transaction.py
from razorpayx_integration.payment_utils.utils import yesterday
from razorpayx_integration.razorpayx_integration.utils import (
    get_enabled_razorpayx_accounts,
)
from razorpayx_integration.razorpayx_integration.utils.transaction import (
    sync_razorpayx_bank_transactions,
)


def execute():
    # transaction date is yesterday, because transactions are fetch daily at 12:00 AM
    transaction_date = yesterday()

    for account in get_enabled_razorpayx_accounts():
        sync_razorpayx_bank_transactions(
            account, from_date=transaction_date, to_date=transaction_date
        )
