import frappe
from frappe import _
from frappe.utils.data import DateTimeLikeObject, get_timestamp

from razorpayx_integration.constant import (
    AUTHORIZED_CONTACT_TYPE,
    AUTHORIZED_FUND_ACCOUNT_TYPE,
    RAZORPAYX,
    RAZORPAYX_SETTING_DOCTYPE,
    SECONDS_IN_A_DAY_MINUS_ONE,
)


def get_razorpayx_account(account_name: str):
    return frappe.get_doc(RAZORPAYX_SETTING_DOCTYPE, account_name)


def validate_razorpayx_contact_type(type: str):
    """
    Check type is in `AUTHORIZED_CONTACT_TYPE` or not.
    If not raises an error.
    """
    if type not in AUTHORIZED_CONTACT_TYPE:
        type_list = (
            "<ul>" + "".join(f"<li>{t}</li>" for t in AUTHORIZED_CONTACT_TYPE) + "</ul>"
        )
        frappe.throw(
            msg=_(f"Invalid contact type: {type}. Must be one of : <br> {type_list}"),
            title=_(f"Invalid {RAZORPAYX} contact type"),
            exc=ValueError,
        )


def validate_razorpayx_bank_account_type(type: str):
    """
    Check type is in `AUTHORIZED_FUND_ACCOUNT_TYPE` or not.
    If not raises an error.
    """
    if type not in AUTHORIZED_FUND_ACCOUNT_TYPE:
        type_list = (
            "<ul>"
            + "".join(f"<li>{t}</li>" for t in AUTHORIZED_FUND_ACCOUNT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_(f"Invalid Account type: {type}. Must be one of : <br> {type_list}"),
            title=_(f"Invalid {RAZORPAYX} Account type"),
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
