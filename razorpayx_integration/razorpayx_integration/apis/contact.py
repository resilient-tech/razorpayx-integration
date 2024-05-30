from typing import Literal

from frappe.utils import validate_email_address

from razorpayx_integration.constant import (
    RAZORPAYX_CONTACT_MAP,
)
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.utils import (
    get_end_of_day_epoch,
    get_start_of_day_epoch,
    validate_razorpayx_contact_type,
)

# todo : use composite API, If composite APIs working properly fine then no need of this API


class RazorPayXContact(BaseRazorPayXAPI):
    """
    Handle APIs for RazorPayX Contact.

    :param str account_name: RazorPayX account for which this contact is associate.

    ---
    Reference: https://razorpay.com/docs/api/x/contacts
    """

    # * utility attributes
    BASE_PATH = "contacts"

    # * override base setup
    def setup(self):
        pass

    ### APIs ###

    def create(
        self, name: str, type: Literal["Employee", "Supplier"], **kwargs
    ) -> dict:
        """
        Creates `RazorPayX Contact`.

        :param str name: The contact's name.
        :param str type: Must be one of ["employee", "supplier"].
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str reference_id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not one of ["employee", "supplier"].\n
        ---
        Example Usage:
        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        response = contact.create(
            "Joe Doe",
            "Employee",
            email="joe123@gmail.com",
            contact="7434870169",
            reference_id="empl-02",
            note="New Employee",
        )
        ```
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/create
        """
        data = {
            "name": name,
            "type": RAZORPAYX_CONTACT_MAP[type],
            "email": kwargs.get("email"),
            "contact": kwargs.get("contact"),
            "reference_id": kwargs.get("reference_id"),
            "notes": (
                {"notes_key_1": kwargs.get("note")} if kwargs.get("note") else None
            ),
        }

        self._process_creation_data(data)

        return self.post(json=data)

    def _fetch(self, params: dict) -> list:
        """
        Fetch `Contacts` associate with given `RazorPayX` account.
        """
        response = self.get(params=params)
        return response.get("items", [])

    def get_all(self, filters: dict = {}, limit: int = None) -> list[dict]:
        """
        Get all `Contacts` associate with given `RazorPayX` account if limit is not given.

        :param dict filters: Result will be filtered as given filters.
        :param int limit: The number of contacts to be retrieved (`Max Limit : 100`).
        ---
        Example Usage:
        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        filters = {
            "name":"joe",
            "email":"joe@gmail.com",
            "contact":"743487045",
            "reference_id":"empl_001",
            "active":1 | True,
            "type":"Employee",
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=contact.get_all(filters=filters)
        ```
        ---
        Note:
            - Not all keys are require.
            - `active` can be int or boolean.
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-all
        """
        if filters:
            self._process_filters(filters)

        if limit and limit <= 100:
            filters["count"] = limit
            return self._fetch(filters=filters)

        skip = 0
        contacts = []
        filters["count"] = 100
        filters["skip"] = 0

        while True:
            items = self._fetch(filters)

            if items and len(items) > 0:
                contacts.extend(items)
            else:
                break

            if isinstance(limit, int):
                limit -= len(items)
                if limit <= 0:
                    break

            skip += 100
            filter["skip"] = skip

        return contacts

    ### Helpers ###
    def _process_creation_data(self, data: dict):
        # Remove keys with None values
        data = {key: value for key, value in data.items() if value is not None}

        validate_razorpayx_contact_type(data.get("type"))

        if email := data.get("email"):
            validate_email_address(email, throw=True)

    def _process_filters(self, filters: dict):
        if email := filters.get("email"):
            validate_email_address(email, throw=True)

        if type := filters.get("type"):
            validate_razorpayx_contact_type(type)

        if from_date := filters.get("from"):
            filters["from"] = get_start_of_day_epoch(from_date)

        if to_date := filters.get("to"):
            filters["to"] = get_end_of_day_epoch(to_date)
