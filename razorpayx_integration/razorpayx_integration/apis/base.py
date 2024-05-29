from urllib.parse import urljoin

import frappe
import requests
from frappe import _

# todo : Handle For Multiple Account !


class BaseRazorPayXAPI:
    # todo: utils attribute
    BASE_PATH = ""

    # todo: details from bank_account ...
    def __init__(self,bank_account, *args, **kwargs):
        self.settings = get_razorpayx_settings()
        if not is_razorpayx_api_enabled(self.settings):
            frappe.throw(_("Please provide <b>RazorpayX API's</b> auth"))

        self.auth = (self.settings.key_id, self.settings.get_password("key_secret"))
        self.default_headers = {}

        self.setup(*args, **kwargs)

    # todo: setup in subclass
    def setup(*args, **kwargs):
        # Override in subclass
        pass

    def get_url(self, *path_segments):
        path_segments = list(path_segments)

        if self.BASE_PATH:
            path_segments.insert(0, self.BASE_PATH)

        return urljoin(
            BASE_URL, "/".join(segment.strip("/") for segment in path_segments)
        )

    def get(self, *args, **kwargs):
        return self._make_request("GET", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._make_request("DELETE", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._make_request("POST", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._make_request("PUT", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._make_request("PATCH", *args, **kwargs)

    def _make_request(
        self,
        method: str,
        endpoint: str = "",
        params: dict = None,
        headers: dict = None,
        json: dict = None,
    ):
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
            or "Give Proper RazorpayX API Attributes"
        ).title()

        frappe.throw(
            msg=_(error_msg),
            title=_("RazorpayX API Failed"),
        )
