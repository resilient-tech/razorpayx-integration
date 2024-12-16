from uuid import uuid4 as generate_idempotency_key

from razorpayx_integration.payment_utils.utils import rupees_to_paisa
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    CONTACT_TYPE_MAP,
    PAYMENT_MODE_THRESHOLD,
    PAYOUT_PURPOSE_MAP,
    RAZORPAYX_CONTACT_TYPE,
    RAZORPAYX_FUND_ACCOUNT_TYPE,
    RAZORPAYX_PAYOUT_CURRENCY,
    RAZORPAYX_PAYOUT_MODE,
    RAZORPAYX_PAYOUT_PURPOSE,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_mode,
    validate_razorpayx_payout_status,
)

# TODO: need proper mapping
# TODO: add Data format and other format


# TODO: need refactoring
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
    def create_with_fund_account_id(self, request: dict, fund_account_id: str) -> dict:
        """
        Create a `Payout` with `Fund Account Id`.

        :param request: Request for `Payout`.
        :param fund_account_id: The fund account's id to be paid.
        """
        payout_request = self.map_payout_request(
            request=request, fund_account_id=fund_account_id
        )
        return self.make_payout(json=payout_request)

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
    def make_payout(self, json: dict) -> dict:
        """
        Base method to create a `Payout`.

        :param json: Processed request data for `Payout`.
        """
        headers = self.get_idempotency_key_header(json)

        return self.post(json=json, headers=headers)

    ### HELPERS ###
    # todo: need proper key generation and implementation
    # todo: BUGGY! if somthing fails after API calls it is not allowing to retry
    # ! important
    def get_idempotency_key_header(self, json: dict) -> dict:
        """
        Generate `Idempotency Key` header for `Payout` creation.

        Example:
        ```
        {"X-Payout-Idempotency": "ACC-PAY-002-2024-06-01"}
        ```

        ---
        Reference: https://razorpay.com/docs/api/x/payout-idempotency/make-request/
        """

        return {"X-Payout-Idempotency": json["notes"]["source_docname"]}

    def map_payout_request(
        self,
        request: dict,
        fund_account_id: str | None = None,
        fund_account_type: str | None = None,
    ) -> dict:
        """
        Map the request data to RazorPayX Payout API's required format.

        :param request: Request data for `Payout`.
        :param fund_account_id: The fund account's id to be used in `Payout`.
        :param fund_account_type: The party's account type to be used in `Payout`.

        ---
        Note: Either `fund_account_id` or `fund_account_type` should be provided. Or none of them.
        """

        payout_request = {
            "queue_if_low_balance": True,
            "account_number": self.account_number,
            "amount": rupees_to_paisa(request["amount"]),
            "currency": RAZORPAYX_PAYOUT_CURRENCY.INR.value,
            "mode": request["mode"],
            "purpose": PAYOUT_PURPOSE_MAP.get(
                request["party_type"], RAZORPAYX_PAYOUT_PURPOSE.PAYOUT.value
            ),
            "reference_id": f"{request['source_doctype']}-{request['source_docname']}",
            "narration": request["payment_description"],
            "notes": {
                "source_doctype": request["source_doctype"],
                "source_docname": request["source_docname"],
                "razorpayx_integration_account": request[
                    "razorpayx_integration_account"
                ],
            },
        }

        if fund_account_id:
            payout_request["fund_account_id"] = fund_account_id
        elif fund_account_type:
            payout_request["fund_account"] = self.get_mapped_fund_account_details(
                request, fund_account_type
            )

        return payout_request

    def get_mapped_fund_account_details(
        self, request: dict, fund_account_type: str
    ) -> dict:
        """
        Make a dictionary for `Fund Account` to be used in `Payout` creation.

        :param data: Request data for `Payout`.
        :param account_type: The type of fund account to be used in `Payout`.
        """
        fund_account = {
            "account_type": fund_account_type,
        }

        if fund_account_type == RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value:
            fund_account["bank_account"] = {
                "name": request["party_name"],
                "ifsc": request["party_bank_ifsc"],
                "account_number": request["party_bank_account_no"],
            }
        else:
            fund_account["vpa"] = {
                "address": request["party_upi_id"],
            }

        fund_account["contact"] = {
            "name": request["party_name"],
            "email": request.get("party_email", ""),
            "contact": request.get("party_mobile", ""),
            "type": CONTACT_TYPE_MAP.get(
                request["party_type"], RAZORPAYX_CONTACT_TYPE.SELF.value
            ),
            "reference_id": request["party_id"],
        }

        return fund_account

    def validate_and_process_request_filters(self, filters: dict):
        if mode := filters.get("mode"):
            validate_razorpayx_payout_mode(mode)

        if status := filters.get("status"):
            validate_razorpayx_payout_status(status)


class RazorPayXCompositePayout(RazorPayXPayout):
    """
    Handle composite APIs for `Payout`.

    :param account_name: RazorPayX account for which this `Payout` is associate.

    ---
    Reference: https://razorpay.com/docs/api/x/payout-composite/
    """

    def create_with_bank_account(
        self, request: dict, pay_instantaneously: bool = False
    ) -> dict:
        """
        Create a `Payout` with party's `Bank Account`.

        :param data: Request data for `Payout`.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/bank-account/
        """

        def get_bank_payment_mode() -> str:
            if pay_instantaneously:
                return RAZORPAYX_PAYOUT_MODE.IMPS.value
            else:
                if request["amount"] > PAYMENT_MODE_THRESHOLD.NEFT.value:
                    return RAZORPAYX_PAYOUT_MODE.RTGS.value
                else:
                    return RAZORPAYX_PAYOUT_MODE.NEFT.value

        party_account_type = RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value

        request["mode"] = get_bank_payment_mode()

        payout_request = self.map_payout_request(
            request=request, fund_account_type=party_account_type
        )

        return self.make_payout(json=payout_request)

    def create_with_vpa(self, request: dict) -> dict:
        """
        Create a `Payout` with party's `VPA`.

        :param data: Request data for `Payout`.
        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/vpa/
        """
        party_account_type = RAZORPAYX_FUND_ACCOUNT_TYPE.VPA.value

        request["mode"] = RAZORPAYX_PAYOUT_MODE.UPI.value

        payout_request = self.map_payout_request(
            request=request, fund_account_type=party_account_type
        )

        return self.make_payout(json=payout_request)


class RazorPayXLinkPayout(RazorPayXPayout):
    """
    Handle APIs for `Link Payout`.

    :param account_name: RazorPayX account for which this `Payout` is associate.

    ---
    Reference: https://razorpay.com/docs/api/x/payout-links
    """

    BASE_PATH = "payout-links"

    def create_with_contact_details(self, request: dict) -> dict:
        """
        Create a `Link Payout` with party's contact details.

        :param data: Request data for `Payout`.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/create/use-contact-details/
        """
        payout_request = self.map_payout_request(request)

        return self.make_payout(json=payout_request)

    def map_payout_request(self, request: dict) -> dict:
        return {
            "account_number": self.account_number,
            "contact": {
                "name": request["party_name"],
                "contact": request.get("party_mobile", ""),
                "email": request.get("party_email", ""),
                "type": CONTACT_TYPE_MAP.get(
                    request["party_type"], RAZORPAYX_CONTACT_TYPE.CUSTOMER.value
                ),
            },
            "amount": rupees_to_paisa(request["amount"]),
            "currency": RAZORPAYX_PAYOUT_CURRENCY.INR.value,
            "purpose": PAYOUT_PURPOSE_MAP.get(
                request["party_type"], RAZORPAYX_PAYOUT_PURPOSE.PAYOUT.value
            ),
            "description": request["payment_description"],
            "send_sms": True,
            "send_email": True,
            "notes": {
                "source_doctype": request["source_doctype"],
                "source_docname": request["source_docname"],
                "razorpayx_integration_account": request[
                    "razorpayx_integration_account"
                ],
            },
        }


# TODO: store response data??
