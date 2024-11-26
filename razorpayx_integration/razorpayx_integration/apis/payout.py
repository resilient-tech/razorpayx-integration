from uuid import uuid4 as generate_idempotency_key

from razorpayx_integration.constants import (
    RAZORPAYX_CONTACT_TYPE,
    RAZORPAYX_FUND_ACCOUNT_TYPE,
    RAZORPAYX_PAYOUT_PURPOSE,
    RAZORPAYX_SUPPORTED_CURRENCY,
)
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.utils import (
    rupees_to_paisa,
    validate_razorpayx_payout_mode,
    validate_razorpayx_payout_status,
)


class RazorPayXPayout(BaseRazorPayXAPI):
    """
    Handle APIs for `Payout`.
    :param account_name: RazorPayX account for which this `Payout` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/payouts/
    """

    # * utility attributes
    BASE_PATH = "payouts"

    # * override base setup
    def setup(self, *args, **kwargs):
        self.account_number = self.razorpayx_account.account_number

    ### APIs ###
    def create_with_fund_account_id(self, data: dict, fund_account_id: str) -> dict:
        """
        Create a `Payout` with `Fund Account Id`.
        :param data: Request data for `Payout`.
        :param fund_account_id: The fund account's id to be paid.
        """
        payout_request = self._map_payout_request(
            data=data, fund_account_id=fund_account_id
        )
        return self._create(json=payout_request)

    def get_by_id(self, payout_id: str) -> dict:
        """
        Fetch the details of a specific `Payout` by Id.
        :param id: `Id` of fund account to fetch (Ex.`payout_jkHgLM02`).
        ---
        Reference: https://razorpay.com/docs/api/x/payouts/fetch-with-id
        """
        return self.get(endpoint=payout_id)

    def get_all(
        self, filters: dict | None = None, count: int | None = None
    ) -> list[dict]:
        """
        Get all `Payouts` associate with given `RazorPayX` account if limit is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of payouts to be retrieved.

        :raises ValueError: If `mode` or `status` is not valid (if specified).\n
        ---
        Example Usage:
        ```
        payout = RazorPayXPayout("RAZORPAYX_BANK_ACCOUNT")
        filters = {
            "contact_id":"cont_00HjGh1",
            "fund_account_id":"fa_00HjHue1",
            "mode":"NEFT",
            "reference_id":"ACC-PAY-003-2024-06-01",
            "status":"processing",
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=payout.get_all(filters)
        ```
        ---
        Note:
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/payouts/fetch-all/
        """
        if not filters:
            filters = {}

        # account number is mandatory
        filters["account_number"] = self.account_number

        return super().get_all(filters, count)

    ### BASES ###
    def _create(self, json: dict) -> dict:
        """
        Base method to create a `Payout`.
        :param json: Processed request data for `Payout`.
        """
        headers = self._get_idempotency_key_header(json)
        return self.post(json=json, headers=headers)

    ### HELPERS ###
    # todo: need proper key generation and implementation
    # ! important
    # def _get_idempotency_key_header(self, json: dict) -> dict:
    #     """
    #     Generate `Idempotency Key` header for `Payout` creation.

    #     Example:
    #     ```
    #     {
    #         "X-Payout-Idempotency": "EMP-30233-NEFT-ACC-PAY-002-2024-06-01"
    #     }
    #     ```
    #     ---
    #     Reference: https://razorpay.com/docs/api/x/payout-idempotency/make-request/
    #     """
    #     if "fund_account_id" in json:
    #         key = f"{json['fund_account_id']}_{json['reference_id']}"
    #     else:
    #         contact_id = json["fund_account"]["contact"]["reference_id"]
    #         key = f"{contact_id}_{json['mode']}_{json['reference_id']}"

    #     return {"X-Payout-Idempotency": key}

    def _get_idempotency_key_header(self, json: dict) -> dict:
        """
        Temp solution for `Idempotency Key` header for `Payout` creation.
        """
        return {"X-Payout-Idempotency": str(generate_idempotency_key())}

    def _map_payout_request(
        self,
        data: dict,
        fund_account_id: str | None = None,
        party_account_type: str | None = None,
    ) -> dict:
        """
        Map the request data to RazorPayX Payout API's required format.
        :param data: Request data for `Payout`.
        :param fund_account_id: The fund account's id to be used in `Payout`.
        :param party_account_type: The party's account type to be used in `Payout`.
        ---
        Note: Either `fund_account_id` or `party_account_type` should be provided.
        """
        payout_request = {
            "account_number": self.account_number,
            "amount": rupees_to_paisa(data["amount"]),
            "currency": RAZORPAYX_SUPPORTED_CURRENCY,
            "mode": data["mode"],
            "purpose": RAZORPAYX_PAYOUT_PURPOSE[data["party_type"].upper()].value,
            "reference_id": data["reference_id"],
            "narration": data["description"],
        }

        if note := data.get("note"):
            payout_request["note"] = {"notes_key_1": note}

        if fund_account_id:
            payout_request["fund_account_id"] = fund_account_id
        elif party_account_type:
            fund_account = self._get_mapped_fund_account_details(
                data, party_account_type
            )
            payout_request["fund_account"] = fund_account

        return payout_request

    def _get_mapped_fund_account_details(
        self, data: dict, fund_account_type: str
    ) -> dict:
        """
        Make a dictionary for `Fund Account` to be used in `Payout` creation.

        :param data: Request data for `Payout`.
        :param account_type: The type of fund account to be used in `Payout`.
        """
        fund_account = {
            "account_type": fund_account_type,
        }

        if fund_account_type == RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT:
            fund_account["bank_account"] = {
                "name": data["party_name"],
                "ifsc": data["ifsc_code"],
                "account_number": data["party_account_number"],
            }
        else:
            fund_account["vpa"] = {
                "address": data["party_vpa"],
            }

        fund_account["contact"] = {
            "name": data["party_name"],
            "email": data.get("party_email", ""),
            "contact": data.get("party_phone", ""),
            "type": RAZORPAYX_CONTACT_TYPE[data["party_type"].upper()].value,
            "reference_id": data["party"],
        }

        return fund_account

    def validate_and_process_request_filters(self, filters: dict):
        if mode := filters.get("mode"):
            validate_razorpayx_payout_mode(mode)

        if status := filters.get("status"):
            validate_razorpayx_payout_status(status)


class CompositeRazorPayXPayout(RazorPayXPayout):
    """
    Handle composite APIs for `Payout`.
    :param account_name: RazorPayX account for which this `Payout` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/payout-composite/
    """

    def create_with_bank_account(self, data: dict) -> dict:
        """
        Create a `Payout` with party's `Bank Account`.
        :param data: Request data for `Payout`.
        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/bank-account/
        """
        party_account_type = RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT

        payout_request = self._map_payout_request(
            data=data, party_account_type=party_account_type
        )

        return self._create(json=payout_request)

    def create_with_vpa(self, data: dict) -> dict:
        """
        Create a `Payout` with party's `VPA`.
        :param data: Request data for `Payout`.
        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/vpa/
        """
        party_account_type = RAZORPAYX_FUND_ACCOUNT_TYPE.VPA

        payout_request = self._map_payout_request(
            data=data, party_account_type=party_account_type
        )

        return self._create(json=payout_request)
