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


class RazorPayXPayout(BaseRazorPayXAPI):
    """
    Handle APIs for `Payout`.

    :param account_name: RazorPayX Integration account from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is to be made for a specific `Fund Account`.
    - Payout will be `queued` if the balance is low.

    ---
    Reference: https://razorpay.com/docs/api/x/payouts/
    """

    # * utility attributes
    BASE_PATH = "payouts"

    # * override base setup
    def setup(self, *args, **kwargs):
        self.razorpayx_account_number = self.razorpayx_account.account_number
        self.default_payout_request = {
            "account_number": self.razorpayx_account_number,
            "queue_if_low_balance": True,
            "currency": RAZORPAYX_PAYOUT_CURRENCY.INR.value,
        }
        self.payout_headers = {}

    ### APIs ###
    def pay_to_bank_account(self, payout_details: dict) -> dict:
        """
        Pay to a `Bank Account` using `Fund Account ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Note:
        - Fund account must associate with the bank account.
            - Refer : https://razorpay.com/docs/api/x/fund-accounts/create/bank-account

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `fund_account_id` :str: The fund account id to be used for the payout (Ex. `fa_00000000000001`).
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).

        Optional:
        - `pay_instantaneously` :bool: Pay instantaneously if `True`. (Default: `False`)
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/create/bank-account
        """
        payout_details["mode"] = self.get_bank_payment_mode(payout_details)

        return self._make_payout(payout_details)

    def pay_to_upi_id(self, payout_details: dict) -> dict:
        """
        Pay to a `UPI ID` using `Fund Account ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Note:
        - Fund account must associate with the UPI ID.
         - Refer : https://razorpay.com/docs/api/x/fund-accounts/create/vpa

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `fund_account_id` :str: The fund account id to be used for the payout (Ex. `fa_00000000000001`).
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).

        Optional:
        - `description` :str: Description of the payout.
            - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/create/vpa
        """
        payout_details["mode"] = RAZORPAYX_PAYOUT_MODE.UPI.value

        return self._make_payout(payout_details)

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

        :raises ValueError: If `mode` or `status` is not valid (if specified).

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
        filters["account_number"] = self.razorpayx_account_number

        return super().get_all(filters, count)

    def cancel(self, payout_id: str) -> dict:
        """
        Cancel a specific `Payout` by Id.

        Caution: ⚠️  Only `queued` payouts can be canceled.

        :param id: Payout ID to be canceled (Ex.`payout_jkHgLM02`).

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/cancel
        """
        return self.post(endpoint=f"{payout_id}/cancel")

    ### BASES ###
    def _make_payout(self, payout_details: dict) -> dict:
        """
        Base method to create a `Payout`.

        Caution: ⚠️  This method should not be called directly.

        :param payout_details: Request body for `Payout`.
        """
        json = self.get_mapped_payout_request_body(payout_details)

        self.set_idempotency_key_header(json)
        # TODO: validation so can reduce the number of API calls

        return self.post(json=json, headers=self.payout_headers)

    ### HELPERS ###
    # TODO: should respect user input ?
    def get_bank_payment_mode(payout_details: dict) -> str:
        """
        Return the payment mode for the payout.

        :param payout_details: Request body for `Payout`.

        Returns: NEFT | RTGS | IMPS
        """

        if payout_details.get("pay_instantaneously"):
            return RAZORPAYX_PAYOUT_MODE.IMPS.value
        else:
            if payout_details["amount"] > PAYMENT_MODE_THRESHOLD.NEFT.value:
                return RAZORPAYX_PAYOUT_MODE.RTGS.value
            else:
                return RAZORPAYX_PAYOUT_MODE.NEFT.value

    # TODO: need proper key generation and implementation
    # TODO: BUGGY! if somthing fails after API calls it is not allowing to retry
    # ! important
    def set_idempotency_key_header(self, json: dict):
        """
        Generate `Idempotency Key` header for `Payout` creation.

        :param json: Mapped request data for `Payout`.

        ---
        Example:
        ```
        {"X-Payout-Idempotency": "ACC-PAY-002-2024-06-01"}
        ```
        ---
        Reference: https://razorpay.com/docs/api/x/payout-idempotency/make-request/
        """

        self.default_headers["X-Payout-Idempotency"] = json["notes"]["source_docname"]

    def get_mapped_payout_request_body(self, payout_details: dict) -> dict:
        """
        Mapping the request data to RazorPayX `Payout` API's required format.

        :param payout_details: Request data for `Payout`.

        ---
        Note: 🟢 Override this method to customize the request data.

        ---
        Mapped Sample:
        ```py
        {
            "account_number": 255185620,
            "amount": 5000,  # in paisa
            "currency": "INR",  # Fixed
            "fund_account_id": "fa_00000000000001",
            "mode": "NEFT",
            "queue_if_low_balance": True,  # Fixed
            "purpose": "payout",
            "reference_id": "ACC-PAY-002-2024-06-01",
            "narration": "Payout for customer",
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
            },
        }
        ```
        """

        mapped_request = self.get_base_mapped_payout_info(payout_details)

        mapped_request["fund_account_id"] = payout_details["fund_account_id"]

        return mapped_request

    def get_base_mapped_payout_info(self, payout_details: dict) -> dict:
        """
        Return the base mapped payout information.

        Consists of:
        - Mandatory values
        - Default values
        - Dependent values

        :param payout_details: Request body for `Payout`.

        ---
        Base Mapped Sample:
        ```py
        {
            "account_number": 255185620,
            "amount": 5000,  # in paisa
            "currency": "INR",  # Fixed
            "mode": "NEFT",
            "queue_if_low_balance": True,  # Fixed
            "purpose": "payout",
            "reference_id": "ACC-PAY-002-2024-06-01",
            "narration": "Payout for customer",
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
            },
        }
        ```
        """

        def get_purpose() -> str:
            if purpose := payout_details.get("purpose"):
                return purpose

            return PAYOUT_PURPOSE_MAP.get(
                payout_details["party_type"], RAZORPAYX_PAYOUT_PURPOSE.PAYOUT.value
            )

        def get_reference_id() -> str:
            if reference_id := payout_details.get("reference_id"):
                return reference_id

            return (
                f"{payout_details['source_doctype']}-{payout_details['source_docname']}"
            )

        def get_notes() -> dict:
            return {
                "source_doctype": payout_details["source_doctype"],
                "source_docname": payout_details["source_docname"],
                **payout_details.get("notes", {}),
            }

        return {
            **self.default_payout_request,
            "amount": rupees_to_paisa(payout_details["amount"]),
            "mode": payout_details["mode"],
            "purpose": get_purpose(),
            "reference_id": get_reference_id(),
            "narration": payout_details.get("description", ""),
            "notes": get_notes(),
        }

    def get_party_fund_account_details(self, payout_details: dict) -> dict:
        """
        Make a dictionary for `Fund Account` to be used in `Payout`.

        :param data: Request body for `Payout`.

        ---
        Note:  ⚠️  `party_account_type` must be provided in the `payout_details`.

        ---
        Fund Account Sample:

        ```py
        # Bank Account
        {
            "account_type": "bank_account",
            "bank_account": {
                "name": "Gaurav Kumar",
                "ifsc": "HDFC0000053",
                "account_number": "7654321234567890",
            },
            "contact": {
                "name": "Gaurav Kumar",
                "email": "gauravemail@gmail.com",
                "contact": "9123456789",
                "type": "customer",
                "reference_id": "cont_00HjGh1",
            },
        }

        # VPA
        {
            "account_type": "vpa",
            "vpa": {
                "address": "gauravkumar@upi",
            },
            "contact": {
                "name": "Gaurav Kumar",
                "email": "gauravemail@gmail.com",
                "contact": "9123456789",
                "type": "customer",
                "reference_id": "cont_00HjGh1",
            },
        }
        ```
        """

        def get_account_details(account_type: str) -> dict:
            match account_type:
                case RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value:
                    return {
                        "bank_account": {
                            "name": payout_details["party_name"],
                            "ifsc": payout_details["party_bank_ifsc"],
                            "account_number": payout_details["party_bank_account_no"],
                        }
                    }
                case RAZORPAYX_FUND_ACCOUNT_TYPE.VPA.value:
                    return {
                        "vpa": {
                            "address": payout_details["party_upi_id"],
                        }
                    }

        return {
            "account_type": payout_details["party_account_type"],
            **get_account_details(payout_details["party_account_type"]),
            "contact": self.get_party_contact_details(payout_details),
        }

    def get_party_contact_details(self, payout_details: dict) -> dict:
        """
        Make a dictionary for `Contact` to be used in `Payout`.

        :param data: Request body for `Payout`.

        ---
        Contact Sample:
        ```
        # If `razorpayx_contact_id` is not provided
        {
            "name": "Gaurav Kumar",
            "email": "gauravemail@gmail.com",
            "contact": "9123456789",
            "type": "customer",
            "reference_id": "cont_00HjGh1",
        }

        # If `razorpayx_contact_id` is provided
        {"id": "cont_00HjGh1"}
        ```
        """

        def get_type() -> str:
            return CONTACT_TYPE_MAP.get(
                payout_details["party_type"], RAZORPAYX_CONTACT_TYPE.SELF.value
            )

        if contact_id := payout_details.get("razorpayx_contact_id"):
            return {"id": contact_id}

        return {
            "name": payout_details["party_name"],
            "email": payout_details.get("party_email", ""),
            "contact": payout_details.get("party_mobile", ""),
            "type": get_type(),
            "reference_id": payout_details.get("party_id", ""),
        }

    ### VALIDATIONS ###
    def validate_and_process_request_filters(self, filters: dict):
        if mode := filters.get("mode"):
            validate_razorpayx_payout_mode(mode)

        if status := filters.get("status"):
            validate_razorpayx_payout_status(status)

        # TODO: validate purpose also ...


class RazorPayXCompositePayout(RazorPayXPayout):
    """
    Handle APIs for `Composite Payout`.

    :param account_name: RazorPayX Integration account from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is made directly to party's `Bank Account` or `VPA`.
    - Payout will be `queued` if the balance is low.

    ---
    Reference: https://razorpay.com/docs/api/x/payout-composite/
    """

    ### APIs ###
    def pay_to_bank_account(self, payout_details: dict) -> dict:
        """
        Make a `Payout` to a party's `Bank Account`.

        :param payout_details: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_name` :str: Name of the party to be paid.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `party_bank_account_no` :str: Bank account number of the party.
        - `party_bank_ifsc` :str: IFSC code of the party's bank.

        Optional:
        - `party_id` :str: Id of the party (Ex. Docname of the party).
        - `party_mobile` :str: Mobile number of the party.
        - `party_email` :str: Email of the party.
        - `pay_instantaneously` :bool: Pay instantaneously if `True`. (Default: `False`)
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/bank-account/
        """
        payout_details["mode"] = self.get_bank_payment_mode(payout_details)
        payout_details[
            "party_account_type"
        ] = RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value

        return self._make_payout(payout_details)

    def pay_to_upi_id(self, payout_details: dict) -> dict:
        """
        Make a `Payout` to a party's `UPI ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_name` :str: Name of the party to be paid.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `party_upi_id` :str: UPI ID of the party (Ex. `gauravkumar@exampleupi`).

        Optional:
        - `party_id` :str: Id of the party (Ex. Docname of the party).
        - `party_mobile` :str: Mobile number of the party.
        - `party_email` :str: Email of the party.
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-composite/create/vpa/
        """
        payout_details["mode"] = RAZORPAYX_PAYOUT_MODE.UPI.value
        payout_details["party_account_type"] = RAZORPAYX_FUND_ACCOUNT_TYPE.VPA.value

        return self._make_payout(payout_details)

    ### HELPERS ###
    def get_mapped_payout_request_body(self, payout_details) -> dict:
        """
        Mapping the request data to RazorPayX `Composite Payout` API's required format.

        :param payout_details: Request body for `Payout`.

        ---
        Note: 🟢 Override this method to customize the request data.

        ---
        Mapped Sample:

        ```py
        {
            "account_number": 255185620,
            "amount": 5000,
            "currency": "INR",
            "mode": "NEFT",
            "queue_if_low_balance": True,
            "purpose": "payout",
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": "Gaurav Kumar",
                    "ifsc": "HDFC0000053",
                    "account_number": "7654321234567890",
                },
                "contact": {
                    "name": "Gaurav Kumar",
                    "email": "gauravemail@gmail.com",
                    "contact": "9123456789",
                    "type": "customer",
                    "reference_id": "cont_00HjGh1",
                },
            },
            "reference_id": "ACC-PAY-002-2024-06-01",
            "narration": "Payout for customer",
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
            },
        }
        ```
        """
        mapped_request = self.get_base_mapped_payout_info(payout_details)

        mapped_request["fund_account"] = self.get_party_fund_account_details(
            payout_details
        )

        return mapped_request


class RazorPayXLinkPayout(RazorPayXPayout):
    """
    Handle APIs for `Link Payout`.

    :param account_name: RazorPayX Integration account from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is made with link (Link will be sent to party's contact details).

    ---
    Reference: https://razorpay.com/docs/api/x/payout-links
    """

    BASE_PATH = "payout-links"

    ### APIs ###
    def create_with_contact_details(self, payout_details: dict) -> dict:
        """
        Create a `Link Payout` with party's contact details.

        :param data: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_name` :str: Name of the party to be paid.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `party_mobile` :str: Mobile number of the party.
        - `party_email` :str: Email of the party.

        Optional:
        - `receipt` :str: Receipt details for the payout.
        - `send_sms` :bool: Send SMS to the party if `True`. (Default: `True`)
        - `send_email` :bool: Send Email to the party if `True`. (Default: `True`)
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.
        - `expire_by` :datetime: Expiry date-time of the link.
            - This parameter can be used only if you have enabled the expiry feature for Payout Links.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/create/use-contact-details/
        """
        return self._make_payout(payout_details)

    def create_with_razorpayx_contact_id(self, payout_details: dict) -> dict:
        """
        Create a `Link Payout` with party's `RazorPayX Contact ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `razorpayx_contact_id` :str: The RazorPayX Contact ID of the party (Ex. `cont_00HjGh1`).

        Optional:
        - `receipt` :str: Receipt details for the payout.
        - `send_sms` :bool: Send SMS to the party if `True`. (Default: `True`)
        - `send_email` :bool: Send Email to the party if `True`. (Default: `True`)
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.
        - `expire_by` :datetime: Expiry date-time of the link.
            - This parameter can be used only if you have enabled the expiry feature for Payout Links.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/create/use-contact-id
        """
        return self._make_payout(payout_details)

    ### HELPERS ###
    def get_mapped_payout_request_body(self, payout_details: dict) -> dict:
        """

        Mapping the request data to RazorPayX `Link Payout` API's required format.

        :param payout_details: Request body for `Payout`.

        ---
        Note: 🟢 Override this method to customize the request data.

        ---
        Mapped Sample:

        ```py
        {
            "account_number": 255185620,
            "contact": {
                "name": "Gaurav Kumar",
                "email": "gauravemail@gmail.com",
                "contact": "9123456789",
                "type": "customer",
            },
            "amount": 5000,
            "currency": "INR",
            "purpose": "payout",
            "description": "Payout for customer",
            "receipt": "Receipt No. 1",
            "send_sms": true,
            "send_email": true,
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
            },
            "expire_by": 1545384058,
        }
        ```

        """
        params_to_delete = ("narration", "queue_if_low_balance", "reference_id", "mode")

        mapped_request = self.get_base_mapped_payout_info(payout_details)

        mapped_request["description"] = mapped_request["narration"]
        mapped_request["contact"] = self.get_party_contact_details(payout_details)

        if expire_by := payout_details.get("expire_by"):
            mapped_request["expire_by"] = expire_by.timestamp()

        for param in params_to_delete:
            del mapped_request[param]

        return mapped_request

    # TODO: others APIs


# TODO: store response data??
