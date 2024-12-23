import json

import frappe
from frappe import _

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE


@frappe.whitelist()
def get_associate_razorpayx_account(
    paid_from_account: str, fieldname: list | str | None = None
) -> dict | None:
    frappe.has_permission(RAZORPAYX_INTEGRATION_DOCTYPE)

    if not fieldname:
        fieldname = "name"
    elif isinstance(fieldname, str):
        fieldname = json.loads(fieldname)

    bank_account = frappe.db.get_value(
        "Bank Account", {"account": paid_from_account}, "name"
    )

    if not bank_account:
        return

    return frappe.db.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"bank_account": bank_account},
        fieldname,
        as_dict=True,
    )


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )


def enqueue_razorpayx_integration_request(**kwargs):
    frappe.enqueue(
        "razorpayx_integration.razorpayx_integration.utils.log_razorpayx_integration_request",
        **kwargs,
    )


def log_razorpayx_integration_request(
    url=None,
    integration_request_service=None,
    request_id=None,
    request_headers=None,
    data=None,
    output=None,
    error=None,
    reference_doctype=None,
    reference_name=None,
    is_remote_request=False,
):
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
            "status": "Failed" if error else "Completed",
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
