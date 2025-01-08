import frappe
from frappe import _
from frappe.utils import fmt_money, get_link_to_form

from razorpayx_integration.payment_utils.utils import paisa_to_rupees, rupees_to_paisa
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    CONTACT_TYPE,
    CONTACT_TYPE_MAP,
    FUND_ACCOUNT_TYPE,
    PAYMENT_MODE_THRESHOLD,
    PAYOUT_CURRENCY,
    PAYOUT_MODE,
    PAYOUT_PURPOSE,
    PAYOUT_PURPOSE_MAP,
)
from razorpayx_integration.razorpayx_integration.utils.validation import (
    validate_razorpayx_payout_description,
    validate_razorpayx_payout_link_status,
    validate_razorpayx_payout_mode,
    validate_razorpayx_payout_status,
)

# TODO: in other than payout api add args for ref_doctype and ref_docname? to log in IR


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

    ### CLASS VARIABLES ###
    BASE_PATH = "payouts"
    DEFAULT_SOURCE_AMOUNT_FIELD = "paid_amount"

    ### SETUPS ###
    def setup(self, *args, **kwargs):
        """
        Override this method to setup `API` specific configurations.

        Caution: ⚠️ Don't forget to call `super().setup()` in sub class.
        """
        super().setup(*args, **kwargs)

        self.razorpayx_account_number = self.razorpayx_account.account_number
        self.default_payout_request = {
            "account_number": self.razorpayx_account_number,
            "queue_if_low_balance": True,
            "currency": PAYOUT_CURRENCY.INR.value,
        }
        self.payout_headers = {}
        self.source_amount_field_map = {
            "Payment Entry": "paid_amount",
        }

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
        payout_details["mode"] = self._get_bank_payment_mode(payout_details)

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
        payout_details["mode"] = PAYOUT_MODE.UPI.value

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
        if source_doctype and source_docname:
            self._set_source_to_ir_log(source_doctype, source_docname)

        response = self.get(endpoint=payout_id)

        if not data:
            return response

        return response.get(data)

    def get_all(
        self,
        *,
        filters: dict | None = None,
        count: int | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> list[dict]:
        """
        Get all `Payouts` associate with given `RazorPayX` account if count is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of payouts to be retrieved.
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        :raises ValueError: If `mode` or `status` is not valid (if specified).

        ---
        Example Usage:
        ```
        payout = RazorPayXPayout(RAZORPAYX_BANK_ACCOUNT)
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
        if source_doctype and source_docname:
            self._set_source_to_ir_log(source_doctype, source_docname)

        if not filters:
            filters = {}

        # account number is mandatory
        filters["account_number"] = self.razorpayx_account_number

        return super().get_all(filters, count)

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
        if source_doctype and source_docname:
            self._set_source_to_ir_log(source_doctype, source_docname)

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

        # set values for Integration Request Log
        self._set_source_to_ir_log(self.source_doctype, self.source_docname)

        self._set_idempotency_key_header(json)

        self._validate_payout_payload(json)

        return self.post(json=json, headers=self.payout_headers)

    ### HELPERS ###
    def _get_bank_payment_mode(self, payout_details: dict) -> str:
        """
        Return the payment mode for the payout.

        :param payout_details: Request body for `Payout`.

        Returns: NEFT | RTGS | IMPS
        """

        if payout_details.get("pay_instantaneously") is True:
            return PAYOUT_MODE.IMPS.value
        else:
            if payout_details["amount"] > PAYMENT_MODE_THRESHOLD.NEFT.value:
                return PAYOUT_MODE.RTGS.value
            else:
                return PAYOUT_MODE.NEFT.value

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

        self.payout_headers["X-Payout-Idempotency"] = self.source_docname

    def _get_mapped_payout_request_body(self, payout_details: dict) -> dict:
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
                **payout_details.get("notes", {}),
            }

        return {
            **self.default_payout_request,
            "amount": rupees_to_paisa(payout_details["amount"]),
            "mode": payout_details.get("mode", PAYOUT_MODE.NEFT.value),
            "purpose": get_purpose(),
            "reference_id": get_reference_id(),
            "narration": payout_details.get("description", ""),
            "notes": get_notes(),
        }

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
                case FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value:
                    return {
                        "bank_account": {
                            "name": payout_details["party_name"],
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
            "account_type": payout_details["party_account_type"],
            **get_account_details(payout_details["party_account_type"]),
            "contact": self._get_party_contact_details(payout_details),
        }

    def _get_party_contact_details(self, payout_details: dict) -> dict:
        """
        Make a dictionary for `Contact` to be used in `Payout`.

        :param data: Request body for `Payout`.

        ---
        Contact Sample:
        ```
        # If `razorpayx_party_contact_id` is not provided
        {
            "name": "Gaurav Kumar",
            "email": "gauravemail@gmail.com",
            "contact": "9123456789",
            "type": "customer",
            "reference_id": "cont_00HjGh1",
        }

        # If `razorpayx_party_contact_id` is provided
        {"id": "cont_00HjGh1"}
        ```
        """

        def get_type() -> str:
            return CONTACT_TYPE_MAP.get(
                payout_details["party_type"], CONTACT_TYPE.SELF.value
            )

        if contact_id := payout_details.get("razorpayx_party_contact_id"):
            return {"id": contact_id}

        return {
            "name": payout_details["party_name"],
            "email": payout_details.get("party_email", ""),
            "contact": payout_details.get("party_mobile", ""),
            "type": get_type(),
            "reference_id": payout_details.get("party_id", ""),
        }

    def _get_source_amount(self, json: dict) -> float:
        """
        Get the amount from the source document.

        :param json: Payload for `Payout`.

        ---
        Note: 🟢 Override this method to customize the amount fetching.
        """
        amount_field = (
            self.source_amount_field_map.get(self.source_doctype)
            or self.DEFAULT_SOURCE_AMOUNT_FIELD
        )

        return frappe.db.get_value(
            self.source_doctype, self.source_docname, amount_field
        )

    def _set_source_to_ir_log(self, source_doctype: str, source_docname: str):
        """
        Set the source document details in the Integration Request Log.

        :param source_doctype: The source document type.
        :param source_docname: The source document name.
        """
        self.default_log_values.update(
            {
                "reference_doctype": source_doctype,
                "reference_name": source_docname,
            }
        )

    ### VALIDATIONS ###
    def _validate_payout_payload(self, json: dict):
        """
        Validation before making payout.

        :param json: Payload for `Payout`.
        """
        self._validate_amount(json)
        self._validate_description(json)
        self._validate_payout_mode(json)

    def _validate_amount(self, json: dict):
        """
        Validate the `amount` of the payout.

        Compare amount with source document amount.

        :param json: Payload for `Payout`.

        ---
        Note: 🟢 Override this method to customize the validation.
        """

        def format_amount(amount: float) -> str:
            return fmt_money(amount, currency=PAYOUT_CURRENCY.INR.value)

        source_amount = self._get_source_amount(json)
        payout_amount = paisa_to_rupees(json["amount"])

        if source_amount == payout_amount:
            return

        message = _(
            "The payout amount {0} does not match with the source document amount {1}."
        ).format(
            frappe.bold(format_amount(payout_amount)),
            frappe.bold(format_amount(source_amount)),
        )

        message += "<br>"

        message += _("Please check the source document {0}.").format(
            frappe.bold(get_link_to_form(self.source_doctype, self.source_docname))
        )

        frappe.throw(
            msg=message,
            title=_("Amount Mismatch"),
        )

    def _validate_description(self, json: dict):
        """
        Validate the `narration` of the payout.

        :param json: Payload for `Payout`.

        ---
        Note: 🟢 Override this method to customize the validation.
        """
        if narration := json.get("narration"):
            validate_razorpayx_payout_description(narration)

    def _validate_payout_mode(self, json: dict):
        """
        Validate the `mode` of the payout.

        :param json: Request or Filter data.
        """
        if mode := json.get("mode"):
            validate_razorpayx_payout_mode(mode)

    def _validate_status(self, json: dict):
        """
        Validate the `status` of the payout.

        :param json: Request or Filter data.
        """
        if status := json.get("status"):
            validate_razorpayx_payout_status(status)

    def _validate_and_process_filters(self, filters: dict):
        """
        Validation before `get_all` API call.

        :param filters: Filters for fetching filtered response.
        """
        self._validate_payout_mode(filters)
        self._validate_status(filters)


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
        payout_details["mode"] = self._get_bank_payment_mode(payout_details)
        payout_details["party_account_type"] = (  # noqa: RUF100
            FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value
        )

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
        payout_details["mode"] = PAYOUT_MODE.UPI.value
        payout_details["party_account_type"] = FUND_ACCOUNT_TYPE.VPA.value

        return self._make_payout(payout_details)

    ### HELPERS ###
    def _get_mapped_payout_request_body(self, payout_details) -> dict:
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
        mapped_request = self._get_base_mapped_payout_info(payout_details)

        mapped_request["fund_account"] = self._get_party_fund_account_details(
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

    ### CLASS VARIABLES ###
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
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.

        Optional:
        - `receipt` :str: Receipt details for the payout.
        - `send_sms` :bool: Send SMS to the party if `True`. (Default: `True`)
        - `send_email` :bool: Send Email to the party if `True`. (Default: `True`)
        - `reference_id` :str: Reference Id of the payout.
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.
        - `expire_by` :datetime: Expiry date-time of the link.
            - ⚠️ This parameter can be used only if you have enabled the expiry feature for Payout Links.
            - Set at least 15 minutes ahead of the current time.

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
        - `razorpayx_party_contact_id` :str: The RazorPayX Contact ID of the party (Ex. `cont_00HjGh1`).
        - `description` :str: Description of the payout.
           - Maximum length `30` characters. Allowed characters: `a-z`, `A-Z`, `0-9` and `space`.

        Optional:
        - `receipt` :str: Receipt details for the payout.
        - `send_sms` :bool: Send SMS to the party if `True`. (Default: `True`)
        - `send_email` :bool: Send Email to the party if `True`. (Default: `True`)
        - `purpose` :str: Purpose of the payout. (Default: `Payout` or decided by `party_type`)
        - `notes` :dict: Additional notes for the payout.
        - `expire_by` :datetime: Expiry date-time of the link.
            - ⚠️ This parameter can be used only if you have enabled the expiry feature for Payout Links.
            - Set at least 15 minutes ahead of the current time.

        ---
        Reference: https://razorpay.com/docs/api/x/payout-links/create/use-contact-id
        """
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
        return super().get_by_id(
            payout_link_id,
            data=data,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )

    def get_all(
        self,
        *,
        filters: dict | None = None,
        count: dict | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ) -> list[dict]:
        """
        Get all `Payout Links` associate with given `RazorPayX` account if count is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of payouts to be retrieved.
        :param source_doctype: The source document type.
        :param source_docname: The source document name.

        :raises ValueError: If `status` is not valid (if specified).

        ---
        Example Usage:
        ```
        link_payout = RazorPayXLinkPayout(RAZORPAYX_BANK_ACCOUNT)
        filters = {
            "id":"poutlk_jkHgLM02",
            "contact_id":"cont_00HjGh1",
            "contact_phone_number":"9123456789",
            "contact_email":"gaurvaexmaple@gmail.com",
            "purpose":"payout",
            "fund_account_id":"fa_00HjHue1",
            "receipt":"ACC-PAY-003-2024-06-01",
            "short_url":"https://rzp.io/p/abc",
            "status":"processing",
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=link_payout.get_all(filters)
        ```

        ---
        Note:
        - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).

        ---
        Reference: https://razorpay.com/docs/api/x/payouts/fetch-all/
        """
        return super().get_all(
            filters=filters,
            count=count,
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
        return super().cancel(
            payout_link_id,
            source_doctype=source_doctype,
            source_docname=source_docname,
        )

    ### HELPERS ###
    def _get_mapped_payout_request_body(self, payout_details: dict) -> dict:
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
            "send_sms": True,
            "send_email": True,
            "notes": {
                "source_doctype": "Payment Entry",
                "source_docname": "PE-0001",
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

    def _validate_status(self, json):
        """
        Validate the `status` of the payout link.

        :param json: Request or Filter data.

        """
        if status := json.get("status"):
            validate_razorpayx_payout_link_status(status)

    def _validate_and_process_filters(self, filters):
        """
        Validation before `get_all` API call.

        :param filters: Filters for fetching filtered response.
        """
        self._validate_status(filters)
