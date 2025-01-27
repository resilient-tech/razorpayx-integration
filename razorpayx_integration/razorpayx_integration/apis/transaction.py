from frappe.utils import DateTimeLikeObject, today

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI

# TODO: Multiple Account can more easily connect with APIs, currently for each account new object initiation require!
# TODO: Need changes as per new design.
# TODO: can use db.bulk_update ???


class RazorPayXTransaction(BaseRazorPayXAPI):
    """
    Handle APIs for `Bank Transaction` which are RazorPayX  accounts.

    :param account_name: RazorPayX account for which this `Transaction` is associate.

    ---
    Reference: https://razorpay.com/docs/api/x/transactions/
    """

    # * utility attributes
    BASE_PATH = "transactions"

    # * override base setup
    def setup(self, *args, **kwargs):
        self.account_number = self.razorpayx_setting.account_number

    ### APIs ###
    def get_by_id(
        self,
        transaction_id: str,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> dict:
        """
        Fetch the details of a specific `Transaction` by Id.

        :param id: `Id` of fund account to fetch (Ex.`txn_jkHgLM02`).
        :param source_doctype: The source doctype of the transaction.
        :param source_docname: The source docname of the transaction

        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-with-id
        """
        self._set_service_details_to_ir_log("Get Transaction By Id")
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        return self.get(endpoint=transaction_id)

    def get_all(
        self,
        *,
        from_date: DateTimeLikeObject | None = None,
        to_date: DateTimeLikeObject | None = None,
        count: int | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> list[dict] | None:
        """
        Get all `Transaction` associate with given `RazorPayX` account if count is not given.

        :param filters: Result will be filtered as given filters.
        :param from_date: The starting date for which transactions are to be fetched.
        :param to_date: The ending date for which transactions are to be fetched.
        :param count: The number of `Transaction` to be retrieved.
        :param source_doctype: The source doctype of the transaction.
        :param source_docname: The source docname of the transaction

        ---
        Example Usage:

        ```
        fund_account = RazorPayXFundAccount(RAZORPAYX_BANK_ACCOUNT)

        # Example 1:
        filters = {
            "from":"2024-01-01"
            "to":"2024-06-01"
        }

        response=fund_account.get_all(filters)

        # Example 2:
        response=fund_account.get_all(from_date="2024-01-01",to_date="2024-06-01",count=10)
        ```

        ---
        Note:
        - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).

        ---
        Reference: https://razorpay.com/docs/api/x/transactions/fetch-all
        """
        filters = {}

        if from_date:
            filters["from"] = from_date

        if to_date:
            filters["to"] = to_date

        if "from" not in filters:
            filters["from"] = self.razorpayx_setting.last_sync_on

        # account number is mandatory
        filters["account_number"] = self.account_number

        if not self.ir_service_set:
            self._set_service_details_to_ir_log("Get All Transactions", False)

        if not (self.source_doctype and self.source_docname):
            self.source_doctype = source_doctype
            self.source_docname = source_docname

        return super().get_all(filters=filters, count=count)

    def get_transactions_for_today(
        self,
        count: int | None = None,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> list[dict] | None:
        """
        Get all transactions for today associate with given `RazorPayX` account.

        :param count: The number of transactions to be retrieved.
        :param source_doctype: The source doctype of the transaction.
        :param source_docname: The source docname of the transaction

        ---
        Note: If count is not given, it will return all transactions for today.
        """
        today_date = today()
        self._set_service_details_to_ir_log("Get Transactions For Today")

        return self.get_all(
            from_date=today_date,
            to_date=today_date,
            count=count,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )

    def get_transactions_for_date(
        self,
        date: DateTimeLikeObject,
        count: int | None = None,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> list[dict] | None:
        """
        Get all transactions for specific date associate with given `RazorPayX` account.

        :param date: A date string in "YYYY-MM-DD" format or a (datetime,date) object.
        """
        self._set_service_details_to_ir_log("Get Transactions For Date")

        return self.get_all(
            from_date=date,
            to_date=date,
            count=count,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )
