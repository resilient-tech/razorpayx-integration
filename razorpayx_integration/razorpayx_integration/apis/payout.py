import frappe
from frappe import _
from payment_integration_utils.payment_integration_utils.constants.payments import (
    TRANSFER_METHOD as PAYOUT_MODE,
)
from payment_integration_utils.payment_integration_utils.utils import (
    rupees_to_paisa,
    to_hyphenated,
)
from payment_integration_utils.payment_integration_utils.utils.validation import (
    validate_payment_mode as validate_payout_mode,
)

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorpayXAPI
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    CONTACT_TYPE,
    CONTACT_TYPE_MAP,
    FUND_ACCOUNT_TYPE,
    PAYOUT_CURRENCY,
    PAYOUT_PURPOSE,
    PAYOUT_PURPOSE_MAP,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_description,
)


class RazorpayXPayout(BaseRazorpayXAPI):
    """
    Handle APIs for `Payout`.

    :param razorpayx_setting_name: RazorpayX Integration Setting from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is to be made for a specific `Fund Account`.
    - Payout will be `queued` if the balance is low.

    ---
    Reference: https://razorpay.com/docs/api/x/payouts/
    """

    ### CLASS VARIABLES ###
    BASE_PATH = "payouts"

    ### SETUPS ###
    def setup(self, *args, **kwargs):
        """
        Override this method to setup `API` specific configurations.

        Caution: ⚠️ Don't forget to call `super().setup()` in sub class.
        """
        super().setup(*args, **kwargs)

        self.razorpayx_account_number = self.razorpayx_setting.account_number
        self.default_payout_request = {
            "account_number": self.razorpayx_account_number,
            "queue_if_low_balance": True,
            "currency": PAYOUT_CURRENCY.INR.value,
        }
        self.payout_headers = {}

    ### APIs ###
    def pay(self, payout_details: dict) -> dict:
        """
        Pay to a `Bank Account` or `UPI` using contact's `Fund Account ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Note:
        - Fund account must associate with the bank account to pay to bank account.
            - Refer : https://razorpay.com/docs/api/x/fund-accounts/create/bank-account
        - Fund account must associate with the UPI ID.
            - Refer : https://razorpay.com/docs/api/x/fund-accounts/create/vpa

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `mode` :str: Payment mode for the payout (Options: `NEFT`, `RTGS`, `IMPS`, `UPI`).
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
        References:
        - https://razorpay.com/docs/api/x/payouts/create/bank-account
        - https://razorpay.com/docs/api/x/payouts/create/vpa

        """
        mode = payout_details["mode"]
        self._validate_payout_mode(mode)

        service = (
            "Make Payout to UPI ID via Fund Account"
            if mode == PAYOUT_MODE.UPI.value
            else "Make Payout to Bank Account via Fund Account"
        )

        self._set_service_details_to_ir_log(service)
        return self._make_payout(payout_details)

    def get_by_id(
        self,
        payout_id: str,
        *,
        data: str | None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> dict:
        """
        Fetch the details of a specific `Payout` by Id.

        :param id: `Id` of fund account to fetch (Ex.`payout_jkHgLM02`).
        :param data: Specific data to be fetched (Ex. `status`, `utr`, etc.).
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        ---
        Note:
        - If data is not provided, the complete payout details will be fetched.
        - If data is not available, `None` will be returned.

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/fetch-with-id
        """
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        if not self.ir_service_set:
            self._set_service_details_to_ir_log("Get Payout by ID")

        response = self.get(endpoint=payout_id)

        if not data:
            return response

        return response.get(data)

    def cancel(
        self,
        payout_id: str,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> dict:
        """
        Cancel a specific `Payout` or `Payout Link` by Id.

        Caution: ⚠️  Only `queued` payouts can be canceled.

        :param payout_id: Payout ID to be canceled (Ex.`payout_jkHgLM02`).
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/cancel
        """
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        if not self.ir_service_set:
            self._set_service_details_to_ir_log("Cancel Payout")

        return self.post(endpoint=f"{payout_id}/cancel")

    ### BASES ###
    def _make_payout(self, payout_details: dict) -> dict:
        """
        Base method to create a `Payout`.

        Caution: ⚠️  This method should not be called directly.

        :param payout_details: Request body for `Payout`.
        """
        json = self._get_mapped_payout_request_body(payout_details)

        # to ease the validation
        self.source_doctype = json["notes"]["source_doctype"]
        self.source_docname = json["notes"]["source_docname"]

        self._set_idempotency_key_header(json)

        # validations
        self._validate_description(json)

        if not self.ir_service_set:
            self._set_service_details_to_ir_log("Make Payout")

        return self.post(json=json, headers=self.payout_headers)

    ### HELPERS ###
    def _set_idempotency_key_header(self, json: dict):
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
        self.payout_headers["X-Payout-Idempotency"] = to_hyphenated(self.source_docname)

    def _get_mapped_payout_request_body(self, payout_details: dict) -> dict:
        """
        Mapping the request data to RazorpayX `Payout` API's required format.

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
                "description": "Payout for customer",
            },
        }
        ```
        """

        mapped_request = self._get_base_mapped_payout_info(payout_details)

        mapped_request["fund_account_id"] = payout_details["fund_account_id"]

        return mapped_request

    def _get_base_mapped_payout_info(self, payout_details: dict) -> dict:
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
                "description": "Payout for customer",
            },
        }
        ```
        """

        def get_purpose() -> str:
            if purpose := payout_details.get("purpose"):
                return purpose

            return PAYOUT_PURPOSE_MAP.get(
                payout_details["party_type"], PAYOUT_PURPOSE.PAYOUT.value
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
                "description": payout_details.get("description", ""),
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

    def _get_party_contact_details(self, payout_details: dict) -> dict:
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
            "reference_id": "Customer: Gaurav",
        }

        # If `razorpayx_contact_id` is provided
        {"id": "cont_00HjGh1"}
        ```
        """
        if contact_id := payout_details.get("razorpayx_contact_id"):
            return {"id": contact_id}

        return {
            "name": self.sanitize_party_name(payout_details["party_name"]),
            "email": payout_details.get("party_email", ""),
            "contact": payout_details.get("party_mobile", ""),
            "reference_id": f"{payout_details['party_type']}: {payout_details.get('party_id', '')}",
            "type": CONTACT_TYPE_MAP.get(
                payout_details["party_type"], CONTACT_TYPE.SELF.value
            ),
        }

    ### VALIDATIONS ###
    def _validate_description(self, json: dict):
        """
        Validate the `narration` of the payout.

        :param json: Payload for `Payout`.

        ---
        Note: 🟢 Override this method to customize the validation.
        """
        if narration := json.get("narration"):
            validate_razorpayx_payout_description(narration)

    def _validate_payout_mode(self, mode: str):
        validate_payout_mode(mode, throw=True)

        if mode == PAYOUT_MODE.LINK.value:
            frappe.throw(
                msg=_("Link Payout is not supported"),
                title=_("Invalid Payout Mode"),
            )


class RazorpayXCompositePayout(RazorpayXPayout):
    """
    Handle APIs for `Composite Payout`.

    :param account_name: RazorpayX Integration account from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is made directly to party's `Bank Account` or `VPA`.
    - Payout will be `queued` if the balance is low.

    ---
    Reference: https://razorpay.com/docs/api/x/payout-composite/
    """

    ### APIs ###
    def pay(self, payout_details: dict) -> dict:
        """
        Make a `Payout` to a party's `Bank Account` or `UPI ID`.

        :param payout_details: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `mode` :str: Payment mode for the payout (Options: `NEFT`, `RTGS`, `IMPS`, `UPI`).
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_name` :str: Name of the party to be paid.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `party_payment_details` :dict: Payment details of the party.
            - If `mode` is `NEFT`, `RTGS`, `IMPS`:
                - `bank_account_no` :str: Bank account number of the party.
                - `bank_ifsc` :str: IFSC code of the party's bank.
            - If `mode` is `UPI`:
                - `upi_id` :str: UPI ID of the party (Ex. `gauravkumar@exampleupi`).
        Optional:
        - `party_id` :str: Id of the party (Ex. Docname of the party).
        - `party_contact_details` :dict: Contact details of the party.
            - `party_mobile` :str: Mobile number of the party.
            - `party_email` :str: Email of the party.
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.

        ---
        References:
        - https://razorpay.com/docs/api/x/payout-composite/create/bank-account/
        - https://razorpay.com/docs/api/x/payout-composite/create/vpa/


        """
        mode = payout_details["mode"]
        self._validate_payout_mode(mode)

        payment_details = payout_details["party_payment_details"]
        payout_details.update(**payout_details.pop("party_contact_details"))

        if mode == PAYOUT_MODE.UPI.value:
            service = "Make Composite Payout to UPI ID"

            payout_details["party_account_type"] = FUND_ACCOUNT_TYPE.VPA.value
            payout_details["party_upi_id"] = payment_details["upi_id"]
        else:
            service = "Make Composite Payout to Bank Account"

            payout_details["party_account_type"] = FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value
            payout_details["party_bank_account_no"] = payment_details["bank_account_no"]
            payout_details["party_bank_ifsc"] = payment_details["bank_ifsc"]

        self._set_service_details_to_ir_log(service)
        return self._make_payout(payout_details)

    ### HELPERS ###
    def _get_mapped_payout_request_body(self, payout_details) -> dict:
        """
        Mapping the request data to RazorpayX `Composite Payout` API's required format.

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
                    "reference_id": "Customer: Gaurav",
                },
            },
            "reference_id": "ACC-PAY-002-2024-06-01",
            "narration": "Payout for customer",
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
                "description": "Payout for customer",
            },
        }
        ```
        """
        mapped_request = self._get_base_mapped_payout_info(payout_details)

        mapped_request["fund_account"] = self._get_party_fund_account_details(
            payout_details
        )

        return mapped_request

    def _get_party_fund_account_details(self, payout_details: dict) -> dict:
        """
        Get a dictionary for `Fund Account` to be used in `Payout`.

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
                "reference_id": "Customer: Gaurav",
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
                "reference_id": "Customer: Gaurav",
            },
        }
        ```
        """
        account_type = payout_details["party_account_type"]

        def get_account_details() -> dict:
            match account_type:
                case FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value:
                    return {
                        "bank_account": {
                            "name": self.sanitize_party_name(
                                payout_details["party_name"]
                            ),
                            "ifsc": payout_details["party_bank_ifsc"],
                            "account_number": payout_details["party_bank_account_no"],
                        }
                    }
                case FUND_ACCOUNT_TYPE.VPA.value:
                    return {
                        "vpa": {
                            "address": payout_details["party_upi_id"],
                        }
                    }

        return {
            "account_type": account_type,
            "contact": self._get_party_contact_details(payout_details),
            **get_account_details(),
        }


class RazorpayXLinkPayout(RazorpayXPayout):
    """
    Handle APIs for `Link Payout`.

    :param account_name: RazorpayX Integration account from which `Payout` will be created.

    ---
    Note:
    - ⚠️ Use when payout is made with link (Link will be sent to party's contact details).

    ---
    Reference: https://razorpay.com/docs/api/x/payout-links
    """

    ### CLASS VARIABLES ###
    BASE_PATH = "payout-links"

    ### APIs ###
    def pay(self, payout_details: dict) -> dict:
        """
        Create a `Link Payout` with party's contact details or `RazorpayX Contact ID`.

        :param data: Request body for `Payout`.

        ---
        Params of `payout_details`:

        Mandatory:
        - `amount` :float: Amount to be paid. (Must be in `INR`)
        - `source_doctype` :str: The source document type.
        - `source_docname` :str: The source document name.
        - `party_type` :str: The type of party to be paid (Ex. `Customer`, `Supplier`, `Employee`).
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.
        - `party_contact_details` :dict: Contact details of the party.
            - If pay with  `RazorpayX contact ID`:
                - `razorpayx_contact_id` :str: The RazorpayX Contact ID of the party (Ex. `cont_00HjGh1`).
            - If pay with `party's contact details`:
                - `party_name` :str: Name of the party.
                - `party_mobile` :str: Mobile number of the party.
                - `party_email` :str: Email of the party.

        Optional:
        - `receipt` :str: Receipt details for the payout.
        - `send_sms` :bool: Send SMS to the party if `True`. (Default: `True`)
        - `send_email` :bool: Send Email to the party if `True`. (Default: `True`)
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.
        - `expire_by` :datetime: Expiry date-time of the link.
            - ⚠️ This can be used only if the expiry feature for Payout Links is enabled.
            - Set at least `15 minutes` ahead of the current time.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/create/use-contact-details/

        """
        payout_details.update(**payout_details.pop("party_contact_details"))

        service = (
            "Make Link Payout with Contact Details"
            if "razorpayx_contact_id" not in payout_details
            else "Make Link Payout with RazorpayX Contact ID"
        )

        self._set_service_details_to_ir_log(service)
        return self._make_payout(payout_details)

    def get_by_id(
        self,
        payout_link_id: str,
        *,
        data: str | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> dict:
        """
        Fetch the details of a specific `Link Payout` by Id.

        :param id: `Id` of fund account to fetch (Ex.`poutlk_jkHgLM02`).
        :param data: Specific data to be fetched (Ex. `status`, `utr`, etc.).
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        ---
        Note:
        - If data is not provided, the complete payout details will be fetched.
        - If data is not available, `None` will be returned.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/fetch-with-id
        """
        self._set_service_details_to_ir_log("Fetch Single Payout Link Details")
        return super().get_by_id(
            payout_link_id,
            data=data,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )

    def cancel(
        self,
        payout_link_id: str,
        *,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> dict:
        """
        Cancel a specific `Payout Link` by Id.

        Caution: ⚠️  Only `issued` payout links can be canceled.

        :param payout_link_id: Payout link ID to be canceled (Ex.`poutlk_jkHgLM02`).
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/cancel
        """
        self._set_service_details_to_ir_log("Cancel Payout Link")
        return super().cancel(
            payout_link_id,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )

    ### HELPERS ###
    def _get_mapped_payout_request_body(self, payout_details: dict) -> dict:
        """
        Mapping the request data to RazorpayX `Link Payout` API's required format.

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
            "send_sms": True,
            "send_email": True,
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
                "description": "Payout for customer",
            },
            "expire_by": 1545384058,
        }
        ```

        """
        params_to_delete = ("queue_if_low_balance", "reference_id", "mode")

        mapped_request = self._get_base_mapped_payout_info(payout_details)

        mapped_request["description"] = mapped_request.pop("narration")
        mapped_request["contact"] = self._get_party_contact_details(payout_details)

        if expire_by := payout_details.get("expire_by"):
            mapped_request["expire_by"] = expire_by.timestamp()

        mapped_request["send_sms"] = payout_details.get("send_sms", True)
        mapped_request["send_email"] = payout_details.get("send_email", True)

        for param in params_to_delete:
            del mapped_request[param]

        return mapped_request

    ### VALIDATIONS ###
    def _validate_description(self, json: dict):
        """
        Validate the `description` of the payout link.

        :param json: Payload for `Payout Link`.

        ---
        Note: 🟢 Override this method to customize the validation.
        """
        validate_razorpayx_payout_description(json["description"])
