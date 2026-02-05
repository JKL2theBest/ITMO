import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VERIFIED_AUTHOR = "verified_author"
    USER = "user"
