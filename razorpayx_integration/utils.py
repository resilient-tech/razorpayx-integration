from datetime import datetime
from typing import Union

import frappe
from frappe import _
from frappe.utils import DateTimeLikeObject, add_to_date, get_timestamp, getdate

from razorpayx_integration.constant import (
    AUTHORIZED_CONTACT_TYPE,
    AUTHORIZED_FUND_ACCOUNT_TYPE,
    RAZORPAYX,
    RAZORPAYX_SETTING_DOCTYPE,
    SECONDS_IN_A_DAY_MINUS_ONE,
)


# todo: check account is enable or not and API credentials are authorized or not!
def get_razorpayx_account(account_name: str):
    return frappe.get_doc(RAZORPAYX_SETTING_DOCTYPE, account_name)


def get_enabled_razorpayx_accounts() -> list[str]:
    return frappe.get_all(
        RAZORPAYX_SETTING_DOCTYPE,
        filters={"disabled": 0},
        pluck="name",
    )


# todo: can use Literal?
def validate_razorpayx_contact_type(type: str):
    """
    Check if the given type is in the list of authorized contact types.\n

    :param type: The type of contact to be validated.
    :raises ValueError: If the given type is not in the authorized contact types list.
    """
    if type not in AUTHORIZED_CONTACT_TYPE:
        type_list = (
            "<ul>" + "".join(f"<li>{t}</li>" for t in AUTHORIZED_CONTACT_TYPE) + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid contact type: {0}. Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Contact Type").format(RAZORPAYX),
            exc=ValueError,
        )


def validate_razorpayx_fund_account_type(type: str):
    """
    Check if the given type is in the list of authorized fund account types.\n

    :param type: The type of fund account to be validated.
    :raises ValueError: If the given type is not in the authorized fund account types list.
    """
    if type not in AUTHORIZED_FUND_ACCOUNT_TYPE:
        type_list = (
            "<ul>"
            + "".join(f"<li>{t}</li>" for t in AUTHORIZED_FUND_ACCOUNT_TYPE)
            + "</ul>"
        )
        frappe.throw(
            msg=_("Invalid Account type: {0}. Must be one of : <br> {1}").format(
                type, type_list
            ),
            title=_("Invalid {0} Fund Account type").format(RAZORPAYX),
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


def rupees_to_paisa(amount: Union[float, int]) -> int:
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
