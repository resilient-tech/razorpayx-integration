from urllib.parse import urljoin

import frappe
import requests
from frappe import _
from frappe.app import UNSAFE_HTTP_METHODS

from razorpayx_integration.constants import (
    RAZORPAYX,
    RAZORPAYX_BASE_API_URL,
    RAZORPAYX_INTEGRATION_DOCTYPE,
    SUPPORTED_HTTP_METHOD,
)
from razorpayx_integration.payment_utils.utils import (
    get_end_of_day_epoch,
    get_start_of_day_epoch,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)

# TODO: logs for API calls.
# TODO: mask sensitive data in logs.


class BaseRazorPayXAPI:
    """
    Base class for RazorPayX APIs.\n
    Must need `RazorPayX Account Name` to initiate API.
    """

    # * utility attributes
    BASE_PATH = ""

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

        self.setup(*args, **kwargs)

    # ? How to validate razorpayx_account's API credential
    # ? can be add to utility
    def authenticate_razorpayx_account(self):
        """
        Check account is enabled or not?\n
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
                msg=_("Please set {0} API credentials.").format(RAZORPAYX),
                title=_("API Credentials Are Missing"),
            )

    def setup(self, *args, **kwargs):
        # Override in subclass
        pass

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

    def get_all(
        self, filters: dict | None = None, count: int | None = None
    ) -> list[dict]:
        """
        Fetches all data of given RazorPayX account for specific API.

        :param filters: Filters for fetching filtered response.
        :param count: Total number of item to be fetched.If not given fetches all.
        """
        if filters:
            self._clean_request_filters(filters)
            self._set_epoch_time_for_date_filters(filters)
            self.validate_and_process_request_filters(filters)

        else:
            filters = {}

        if isinstance(count, int) and count <= 0:
            frappe.throw(
                _("Count can't be {0}").format(frappe.bold(count)),
                title=_("Invalid Count To Fetch Data"),
            )

        if count and count <= 100:
            filters["count"] = count
            return self._fetch(filters)

        if count is None:
            FETCH_ALL_ITEMS = True
        else:
            FETCH_ALL_ITEMS = False

        result = []
        filters["count"] = 100  # max limit is 100
        filters["skip"] = 0

        while True:
            items = self._fetch(filters)

            if items and isinstance(items, list):
                result.extend(items)
            else:
                break

            if len(items) < 100:
                break

            if not FETCH_ALL_ITEMS:
                count -= len(items)
                if count <= 0:
                    break

            filters["skip"] += 100

        return result

    def _make_request(
        self,
        method: str,
        endpoint: str = "",
        params: dict | None = None,
        headers: dict | None = None,
        json: dict | None = None,
    ):
        """
        Base for making HTTP request.\n
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

        if method in UNSAFE_HTTP_METHODS and json:
            request_args.json = json

        try:
            response = requests.request(method, **request_args)
            response_json = response.json(object_hook=frappe._dict)

            if response.status_code >= 400:
                self.handle_failed_api_response(response_json)

            return response_json

        except Exception as e:
            raise e

    # todo:  also accept endpoint,headers
    def _fetch(self, params: dict) -> list:
        """
        Fetches `items` from the API response based on the given parameters.
        """
        response = self.get(params=params)
        return response.get("items", [])

    def _clean_request_filters(self, filters: dict):
        """
        Cleans the request filters by removing any key-value pairs where
        the value is falsy.
        """
        keys_to_delete = [key for key, value in filters.items() if not value]

        for key in keys_to_delete:
            del filters[key]

    def _set_epoch_time_for_date_filters(self, filters: dict):
        """
        Converts `from` and `to` date filters to epoch time.
        """
        if from_date := filters.get("from"):
            filters["from"] = get_start_of_day_epoch(from_date)

        if to_date := filters.get("to"):
            filters["to"] = get_end_of_day_epoch(to_date)

    def validate_and_process_request_filters(self, filters: dict):
        # override in sub class
        # validate and process filters except date filters (from,to)
        pass

    # TODO:  handle special(error) http code (specially payout process!!)
    def handle_failed_api_response(self, response_json: dict | None = None):
        """
        Handle failed API response from RazorPayX.

        Error response format:
        {
            "error": {
                "code": "SERVER_ERROR",
                "description": "Server Is Down",
                "source": "NA",
                "step": "NA",
                "reason": "NA",
                "metadata": {}
            }
        }
        """
        error_msg = "There is some error in <strong>RazorPayX</strong>"

        if response_json:
            error_msg = (
                response_json.get("message")
                or response_json.get("error", {}).get("description")
                or error_msg
            ).title()

        frappe.throw(
            msg=_(error_msg),
            title=_("{0} API Failed").format(RAZORPAYX),
        )
