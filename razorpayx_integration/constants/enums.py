from enum import Enum

import frappe


class BaseEnum(Enum):
    """
    Note: Only use when all keys have unique values
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
    def scrubbed_values(cls) -> list:
        """
        Returns scrubbed values.

        Eg. `Not Initiated` -> `not_initiated`
        """
        return [frappe.scrub(member.value) for member in cls]
