from typing import Optional

from frappe.utils.data import DateTimeLikeObject, today

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.utils import get_end_of_day_epoch, get_start_of_day_epoch

# todo: Multiple Account can more easily connect with APIs, currently for each account new object initiation require!


class RazorPayXTransaction(BaseRazorPayXAPI):
    """
    Handle APIs for `Transaction` which are RazorPayX  accounts.
    :param str account_name: RazorPayX account for which this `Transaction` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/transactions/
    """

    # * utility attributes
    BASE_PATH = "transactions"

    # * override base setup
    def setup(self):
        self.account_number = self.razorpayx_account.account_number

    ### APIs ###
    def get_by_id(self, transaction_id: str) -> dict:
        """
        Fetch the details of a specific `Transaction` by Id.
        :param str id: `Id` of fund account to fetch (Ex.`txn_jkHgLM02`).
        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-with-id
        """
        return self.get(endpoint=transaction_id)

    # todo: filters default should be None
    def get_all(self, filters: dict = {}, count: Optional[int] = None) -> list[dict]:
        """
        Get all `Transaction` associate with given `RazorPayX` account if limit is not given.

        :param dict filters: Result will be filtered as given filters.
        :param int count: The number of `Transaction` to be retrieved.
        ---
        Example Usage:
        ```
        fund_account = RazorPayXFundAccount("RAZORPAYX_BANK_ACCOUNT")
        filters = {
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=fund_account.get_all(filters)
        ```
        ---
        Note:
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-all
        """
        if filters:
            filters = self._process_filters(filters)

        # account number is mandatory
        filters["account_number"] = self.account_number

        if count and count <= 100:
            filters["count"] = count
            return self._fetch(filters)

        skip = 0
        transactions = []
        filters["count"] = 100  # max limit is 100
        filters["skip"] = 0

        while True:
            items = self._fetch(filters)

            if items:
                transactions.extend(items)
            elif not items or len(items) < 100:
                break

            if isinstance(count, int):
                count -= len(items)
                if count <= 0:
                    break

            skip += 100
            filters["skip"] = skip

        return transactions

    def get_transactions_for_today(self, count: Optional[int] = None):
        """
        Get all transactions for today associate with given `RazorPayX` account.
        """
        filters = {"from": today(), "to": today()}
        return self.get_all(filters=filters, count=count)

    def get_transactions_for_date(
        self, date: DateTimeLikeObject, count: Optional[int] = None
    ):
        """
        Get all transactions for specific date associate with given `RazorPayX` account.
        :param date: A date string in "YYYY-MM-DD" format or a (datetime,date) object.
        """
        filters = {"from": date, "to": date}
        return self.get_all(filters=filters, count=count)

    ### Bases ###
    def _fetch(self, params: dict):
        """
        Fetch `Transactions` associate with given `RazorPayX` account.
        """
        response = self.get(params=params)
        return response.get("items", [])

    ### Helpers ###
    def _process_filters(self, filters: dict) -> dict:
        if from_date := filters.get("from"):
            filters["from"] = get_start_of_day_epoch(from_date)

        if to_date := filters.get("to"):
            filters["to"] = get_end_of_day_epoch(to_date)

        return filters
