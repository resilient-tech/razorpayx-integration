from typing import Optional, Union

from razorpayx_integration.constant import RAZORPAYX_FUND_ACCOUNT_TYPE
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.utils import validate_razorpayx_fund_account_type

# todo : use composite API, If composite APIs working properly fine then no need of this API
# todo: this need to be refactor and optimize


class RazorPayXFundAccount(BaseRazorPayXAPI):
    """
    Handle APIs for RazorPayX Fund Account.
    :param account_name: RazorPayX account for which this `Fund Account` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/fund-accounts/
    """

    # * utility attributes
    BASE_PATH = "fund_accounts"

    # * override base setup
    def setup(self, *args, **kwargs):
        pass

    ### APIs ###
    def create_with_bank_account(
        self, contact_id: str, contact_name: str, ifsc_code: str, account_number: str
    ):
        """
        Create RazorPayX `Fund Account` with contact's bank account details.

        :param contact_id: The ID of the contact to which the `fund_account` is linked (Eg. `cont_00HjGh1`).
        :param contact_name: The account holder's name.
        :param ifsc_code: Unique identifier of a bank branch (Eg. `HDFC0000053`).
        :param account_number: The account number (Eg. `765432123456789`).
        ---
        Reference: https://razorpay.com/docs/api/x/fund-accounts/create/bank-account
        """
        json = {
            "contact_id": contact_id,
            "account_type": RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT,
            "bank_account": {
                "name": contact_name,
                "ifsc": ifsc_code,
                "account_number": account_number,
            },
        }
        return self.post(json=json)

    def create_with_vpa(self, contact_id: str, vpa: str):
        """
        Create RazorPayX `Fund Account` with contact's Virtual Payment Address.

        :param str contact_id: The ID of the contact to which the `fund_account` is linked (Eg. `cont_00HjGh1`).
        :param str vpa: The contact's virtual payment address (VPA) (Eg. `joedoe@exampleupi`)
        ---
        Reference: https://razorpay.com/docs/api/x/fund-accounts/create/vpa
        """
        json = {
            "contact_id": contact_id,
            "account_type": RAZORPAYX_FUND_ACCOUNT_TYPE.VPA,
            "vpa": {"address": vpa},
        }
        return self.post(json=json)

    def get_by_id(self, id: str):
        """
        Fetch the details of a specific `Fund Account` by Id.
        :param id: `Id` of fund account to fetch (Ex.`fa_00HjHue1`).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-with-id
        """
        return self.get(endpoint=id)

    def get_all(
        self, filters: Optional[dict] = None, count: Optional[int] = None
    ) -> list[dict]:
        """
        Get all `Fund Account` associate with given `RazorPayX` account if limit is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of `Fund Account` to be retrieved.
        ---
        Example Usage:
        ```
        fund_account = RazorPayXFundAccount("RAZORPAYX_BANK_ACCOUNT")
        filters = {
            "contact_id":"cont_hkj012yuGJ",
            "account_type":"bank_account",
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=fund_account.get_all(filters)
        ```
        ---
        Note:
            - Not all filters are require.
            - `account_type` can be one of the ['bank_account','vpa'], if not raises an error.
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/fund-accounts/fetch-all
        """
        return super().get_all(filters, count)

    def activate(self, id: str) -> dict:
        """
        Activate the `Fund Account` for the given Id if it is deactivated.

        :param id: Id of the `Fund Account` to make activate (Ex.`fa_00HjHue1`).
        """
        return self._change_state(id=id, active=True)

    def deactivate(self, id: str) -> dict:
        """
        Deactivate the `Fund Account` for the given Id if it is activated.

        :param id: Id of the `Fund Account` to make deactivate (Ex.`fa_00HjHue1`).
        """
        return self._change_state(id=id, active=False)

    ### Bases ###
    def _change_state(self, id: str, active: Union[bool, int]) -> dict:
        """
        Change the state of the `Fund Account` for the given Id.

        :param id: Id of `Fund Account` to change state (Ex.`fa_00HjHue1`).
        :param active: Represent state. (`True`:Active,`False`:Inactive)
        ---
        Reference: https://razorpay.com/docs/api/x/fund-accounts/activate-or-deactivate
        """
        return self.patch(endpoint=id, json={"active": active})

    ### Helpers ###
    def validate_and_process_request_filters(self, filters: dict) -> dict:
        if account_type := filters.get("account_type"):
            validate_razorpayx_fund_account_type(account_type)
