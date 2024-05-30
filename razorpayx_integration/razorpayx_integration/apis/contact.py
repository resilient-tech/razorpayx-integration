from typing import Literal

import frappe
from frappe import _

from razorpayx_integration.constant import (
    AUTHORIZED_CONTACT_TYPE,
    RAZORPAYX,
    RAZORPAYX_CONTACT_MAP,
)
from razorpayx_integration.razorpayx_integration.apis.base import BaseRazorPayXAPI


class RazorPayXContact(BaseRazorPayXAPI):
    """
    Handle APIs for RazorPayX Contact.

    :param str account_name: RazorPayX account for which this contact is associate.

    1) Create
    2) Update
    3) Fetch

    Reference: https://razorpay.com/docs/api/x/contacts
    """

    # * utility attributes
    BASE_PATH = "contacts"

    # * override base setup
    def setup(self):
        pass

    # * APIs
    def create(self, name: str, type: Literal["Employee", "Supplier"], **kwargs):
        """
        Creates `RazorPayX Contact`.

        :param str name: The contact's name.
        :param str type: Must be one of ["employee", "supplier"].
        :param str email: Email address of the contact.
        :param str contact: Contact number of the contact.
        :param str id: Reference Id for contact.
        :param str note: Additional note for the contact.

        :raises ValueError: If `type` is not one of ["employee", "supplier"].

        Example Usage:

        ```
        contact = RazorPayXContact("RAZORPAYX_BANK_ACCOUNT")
        response = contact.create(
            "Joe Doe",
            "Employee",
            email="joe123@gmail.com",
            contact="7434870169",
            id="empl-02",
            note="New Employee",
        )
        ```

        Reference: https://razorpay.com/docs/api/x/contacts/create
        """
        if type not in AUTHORIZED_CONTACT_TYPE:
            type_list = (
                "<ul>"
                + "".join(f"<li>{t}</li>" for t in AUTHORIZED_CONTACT_TYPE)
                + "</ul>"
            )
            frappe.throw(
                msg=_(
                    f"Invalid contact type: {type}. Must be one of : <br> {type_list}"
                ),
                title=_(f"Invalid {RAZORPAYX} contact type"),
                exc=ValueError,
            )

        data = {
            "name": name,
            "type": RAZORPAYX_CONTACT_MAP[type],
            "email": kwargs.get("email"),
            "contact": kwargs.get("contact"),
            "reference_id": kwargs.get("id"),
            "notes": (
                {"notes_key_1": kwargs.get("note")} if kwargs.get("note") else None
            ),
        }

        # Remove keys with None values
        data = {key: value for key, value in data.items() if value is not None}

        return self.post(json=data)

    def get_all(self):
        return self.get()
