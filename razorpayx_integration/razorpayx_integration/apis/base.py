from urllib.parse import urljoin

import frappe
import frappe.utils
import requests
from frappe import _
from frappe.app import UNSAFE_HTTP_METHODS

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.utils import (
    enqueue_integration_request,
    get_end_of_day_epoch,
    get_start_of_day_epoch,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)

RAZORPAYX_BASE_API_URL = "https://api.razorpay.com/v1/"


class SUPPORTED_HTTP_METHOD(BaseEnum):
    GET = "GET"
    DELETE = "DELETE"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


class BaseRazorPayXAPI:
    """
    Base class for RazorPayX APIs.

    Must need `RazorPayX Integration Account` name to initiate API.

    :param razorpayx_account: RazorPayX Integration Account name.
    """

    ### CLASS ATTRIBUTES ###
    BASE_PATH = ""

    ### SETUP ###
    def __init__(self, razorpayx_account: str, *args, **kwargs):
        self.razorpayx_account: RazorPayXIntegrationSetting = frappe.get_doc(
            RAZORPAYX_INTEGRATION_DOCTYPE, razorpayx_account
        )

        self.authenticate_razorpayx_account()

        self.auth = (
            self.razorpayx_account.key_id,
            self.razorpayx_account.get_password("key_secret"),
        )
        self.default_headers = {}
        self.default_log_values = {}  # Show value in Integration Request Log
        self.ir_service_set = False  # Set service details in Integration Request Log
        self.sensitive_infos = ()  # Sensitive info to mask in Integration Request Log
        self.place_holder = "************"

        self.setup(*args, **kwargs)

    def authenticate_razorpayx_account(self):
        """
        Check account is enabled or not?

        Validate RazorPayX API credential `Id` and `Secret` for respective account.
        """
        if self.razorpayx_account.disabled:
            frappe.throw(
                msg=_("To use {0} account, please enable it first!").format(
                    frappe.bold(self.razorpayx_account.name)
                ),
                title=_("RazorPayX Integration Account Is Disable"),
            )

        if not self.razorpayx_account.key_id or not self.razorpayx_account.key_secret:
            frappe.throw(
                msg=_("Please set <strong>RazorPayX</strong> API credentials."),
                title=_("API Credentials Are Missing"),
            )

        if not self.razorpayx_account.webhook_secret:
            frappe.msgprint(
                msg=_(
                    "RazorPayX Webhook Secret is missing! <br> You will not receive any updates!"
                ),
                indicator="yellow",
                alert=True,
            )

    def setup(self, *args, **kwargs):
        """
        Override this method to setup API specific configurations.
        """
        pass

    ### APIs ###
    def get(self, *args, **kwargs):
        """
        Make `GET` HTTP request.
        """
        return self._make_request(SUPPORTED_HTTP_METHOD.GET.value, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Make `DELETE` HTTP request.
        """
        return self._make_request(SUPPORTED_HTTP_METHOD.DELETE.value, *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Make `POST` HTTP request.
        """
        return self._make_request(SUPPORTED_HTTP_METHOD.POST.value, *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Make `PUT` HTTP request.
        """
        return self._make_request(SUPPORTED_HTTP_METHOD.PUT.value, *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Make `PATCH` HTTP request.
        """
        return self._make_request(SUPPORTED_HTTP_METHOD.PATCH.value, *args, **kwargs)

    ### API WRAPPERS ###
    # TODO: should add `skip` in filters (Handle pagination + if not given fetch all) (Change in sub class)
    def get_all(
        self, filters: dict | None = None, count: int | None = None
    ) -> list[dict] | None:
        """
        Fetches all data of given RazorPayX account for specific API.

        :param filters: Filters for fetching filtered response.
        :param count: Total number of item to be fetched.If not given fetches all.
        """
        MAX_LIMIT = 100

        if filters:
            self._clean_request(filters)
            self._set_epoch_time_for_date_filters(filters)
            self._validate_and_process_filters(filters)

        else:
            filters = {}

        if isinstance(count, int) and count <= 0:
            frappe.throw(
                _("Count can't be {0}").format(frappe.bold(count)),
                title=_("Invalid Count To Fetch Data"),
            )

        if count and count <= MAX_LIMIT:
            filters["count"] = count
            return self._fetch(filters)

        if count is None:
            FETCH_ALL_ITEMS = True
        else:
            FETCH_ALL_ITEMS = False

        result = []
        filters["count"] = MAX_LIMIT
        filters["skip"] = 0

        while True:
            items = self._fetch(filters)

            if items and isinstance(items, list):
                result.extend(items)
            else:
                break

            if len(items) < MAX_LIMIT:
                break

            if not FETCH_ALL_ITEMS:
                count -= len(items)
                if count <= 0:
                    break

            filters["skip"] += MAX_LIMIT

        return result

    ### BASES ###
    def _make_request(
        self,
        method: str,
        endpoint: str = "",
        params: dict | None = None,
        headers: dict | None = None,
        json: dict | None = None,
    ):
        """
        Base for making HTTP request.

        Process headers,params and data then make request and return processed response.
        """
        method = method.upper()
        if method not in SUPPORTED_HTTP_METHOD.values():
            frappe.throw(_("Invalid method {0}").format(method))

        request_args = frappe._dict(
            url=self.get_url(endpoint),
            params=params,
            headers={
                **self.default_headers,
                **(headers or {}),
            },
            auth=self.auth,
        )

        # preparing log for Integration Request
        self._set_source_to_ir_log()

        ir_log = frappe._dict(
            **self.default_log_values,
            url=request_args.url,
            data=request_args.params,
            request_headers=request_args.headers.copy(),
        )

        if method in UNSAFE_HTTP_METHODS and json:
            request_args.json = json

            copied_json = json.copy()

            if not request_args.params:
                ir_log.data = copied_json
            else:
                ir_log.data = {
                    "params": request_args.params,
                    "body": copied_json,
                }

        response_json = None

        try:
            self._before_request(request_args)

            response = requests.request(method, **request_args)
            response_json = response.json(object_hook=frappe._dict)

            if response.status_code >= 400:
                self._handle_failed_api_response(response_json)

            # Raise HTTPError for other HTTP codes
            response.raise_for_status()

            return response_json

        except Exception as e:
            ir_log.error = str(e)
            raise e
        finally:
            if response_json:
                ir_log.output = response_json.copy()

            self._mask_sensitive_info(ir_log)

            if not ir_log.integration_request_service:
                ir_log.integration_request_service = "RazorPayX Integration"

            enqueue_integration_request(**ir_log)

    def _fetch(self, params: dict) -> list:
        """
        Fetches `items` from the API response based on the given parameters.
        """
        response = self.get(params=params)
        return response.get("items", [])

    ### API HELPERS ###
    def get_url(self, *path_segments):
        """
        Generate particular API's URL by combing given path_segments.

        Example:
            if path_segments = 'contact/old' then
            URL will `RAZORPAYX_BASE_URL/BASE_PATH/contact/old`
        """

        path_segments = list(path_segments)

        if self.BASE_PATH:
            path_segments.insert(0, self.BASE_PATH)

        return urljoin(
            RAZORPAYX_BASE_API_URL,
            "/".join(segment.strip("/") for segment in path_segments),
        )

    def _before_request(self, request_args):
        """
        Override in sub class to perform any operation before making the request.
        """
        return

    def _clean_request(self, filters: dict):
        """
        Cleans the request filters by removing any key-value pairs where
        the value is falsy.
        """
        keys_to_delete = [key for key, value in filters.items() if not value]

        for key in keys_to_delete:
            del filters[key]

    def _set_epoch_time_for_date_filters(self, filters: dict):
        """
        Converts  the date filters `from` and `to` to epoch time (Unix timestamp).
        """
        if from_date := filters.get("from"):
            filters["from"] = get_start_of_day_epoch(from_date)

        if to_date := filters.get("to"):
            filters["to"] = get_end_of_day_epoch(to_date)

    def _validate_and_process_filters(self, filters: dict):
        """
        Override in sub class to validate and process filters, except date filters (from,to).

        Validation happen before `get_all()` to reduce API calls.
        """
        pass

    ### LOGGING ###
    def _set_service_details_to_ir_log(
        self, service_name: str, service_set: bool = True
    ):
        """
        Set the service details in the Integration Request Log.

        :param service_name: The service name.
        :param service_set:  Set flag that service name for Integration request has been set or not.
        """
        self.default_log_values.update(
            {"integration_request_service": f"RazorPayX - {service_name}"}
        )

        self.ir_service_set = service_set

    def _set_source_to_ir_log(self):
        """
        Set the source document details in the Integration Request Log.
        """
        if not (self.source_doctype and self.source_docname):
            return

        self.default_log_values.update(
            {
                "reference_doctype": self.source_doctype,
                "reference_name": self.source_docname,
            }
        )

    def _mask_sensitive_info(self, ir_log: dict):
        """
        Mask sensitive information in the Integration Request Log.
        """
        pass

    ### ERROR HANDLING ###
    # TODO:  handle special(error) http code (specially payout process!!)
    def _handle_failed_api_response(self, response_json: dict | None = None):
        """
        Handle failed API response from RazorPayX.

        ---
        Error response format:
        ```py
        {
            "error": {
                "code": "SERVER_ERROR",
                "description": "Server Is Down",
                "source": "NA",
                "step": "NA",
                "reason": "NA",
                "metadata": {},
            },
        }
        ```

        ---
        Reference: https://razorpay.com/docs/errors/#sample-code
        """
        error_msg = "There is some error in <strong>RazorPayX</strong>"
        title = _("RazorPayX API Failed")

        if response_json:
            error_msg = (
                response_json.get("message")
                or response_json.get("error", {}).get("description")
                or error_msg
            )

        self._handle_custom_error(error_msg, title=title)

        frappe.throw(
            msg=_(error_msg),
            title=title,
        )

    def _handle_custom_error(self, error_msg: str, title: str | None = None):
        """
        Handle custom error message.

        :param error_msg: RazorPayX API error message.
        :param title: Title of the error message.
        """
        match error_msg:
            case "Different request body sent for the same Idempotency Header":
                error_msg = _(
                    "Please cancel/delete the current document and pay with a new document."
                )

                error_msg += "<br><br>"

                error_msg += _(
                    "You faced this issue because payment details were changed after the first payment attempt."
                )

                title = _("Payment Details Changed")

            case "Authentication failed":
                error_msg = _(
                    "RazorPayX API credentials are invalid. Please set valid <strong>Key ID</strong> and <strong>Key Secret</strong>."
                )

                title = _("RazorPayX Authentication Failed")

            case "The RazorpayX Account number is invalid.":
                error_msg = _(
                    "Bank Account number is not matching with the <strong>RazorPayX</strong> account. <br> Please set valid <strong>Bank Account</strong>."
                )

                title = _("Invalid Bank Account Number")

        if not title:
            title = _("RazorPayX API Failed")

        frappe.throw(title=title, msg=error_msg)
