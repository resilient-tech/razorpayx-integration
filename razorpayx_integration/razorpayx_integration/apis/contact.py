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
    :param str account_name: RazorPayX account for which this `Contact` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/contacts
    """

    # * utility attributes
    BASE_PATH = "contacts"

    # * override base setup
    def setup(self):
        pass

    ### APIs ###
    def create(self, **kwargs) -> dict:
        """
        Creates `RazorPayX Contact`.

        :param dict json: Full details of contact to create.
        :param str name: The contact's name.
        :param str type: Must be one of ["employee", "supplier"] (if passed).
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not one of ["employee", "supplier"].\n
        ---
        Example Usage:
        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        response = contact.create(
            name="Joe Doe",
            type="employee",
            email="joe123@gmail.com",
            contact="7434870169",
            id="empl-02",
            note="New Employee",
        )
        ---
        json = {
            "name"="Joe Doe",
            "type"="employee",
            "email"="joe123@gmail.com",
            "contact"="7434870169",
            "id"="empl-02",
            "note"="New Employee",
        }

        response = contact.create(json=json)
        ```
        ---
        Note:
            - If json passed in args, then other args will discarded.
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/create
        """
        contact_details = self._process_request_data(kwargs)
        return self.post(json=contact_details)

    def fetch_by_id(self, id: str) -> dict:
        """
        Fetch the details of a specific `Contact` by Id.
        :param str id: `Id` of contact to fetch (Ex.`cont_hkj012yuGJ`).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-with-id
        """
        return self.get(endpoint=id)

    def get_all(self, filters: dict = {}, limit: int = None) -> list[dict]:
        """
        Get all `Contacts` associate with given `RazorPayX` account if limit is not given.

        :param dict filters: Result will be filtered as given filters.
        :param int limit: The number of contacts to be retrieved (`Max Limit : 100`).

        :raises ValueError: If `type` is not one of ["employee", "supplier"].\n
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
            "type":"employee",
            "from":"2024-01-01"
            "to":"2024-06-01"
        }
        response=contact.get_all(filters)
        ```
        ---
        Note:
            - Not all filters are require.
            - `active` can be int or boolean.
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-all
        """
        if filters:
            filters = self._process_filters(filters)

        if limit and limit <= 100:
            filters["count"] = limit
            return self._fetch(filters)

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
            filters["skip"] = skip

        return contacts

    def update(self, id: str, **kwargs):
        """
        Updates `RazorPayX Contact`.

        :param str id: Contact Id of whom to update details (Ex.`cont_hkj012yuGJ`).
        :param dict json: Full details of contact to create.
        :param str name: The contact's name.
        :param str type: Must be one of ["employee", "supplier"] (if passed).
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not one of ["employee", "supplier"].\n
        ---
        Example Usage:
        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        response = contact.update(
            id='cont_hkj012yuGJ'
            name="Joe Doe",
            type="employee",
            email="joe123@gmail.com",
            contact="7434870169",
            id="empl-02",
            note="New Employee",
        )
        ---
        json = {
            "name"="Joe Doe",
            "type"="employee",
            "email"="joe123@gmail.com",
            "contact"="7434870169",
            "id"="empl-02",
            "note"="New Employee",
        }

        response = contact.update(id='cont_hkj012yuGJ',json=json)
        ```
        ---
        Note:
            - If json passed in args, then other args will discarded.
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/update
        """
        filters = self._process_request_data(kwargs)
        return self.patch(endpoint=id, json=filters)

    def activate(self, id: str) -> dict:
        """
        Activate the contact for the given `Id` if it is deactivated.

        :param str id: `Id` of contact to make activate (Ex.`cont_hkj012yuGJ`).
        """
        return self._change_state(id=id, active=True)

    def deactivate(self, id: str) -> dict:
        """
        Deactivate the contact for the given `Id` if it is activated.

        :param str id: `Id` of contact to make deactivate (Ex.`cont_hkj012yuGJ`).
        """
        return self._change_state(id=id, active=False)

    ### Bases ###
    def _fetch(self, params: dict) -> list:
        """
        Fetch `Contacts` associate with given `RazorPayX` account.
        """
        response = self.get(params=params)
        return response.get("items", [])

    def _change_state(self, id: str, active: bool) -> dict:
        """
        Change the state of the `Contact` for the given Id.

        :param str id: Id of `Contact` to change state (Ex.`cont_hkj012yuGJ`).
        :param bool active: Represent state. (`True`:Active,`False`:Inactive)
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/activate-or-deactivate
        """
        return self.patch(endpoint=id, json={"active": active})

    ### Helpers ###
    def _process_request_data(self, request_data: dict) -> dict:
        json = request_data.get("json")
        if json and isinstance(json, dict):
            if id := json.get("id"):
                json["reference_id"] = id
                del json["id"]

            if note := json.get("note"):
                json["notes"] = {"notes_key_1": note}
                del json["note"]

            return self._validate_request_data(json)

        process_data = {
            "name": request_data.get("name"),
            "type": request_data.get("type"),
            "email": request_data.get("email"),
            "contact": request_data.get("contact"),
            "reference_id": request_data.get("id"),
            "notes": (
                {"notes_key_1": request_data.get("note")}
                if request_data.get("note")
                else None
            ),
        }

        return self._validate_request_data(process_data)

    def _validate_request_data(self, request_data: dict) -> dict:
        # Remove keys with None values
        request_data = {
            key: value for key, value in request_data.items() if value is not None
        }

        if email := request_data.get("email"):
            validate_email_address(email, throw=True)

        if type := request_data.get("type"):
            # ? can remove MAP and use directly vendor instead of supplier!
            validate_razorpayx_contact_type(type)
            request_data["type"] = RAZORPAYX_CONTACT_MAP[type]

        return request_data

    def _process_filters(self, filters: dict) -> dict:
        filters = self._validate_request_data(filters)

        if from_date := filters.get("from"):
            filters["from"] = get_start_of_day_epoch(from_date)

        if to_date := filters.get("to"):
            filters["to"] = get_end_of_day_epoch(to_date)

        return filters
