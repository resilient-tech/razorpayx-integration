from typing import Optional, Union

from frappe.utils import validate_email_address

from razorpayx_integration.constants import RAZORPAYX_CONTACT_TYPE
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI
from razorpayx_integration.utils import validate_razorpayx_contact_type

# todo : use composite API, If composite APIs working properly fine then no need of this API
# todo: this need to be refactor and optimize


class RazorPayXContact(BaseRazorPayXAPI):
    """
    Handle APIs for RazorPayX Contact.
    :param account_name: RazorPayX account for which this `Contact` is associate.
    ---
    Reference: https://razorpay.com/docs/api/x/contacts
    """

    # * utility attributes
    BASE_PATH = "contacts"

    # * override base setup
    def setup(self, *args, **kwargs):
        pass

    ### APIs ###
    def create(self, **kwargs) -> dict:
        """
        Creates `RazorPayX Contact`.

        :param dict json: Full details of the contact to create.
        :param str name: The name of the contact.
        :param str type: Contact's ERPNext DocType.
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not valid.\n
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
            - If `json` passed in args, then remaining args will be discarded.
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/create
        """
        return self.post(json=self.get_processed_request(kwargs))

    def get_by_id(self, id: str) -> dict:
        """
        Fetch the details of a specific `Contact` by Id.
        :param id: `Id` of contact to fetch (Ex.`cont_hkj012yuGJ`).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-with-id
        """
        return self.get(endpoint=id)

    def get_all(
        self, filters: Optional[dict] = None, count: Optional[int] = None
    ) -> list[dict]:
        """
        Get all `Contacts` associate with given `RazorPayX` account if limit is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of contacts to be retrieved.

        :raises ValueError: If `type` is not valid.\n
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
            - `active` can be int or boolean.
            - `from` and `to` can be str,date,datetime (in YYYY-MM-DD).
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-all
        """
        return super().get_all(filters, count)

    def update(self, id: str, **kwargs):
        """
        Updates `RazorPayX Contact`.

        :param id: Contact Id of whom to update details (Ex.`cont_hkj012yuGJ`).
        :param dict json: Full details of contact to create.
        :param str name: The contact's name.
        :param str type: Contact's ERPNext DocType.
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not valid.\n
        ---
        Example Usage:
        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        response = contact.update(
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
        return self.patch(endpoint=id, json=self.get_processed_request(kwargs))

    def activate(self, id: str) -> dict:
        """
        Activate the contact for the given `Id` if it is deactivated.

        :param id: `Id` of contact to make activate (Ex.`cont_hkj012yuGJ`).
        """
        return self._change_state(id=id, active=True)

    def deactivate(self, id: str) -> dict:
        """
        Deactivate the contact for the given `Id` if it is activated.

        :param id: `Id` of contact to make deactivate (Ex.`cont_hkj012yuGJ`).
        """
        return self._change_state(id=id, active=False)

    ### Bases ###
    def _change_state(self, id: str, active: Union[bool, int]) -> dict:
        """
        Change the state of the `Contact` for the given Id.

        :param id: Id of `Contact` to change state (Ex.`cont_hkj012yuGJ`).
        :param active: Represents the state. (`True`:Active,`False`:Inactive)
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/activate-or-deactivate
        """
        return self.patch(endpoint=id, json={"active": active})

    ### Helpers ###
    def get_processed_request(self, request: dict) -> dict:
        """
        Maps given request data to RazorPayX request data structure.
        """
        json = request.get("json")

        if json and isinstance(json, dict):
            if id := json.get("id"):
                json["reference_id"] = id
                del json["id"]

            if note := json.get("note"):
                json["notes"] = {"notes_key_1": note}
                del json["note"]

        else:
            json = {
                "name": request.get("name"),
                "type": request.get("type"),
                "email": request.get("email"),
                "contact": request.get("contact"),
                "reference_id": request.get("id"),
                "notes": (
                    {"notes_key_1": request.get("note")}
                    if request.get("note")
                    else None
                ),
            }

        self._clean_request_filters(json)
        self.validate_email_and_type_of_contact(json)

        return json

    def validate_email_and_type_of_contact(self, request: dict):
        if email := request.get("email"):
            validate_email_address(email, throw=True)

        if type := request.get("type"):
            # Razorpayx does not support `supplier` type contact
            request["type"] = RAZORPAYX_CONTACT_TYPE[type.upper()].value
            validate_razorpayx_contact_type(request["type"])

    def validate_and_process_request_filters(self, filters: dict):
        self.validate_email_and_type_of_contact(filters)
