from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class LinkStatus:
    """
    Result of validating a single HTTP(S) link.

    The cleaner follows redirects and records both the original and final URL,
    along with the observed status code if available.
    """

    #: The original URL as found in the RST content
    url: str
    #: The final URL after redirects (if any)
    final_url: str | None = None
    #: The final HTTP status code, if a response was obtained
    status_code: int | None = None
    #: Any transport or protocol error description
    error: str | None = None
    #: Whether access appears disallowed by robots.txt for our user agent
    robots_disallowed: bool | None = None


@dataclass
class LinkOccurrence:
    """
    Represents a single link occurrence found in a file.
    """

    #: Absolute path to the source ``.rst`` file containing the link.
    file_path: Path
    #: 1-based line number where the link was found.
    line_number: int
    #: The exact hyperlink text as it appears in the file. For
    #: external links this is the URL; for Sphinx roles it is the full role
    #: markup (e.g., ``:ref:`label`` or ``:doc:`Title <path>``).
    link_text: str
    #: Optional flag propagated for external links indicating
    #: that robots.txt appears to disallow access for the configured
    #: User-Agent. ``None`` when not applicable or unknown.
    robots_disallowed: bool | None = None
