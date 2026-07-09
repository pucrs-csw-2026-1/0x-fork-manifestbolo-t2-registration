"""Enums for the registration domain."""

from enum import StrEnum


class RegistrationStatus(StrEnum):
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
