from enum import Enum

import frappe


class BaseEnum(Enum):
    """
    ⚠️ Only use when all keys have unique values
    """

    @classmethod
    def has_value(cls, value) -> bool:
        """
        Check if the Enum has a value or not.
        """
        return value in cls._value2member_map_

    @classmethod
    def values(cls) -> list:
        """
        Return a list of all the values.
        """
        return [member.value for member in cls]

    @classmethod
    def names(cls) -> list:
        """
        Return a list of all the names(keys).
        """
        return [member.name for member in cls]

    @classmethod
    def data(cls) -> dict:
        """
        Return a dictionary of all the names(keys) and values.
        """
        return {member.name: member.value for member in cls}

    @classmethod
    def values_as_string(cls, sep: str = "\n") -> str:
        """
        Return the value as a string with the separator.

        :param sep: Separator to join the values.
        """
        return sep.join(cls.values())

    @classmethod
    def names_as_string(cls, sep: str = "\n") -> str:
        """
        Return the names(keys) as a string with the separator.

        :param sep: Separator to join the names.
        """
        return sep.join(cls.names())

    @classmethod
    def values_as_html_list(cls, ordered: bool = False) -> str:
        """
        Return the values as an HTML list.

        :param ordered: Ordered list or not.
        """

        def get_tag():
            return "ol" if ordered else "ul"

        return (
            f"<{get_tag()}>"
            + "".join(f"<li>{value}</li>" for value in cls.values())
            + f"</{get_tag()}>"
        )

    @classmethod
    def scrubbed_values(cls, as_string: bool = False, sep: str = "\n") -> list | str:
        """
        Returns scrubbed values.

        :param as_string: Return as a string.
        :param sep: Separator to join the values.

        Eg. `Not Initiated` -> `not_initiated`
        """
        values = [frappe.scrub(member.value) for member in cls]

        if as_string:
            return sep.join(values)

        return values

    @classmethod
    def title_case_values(cls, as_string: bool = False, sep: str = "\n") -> list | str:
        """
        Returns title case values.

        :param as_string: Return as a string.
        :param sep: Separator to join the values.

        Eg. `not_initiated` -> `Not Initiated`
        """
        values = [member.value.title() for member in cls]

        if as_string:
            return sep.join(values)

        return values

    @classmethod
    def lower_case_values(cls, as_string: bool = False, sep: str = "\n") -> list | str:
        """
        Returns lower case values.

        :param as_string: Return as a string.
        :param sep: Separator to join the values.

        Eg. `Not Initiated` -> `not initiated`
        """
        values = [member.value.lower() for member in cls]

        if as_string:
            return sep.join(values)

        return values

    @classmethod
    def upper_case_values(cls, as_string: bool = False, sep: str = "\n") -> list | str:
        """
        Returns upper case values.

        :param as_string: Return as a string.
        :param sep: Separator to join the values.

        Eg. `Not Initiated` -> `NOT INITIATED`
        """
        values = [member.value.upper() for member in cls]

        if as_string:
            return sep.join(values)

        return values
