import re
from datetime import datetime

import frappe
from frappe import _
from frappe.core.page.permission_manager.permission_manager import (
    remove as remove_role_permissions,
)
from frappe.permissions import add_permission, update_permission_property
from frappe.utils import (
    DateTimeLikeObject,
    add_to_date,
    get_datetime,
    get_timestamp,
    getdate,
)

from razorpayx_integration.constants import SECONDS_IN_A_DAY

################# APIs RELATED #################


def get_start_of_day_epoch(date: DateTimeLikeObject = None) -> int:
    """
    Return the Unix timestamp (seconds since Epoch) for the start of the given `date`.\n
    If `date` is None, the current date's start of day timestamp is returned.

    :param date: A date string in "YYYY-MM-DD" format or a (datetime,date) object.
    :return: Unix timestamp for the start of the given date.
    ---
    Example:
    ```
    get_start_of_day_epoch("2024-05-30") ==> 1717007400
    get_start_of_day_epoch(datetime(2024, 5, 30)) ==> 1717007400
    ```
    ---
    Note:
        - Unix timestamp refers to `2024-05-30 12:00:00 AM`
    """
    return int(get_timestamp(date))


def get_end_of_day_epoch(date: DateTimeLikeObject = None) -> int:
    """
    Return the Unix timestamp (seconds since Epoch) for the end of the given `date`.\n
    If `date` is None, the current date's end of day timestamp is returned.

    :param date: A date string in "YYYY-MM-DD" format or a (datetime,date) object.
    :return: Unix timestamp for the end of the given date.
    ---
    Example:
    ```
    get_end_of_day_epoch("2024-05-30") ==> 1717093799
    get_end_of_day_epoch(datetime(2024, 5, 30)) ==> 1717093799
    ```
    ---
    Note:
        - Unix timestamp refers to `2024-05-30 11:59:59 PM`
    """
    return int(get_timestamp(date)) + (SECONDS_IN_A_DAY - 1)


def get_str_datetime_from_epoch(epoch_time: int) -> str:
    """
    Get Local datetime from Epoch Time.\n
    Format: yyyy-mm-dd HH:MM:SS
    """
    return datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")


def yesterday():
    """
    Get the date of yesterday from the current date.
    """
    return add_to_date(getdate(), days=-1)


def rupees_to_paisa(amount: float | int) -> int:
    """
    Convert the given amount in Rupees to Paisa.

    :param amount: The amount in Rupees to be converted to Paisa.

    Example:
    ```
    rupees_to_paisa(100) ==> 10000
    ```
    """
    return int(amount * 100)


def paisa_to_rupees(amount: int) -> int | float:
    """
    Convert the given amount in Paisa to Rupees.

    :param amount: The amount in Paisa to be converted to Rupees.

    Example:
    ```
    paisa_to_rupees(10000) ==> 100
    ```
    """
    return amount / 100


################# HTML RELATED #################
def get_unordered_list(items: list[str]) -> str:
    return "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"


################# WRAPPERS #################
def enqueue_integration_request(**kwargs):
    frappe.enqueue(
        "razorpayx_integration.payment_utils.utils.log_integration_request",
        **kwargs,
    )


def log_integration_request(
    url=None,
    integration_request_service=None,
    request_id=None,
    request_headers=None,
    data=None,
    status=None,
    output=None,
    error=None,
    reference_doctype=None,
    reference_name=None,
    is_remote_request=False,
):
    def get_status():
        if status:
            return status

        return "Failed" if error else "Completed"

    return frappe.get_doc(
        {
            "doctype": "Integration Request",
            "integration_request_service": integration_request_service,
            "request_id": request_id,
            "url": url,
            "request_headers": pretty_json(request_headers),
            "data": pretty_json(data),
            "output": pretty_json(output),
            "error": pretty_json(error),
            "status": get_status(),
            "reference_doctype": reference_doctype,
            "reference_docname": reference_name,
            "is_remote_request": is_remote_request,
        }
    ).insert(ignore_permissions=True)


def pretty_json(obj):
    if not obj:
        return ""

    if isinstance(obj, str):
        return obj

    return frappe.as_json(obj, indent=4)


################# SETUPS #################


### After Install Setup ###
def make_roles_and_permissions(roles: list[dict]):
    """
    Make roles and permissions for the given roles.

    Apply roles to the doctypes with the given permissions.

    :param roles: List of roles with permissions.

    Structure of the `roles` list:
    ```py
    [
        {
            "doctype": "DocType",
            "role_name": "Role Name",
            "permlevels": PERMLEVEL,
            "permissions": ["read", "write", "create", "delete", "submit" ...],
        },
        ...,
    ]
    ```
    """
    create_roles(list({role["role_name"] for role in roles}))
    apply_roles_to_doctype(roles)


def create_roles(role_names: list[str]):
    """
    Create roles with the given names.

    If the role already exists, it will be skipped.

    :param role_names: List of role names to be created.

    Note: `Desk Access` is set to `1` for all the roles.
    """
    for role_name in role_names:
        try:
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            ).save()

        except frappe.DuplicateEntryError:
            pass


def apply_roles_to_doctype(roles: list[dict]):
    """
    Apply roles to the doctypes with the given permissions.

    :param roles: List of roles with permissions.

    Structure of the `roles` list:
    ```py
    [
        {
            "doctype": "DocType",
            "role_name": "Role Name",
            "permlevels": PERMLEVEL | [PERMLEVEL, ...],
            "permissions": ["read", "write", "create", "delete", "submit" ...],
        },
        ...,
    ]
    ```
    """
    for role in roles:
        doctype, role_name, permlevels, permissions = role.values()

        if isinstance(permlevels, int):
            permlevels = [permlevels]

        # Adding role to the doctype
        for permlevel in permlevels:
            add_permission(doctype, role_name, permlevel)

        # Updating permissions (types) for the roles in the doctype
        for permission in permissions:
            for permlevel in permlevels:
                update_permission_property(doctype, role_name, permlevel, permission, 1)


def make_workflows(workflows: list[dict]):
    """
    Create workflows.

    :param workflows: List of workflows

    Note: Duplicate workflows will be skipped.
    """
    for workflow in workflows:
        try:
            doc = frappe.new_doc("Workflow")
            doc.update(workflow)
            doc.save()
        except frappe.DuplicateEntryError:
            pass


def make_workflow_states(states: dict):
    """
    Create workflow states.

    :param states: {state_name: style}
    """
    user = frappe.session.user or "Administrator"

    fields = [
        "name",
        "workflow_state_name",
        "style",
        "creation",
        "modified",
        "owner",
        "modified_by",
    ]

    documents = [
        [state, state, style, get_datetime(), get_datetime(), user, user]
        for state, style in states.items()
    ]

    frappe.db.bulk_insert(
        "Workflow State",
        fields,
        documents,
        ignore_duplicates=True,
    )


def make_workflow_actions(actions: list[str]):
    """
    Create workflow actions.

    :param actions: list of action names
    """
    user = frappe.session.user or "Administrator"

    fields = [
        "name",
        "workflow_action_name",
        "creation",
        "modified",
        "owner",
        "modified_by",
    ]

    documents = [
        [action, action, get_datetime(), get_datetime(), user, user]
        for action in actions
    ]

    frappe.db.bulk_insert(
        "Workflow Action Master",
        fields,
        documents,
        ignore_duplicates=True,
    )


### Before Uninstall Setup ###
def delete_custom_fields(custom_fields: dict):
    """
    Delete custom fields from the given doctypes.

    :param custom_fields: Dictionary of doctypes with fields to be deleted.

    ---
    Structure of the `custom_fields` dictionary:

    ```py
    # first structure
    {
        "DocType1": ["field1", "field2", ...],
        "DocType2": ["field1", "field2", ...],
        ...
    }

    # second structure
    {
        "DocType1": [
            {"fieldname": "field1", ...},
            {"fieldname": "field2", ...},
            ...
        ],
        "DocType2": [
            {"fieldname": "field1", ...},
            {"fieldname": "field2", ...},
            ...
        ],
        ...
    }
    ```

    """
    for doctype, fields in custom_fields.items():
        fieldnames = []

        if isinstance(fields, list) and fields:
            if isinstance(fields[0], str):
                fieldnames = fields
            elif isinstance(fields[0], dict):
                fieldnames = [field["fieldname"] for field in fields]

        if not fieldnames:
            continue

        frappe.db.delete(
            "Custom Field",
            {
                "fieldname": ("in", fieldnames),
                "dt": doctype,
            },
        )

        frappe.clear_cache(doctype=doctype)


def delete_property_setters(property_setters: list[dict]):
    """
    Delete property setters.

    :param property_setters: List of property setters.
    """
    field_map = {
        "doctype": "doc_type",
        "fieldname": "field_name",
    }

    for property_setter in property_setters:
        for key, fieldname in field_map.items():
            if key in property_setter:
                property_setter[fieldname] = property_setter.pop(key)

        frappe.db.delete("Property Setter", property_setter)

        frappe.clear_cache(doctype=property_setter["doc_type"])


def delete_roles_and_permissions(roles: list[dict]):
    """
    Delete roles.

    :param roles: List of roles.

    Structure of the `roles` list:
    ```py
    [
        {
            "doctype": "DocType",
            "role_name": "Role Name",
            "permlevels": PERMLEVEL | [PERMLEVEL, ...],
            "permissions": ["read", "write", "create", "delete", "submit" ...],
        },
        ...,
    ]
    ```
    """
    remove_permissions(roles)
    delete_roles(list({role["role_name"] for role in roles}))


def remove_permissions(roles: list[dict]):
    """
    Remove permissions from the doctypes for the given roles.

    :param roles: List of roles with permissions.

    Structure of the `roles` list:
    ```py
    [
        {
            "doctype": "DocType",
            "role_name": "Role Name",
            "permlevels": PERMLEVEL | [PERMLEVEL, ...],
            "permissions": ["read", "write", "create", "delete", "submit" ...],
        },
        ...,
    ]
    ```
    """
    for role in roles:
        try:
            doctype, role_name, permlevels, permissions = role.values()
            if isinstance(permlevels, int):
                permlevels = [permlevels]

            for permlevel in permlevels:
                remove_role_permissions(doctype, role_name, permlevel)
        except Exception:
            pass


def delete_roles(roles: list[str]):
    """
    Delete roles with the given names.

    :param roles: List of role names to be deleted.
    """
    frappe.db.delete("Role", {"role_name": ("in", roles)})


### String Manipulation ###
def to_hyphenated(text):
    """
    Replace any character that is not alphanumeric with a hyphen, including spaces.

    :param text: The text to be converted.

    ---
    Example:

    ```py
    convert_special_chars_to_hyphen("Hello World!") ==> "Hello-World-"
    ```
    """
    return re.sub(r"[^a-zA-Z0-9]", "-", text)
