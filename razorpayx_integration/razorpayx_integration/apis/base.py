from urllib.parse import urljoin

import frappe
import requests
from frappe import _

from razorpayx_integration.constant import (
    BASE_URL,
    RAZORPAYX,
    UNSAFE_HTTP_METHODS,
    VALID_HTTP_METHODS,
)
from razorpayx_integration.utils import get_razorpayx_account


# todo: logs for API calls.
class BaseRazorPayXAPI:
    """
    Base class for RazorPayX APIs.\n
    Must need `RazorPayX Account Name` to initiate API.
    """

    # * utility attributes
    BASE_PATH = ""

    def __init__(self, account_name: str, *args, **kwargs):
        self.razorpayx_account = get_razorpayx_account(account_name)
        self.authenticate_razorpayx_account()

        self.account_number = self.razorpayx_account.account_number
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
                msg=_(
                    f"To use <b>{self.razorpayx_account.bank_account} account enable it first</b>"
                ),
                title=_("Account Is Disable"),
            )

        # todo : if credential authenticate then check `Key Authorized` field

    def setup(*args, **kwargs):
        # Override in subclass
        pass

    # ? why multiple path_segment require? it is already string
    def get_url(self, *path_segments):
        """
        Generate particular API's URL by combing given path_segments.

        Example:
            if path_segments = 'contact/old' then
            URL will `BASEURL/BASE_PATH/contact/old`
        """

        path_segments = list(path_segments)

        if self.BASE_PATH:
            path_segments.insert(0, self.BASE_PATH)

        return urljoin(
            BASE_URL, "/".join(segment.strip("/") for segment in path_segments)
        )

    def get(self, *args, **kwargs):
        """
        Make `GET` HTTP request.
        """
        return self._make_request("GET", *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Make `DELETE` HTTP request.
        """
        return self._make_request("DELETE", *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Make `POST` HTTP request.
        """
        return self._make_request("POST", *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Make `PUT` HTTP request.
        """
        return self._make_request("PUT", *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Make `PATCH` HTTP request.
        """
        return self._make_request("PATCH", *args, **kwargs)

    def _make_request(
        self,
        method: str,
        endpoint: str = "",
        params: dict = None,
        headers: dict = None,
        json: dict = None,
    ):
        """
        Base for making HTTP request.\n
        Process headers,params and data then make request and return processed response.
        """
        method = method.upper()
        if method not in VALID_HTTP_METHODS:
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

            if response.status_code != 200:
                self.handle_failed_api_response(response_json)

            return response_json

        except Exception as e:
            raise e

    # todo:  handle special(error) http code (specially payout process!!)
    def handle_failed_api_response(self, response_json: dict):
        """
        - Error response:
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
        error_msg = (
            response_json.get("message")
            or response_json.get("error").get("description")
            or f"There is some error occur in {RAZORPAYX} API"
        ).title()

        frappe.throw(
            msg=_(error_msg),
            title=_(f"{RAZORPAYX} API Failed"),
        )
