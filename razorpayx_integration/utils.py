import json
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import DateTimeLikeObject, add_to_date, get_timestamp, getdate

from razorpayx_integration.razorpayx_integration.constants import (
    RAZORPAYX,
    RAZORPAYX_SETTING_DOCTYPE,
    SECONDS_IN_A_DAY_MINUS_ONE,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_CONTACT_TYPE,
    RAZORPAYX_FUND_ACCOUNT_TYPE,
    RAZORPAYX_PAYOUT_MODE,
    RAZORPAYX_PAYOUT_STATUS,
)


@frappe.whitelist()
def get_associate_razorpayx_account(
    paid_from_account: str, fieldname: list | str | None = None
) -> dict | None:
    frappe.has_permission(RAZORPAYX_SETTING_DOCTYPE)

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
        RAZORPAYX_SETTING_DOCTYPE,
        {"bank_account": bank_account},
        fieldname,
        as_dict=True,
        debug=True,
    )


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_SETTING_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )


def validate_razorpayx_contact_type(type: str):
    """
    :raises ValueError: If the type is not valid.
    """
    if not RAZORPAYX_CONTACT_TYPE.has_value(type):
        type_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_CONTACT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid contact type: {0}. <br> Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Contact Type").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_fund_account_type(type: str):
    """
    :raises ValueError: If the type is not valid.
    """
    if not RAZORPAYX_FUND_ACCOUNT_TYPE.has_value(type):
        type_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_FUND_ACCOUNT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Account type: {0}. <br> Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Fund Account type").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_payout_mode(mode: str):
    """
    :raises ValueError: If the mode is not valid.
    """
    if not RAZORPAYX_PAYOUT_MODE.has_value(mode):
        mode_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_PAYOUT_MODE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Payout mode: {0}.<br> Must be one of : <br> {1}").format(
                mode, mode_list
            ),
            title=_("Invalid {0} Payout mode").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_payout_status(status: str):
    """
    :raises ValueError: If the status is not valid.
    """
    if not RAZORPAYX_PAYOUT_STATUS.has_value(status):
        status_list = (
            "<ul>"
            + "".join(f"<li>{t.value}</li>" for t in RAZORPAYX_PAYOUT_STATUS)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Payout status: {0}.<br> Must be one of : <br> {1}").format(
                status, status_list
            ),
            title=_("Invalid {0} Payout status").format(RAZORPAYX),
            exc=ValueError,
        )


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
    return int(get_timestamp(date)) + SECONDS_IN_A_DAY_MINUS_ONE


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
    return amount * 100


def paisa_to_rupees(amount: int) -> int:
    """
    Convert the given amount in Paisa to Rupees.

    :param amount: The amount in Paisa to be converted to Rupees.

    Example:
    ```
    paisa_to_rupees(10000) ==> 100
    ```
    """
    return amount / 100
