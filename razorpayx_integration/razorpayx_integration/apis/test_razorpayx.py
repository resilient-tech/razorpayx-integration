"""
Module for API testing and validation.
"""

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI


class RazorPayXTestAPI(BaseRazorPayXAPI):
    """
    Test API for RazorPayX Integration.
    """

    def __init__(
        self,
        id: str,
        secret: str,
        account_number: str | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
        *args,
        **kwargs,
    ):
        self.auth = (id, secret)
        self.account_number = account_number
        self.source_doctype = source_doctype
        self.source_docname = source_docname

        self.default_headers = {}
        self.default_log_values = {}  # Show value in Integration Request Log
        self.sensitive_infos = ()  # Sensitive info to mask in Integration Request Log

    def validate_credentials(self):
        """
        Validate RazorPayX API credentials.
        """
        self._set_service_details_to_ir_log("Validate API Credentials")
        self.set_base_path("transactions")

        self.sensitive_infos += ("output", "url", "data")

        # for new document doc is still not saved in db
        self.source_docname = ""
        self.source_doctype = ""

        self.get_all(filters={"account_number": self.account_number}, count=1)

    def set_base_path(self, path: str):
        """
        Set API path.
        """
        self.BASE_PATH = path

    def _mask_sensitive_info(self, ir_log: dict):
        """
        Mask sensitive info in Integration Request Log.
        """
        if not self.sensitive_infos:
            return

        for key in self.sensitive_infos:
            if key == "output" and ir_log.error:
                continue

            ir_log[key] = "*****"
