from enum import Enum


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
