"""
Module for API testing and validation.
"""

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI


class RazorPayXValidation(BaseRazorPayXAPI):
    """
    Validate RazorPayX APIs.

    :param id: RazorPayX API Key ID
    :param secret: RazorPayX API Key Secret
    :param account_number: RazorPayX Account Number
    :param source_doctype: Source Doctype
    :param source_docname: Source Docname
    """

    def __init__(
        self,
        id: str,
        secret: str,
        account_number: str | None = None,
        source_doctype: str | None = None,
        source_docname: str | None = None,
    ):
        """
        Validate RazorPayX APIs.

        :param id: RazorPayX API Key ID
        :param secret: RazorPayX API Key Secret
        :param account_number: RazorPayX Account Number
        :param source_doctype: Source Doctype
        :param source_docname: Source Docname
        """
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

        - Key ID
        - Key Secret
        """
        self._set_service_details_to_ir_log("Validate API Credentials")
        self.set_base_path("transactions")

        self.get_all(filters={"account_number": self.account_number}, count=1)

    def set_base_path(self, path: str):
        """
        Set base API path.
        """
        self.BASE_PATH = path
