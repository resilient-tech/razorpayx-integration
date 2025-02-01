from frappe.utils import validate_email_address

from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorpayXAPI
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    CONTACT_TYPE,
)

# ! IMPORTANT: Currently this API is not maintained.
# TODO: this need to be refactor and optimize
# TODO: Add service details to IR log
# TODO: Add source doctype and docname to IR log


class RazorpayXContact(BaseRazorpayXAPI):
    """
    Handle APIs for RazorpayX Contact.

    :param account_name: RazorpayX account for which this `Contact` is associate.

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
        Creates `RazorpayX Contact`.

        :param dict json: Full details of the contact to create.
        :param str name: [*] The name of the contact.
        :param str type: Contact's ERPNext DocType. (Ex. `Employee`, `Customer`, `Supplier`)
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param dict notes: Additional notes for the contact.

        ---
        Example Usage:
        ```
        contact = RazorpayXContact(RAZORPAYX_BANK_ACCOUNT)

        # Using args
        response = contact.create(
            name="Joe Doe",
            type="Employee",
            email="joe123@gmail.com",
            contact="7434870169",
            id="empl-02",
            notes={
                "source": "ERPNext",
                "demo": True,
            }
        )

        # Using json
        json = {
            "name"="Joe Doe",
            "type"="Employee",
            "email"="joe123@gmail.com",
            "contact"="7434870169",
            "id"="empl-02",
            notes={
                "source": "ERPNext",
                "demo": True,
            }
        }

        response = contact.create(json=json)
        ```
        ---

        Note:
        - If `json` passed in args, then remaining args will be discarded.
        - [*] Required fields.
        ---
        Reference: https://razorpay.com/docs/api/x/contacts/create
        """
        return self.post(json=self.get_mapped_request(kwargs))

    def get_by_id(self, id: str) -> dict:
        """
        Fetch the details of a specific `Contact` by Id.

        :param id: `Id` of contact to fetch (Ex.`cont_hkj012yuGJ`).

        ---
        Reference: https://razorpay.com/docs/api/x/contacts/fetch-with-id
        """
        return self.get(endpoint=id)

    def get_all(
        self, filters: dict | None = None, count: int | None = None
    ) -> list[dict]:
        """
        Get all `Contacts` associate with given `RazorpayX` account if limit is not given.

        :param filters: Result will be filtered as given filters.
        :param count: The number of contacts to be retrieved.

        :raises ValueError: If `type` is not valid.

        ---
        Example Usage:
        ```
        contact = RazorpayXContact(RAZORPAYX_BANK_ACCOUNT)

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
        Updates `RazorpayX Contact`.

        :param id: Contact Id of whom to update details (Ex.`cont_hkj012yuGJ`).
        :param dict json: Full details of contact to create.
        :param str name: The contact's name.
        :param str type: Contact's ERPNext DocType.
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param dict notes: Additional notes for the contact.

        ---
        Example Usage:
        ```
        contact = RazorpayXContact(RAZORPAYX_BANK_ACCOUNT)

        # Using args
        response = contact.update(
            name="Joe Doe",
            type="employee",
            email="joe123@gmail.com",
            contact="7434870169",
            id="empl-02",
            notes = {
                "source": "ERPNext",
                "demo": True,
            }
        )

        # Using json
        json = {
            "name"="Joe Doe",
            "type"="employee",
            "email"="joe123@gmail.com",
            "contact"="7434870169",
            "id"="empl-02",
            "notes"={
                "source": "ERPNext",
                "demo": True,
            }
        }

        response = contact.update(id='cont_hkj012yuGJ',json=json)
        ```

        ---
        Note:
        - If json passed in args, then other args will discarded.

        ---
        Reference: https://razorpay.com/docs/api/x/contacts/update
        """
        return self.patch(endpoint=id, json=self.get_mapped_request(kwargs))

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
    def _change_state(self, id: str, active: bool | int) -> dict:
        """
        Change the state of the `Contact` for the given Id.

        :param id: Id of `Contact` to change state (Ex.`cont_hkj012yuGJ`).
        :param active: Represents the state. (`True`:Active,`False`:Inactive)

        ---
        Reference: https://razorpay.com/docs/api/x/contacts/activate-or-deactivate
        """
        return self.patch(endpoint=id, json={"active": active})

    ### Helpers ###
    def get_mapped_request(self, request: dict) -> dict:
        """
        Maps given request data to RazorpayX request data structure.
        """
        json = request.get("json")

        if json and isinstance(json, dict):
            if id := json.get("id"):
                json["reference_id"] = id
                del json["id"]

        else:
            json = {
                "name": request.get("name"),
                "type": request.get("type"),
                "email": request.get("email"),
                "contact": request.get("contact"),
                "reference_id": request.get("id"),
                "notes": request.get("notes"),
            }

        if json.get("type"):
            json["type"] = self.get_contact_type(json)

        self._clean_request(json)
        self.validate_email(json)

        return json

    def get_contact_type(self, request: dict) -> str | None:
        """
        Get the RazorpayX Contact Type for given ERPNext DocType.

        :param request: Request data.

        ---
        Note:
        - Returns `None` if `type` is not valid.
        - Default Contact Type is `Customer`.
        """
        doctype = request.get("type", "").upper()

        if not doctype:
            return

        if doctype not in CONTACT_TYPE.values():
            return CONTACT_TYPE.CUSTOMER.value

        return CONTACT_TYPE[doctype].value

    def validate_email(self, request: dict):
        if email := request.get("email"):
            validate_email_address(email, throw=True)

    def _validate_and_process_filters(self, filters: dict):
        self.validate_email(filters)
        filters["type"] = self.get_contact_type(filters)
