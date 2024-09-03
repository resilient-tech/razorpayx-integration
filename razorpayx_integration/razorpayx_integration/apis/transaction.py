from typing import Optional

from frappe.utils import DateTimeLikeObject, today

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI

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
    def setup(self, *args, **kwargs):
        # todo: changes it is now Customer Identifier ...
        self.account_number = self.razorpayx_account.account_number

    ### APIs ###
    def get_by_id(self, transaction_id: str) -> dict:
        """
        Fetch the details of a specific `Transaction` by Id.
        :param id: `Id` of fund account to fetch (Ex.`txn_jkHgLM02`).
        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-with-id
        """
        return self.get(endpoint=transaction_id)

    def get_all(
        self,
        filters: Optional[dict] = None,
        from_date: Optional[DateTimeLikeObject] = None,
        to_date: Optional[DateTimeLikeObject] = None,
        count: Optional[int] = None,
    ) -> list[dict]:
        """
        Get all `Transaction` associate with given `RazorPayX` account if count is not given.

        :param filters: Result will be filtered as given filters.
        :param from_date: The starting date for which transactions are to be fetched.
        :param to_date: The ending date for which transactions are to be fetched.
        :param count: The number of `Transaction` to be retrieved.
        ---
        Example Usage:
        ```
        fund_account = RazorPayXFundAccount("RAZORPAYX_BANK_ACCOUNT")
        filters = {
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=fund_account.get_all(filters)
        ---
        response=fund_account.get_all(from_date="2024-01-01",to_date="2024-06-01",count=10)
        ```
        ---
        Note:
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-all
        """
        if not filters:
            filters = {}

            if from_date:
                filters["from"] = from_date

            if to_date:
                filters["to"] = to_date

        # account number is mandatory
        filters["account_number"] = self.account_number

        return super().get_all(filters, count)

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
