from __future__ import annotations


class RSTBuddyError(Exception):
    """Base exception for all RSTBuddy errors."""


class ConfigurationError(RSTBuddyError):
    """Raised when settings or configuration fails."""


class FileError(RSTBuddyError):
    """Raised when file I/O operations fail."""


class ConversionError(RSTBuddyError):
    """Raised when RST to Markdown conversion fails."""


class NoPandocError(RSTBuddyError):
    """Raised when pandoc is not installed."""
