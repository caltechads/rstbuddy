"""
RST link checking service.

This module provides `RSTLinkChecker`, a focused scanner that walks a given
documentation root to find and validate hyperlinks within reStructuredText
(`.rst`) files. It validates four kinds of links:

- External HTTP(S) links (with concurrent checks and optional robots.txt
  annotation)
- Sphinx `:ref:` roles (against explicit label targets declared as ``.. _label:``)
- Sphinx `:doc:` roles (resolving absolute paths relative to ``doc/source`` and
  relative paths from the current file, with a fallback to ``doc/source``)
- Custom label references in the format `Label`_ (against explicit label definitions
  declared as ``.. Label: URL``)

The scanner intentionally ignores links that appear inside fenced code blocks
and the content of code-like directives (e.g., ``.. code-block::``), while
including admonition directives (e.g., ``.. note::``) that contain prose.
"""

from __future__ import annotations

import csv
import io
import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from ..models import LinkOccurrence, LinkStatus
from ..settings import Settings

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Regex that matches the opening line of a fenced code block (Markdown-style
#: triple backticks) and optionally captures a language identifier.
_FENCE_OPEN_PATTERN = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_+-]+)?\s*$")
#: Regex that matches a closing line for a fenced code block (or a stray
#: triple-backtick line by itself).
_FENCE_LINE_PATTERN = re.compile(r"^\s*```\s*$")


#: Built-in set of directive names whose contents should be treated as code-like
#: and consequently ignored during link scanning. These are conservative defaults
#: and may be extended via settings (``check_rst_links_extra_skip_directives``).
CODE_LIKE_DIRECTIVES_DEFAULT = {
    "code-block",
    "literalinclude",
    "parsed-literal",
}

#: Common admonition directive names. Admonitions are not skipped; links inside
#: these directives are included in the scan because they represent user-facing
#: prose.
ADMONITION_DIRECTIVES = {
    "note",
    "warning",
    "important",
    "versionchanged",
    "tip",
    "caution",
    "attention",
    "hint",
    "danger",
    "error",
}


@dataclass
class LabelDefinition:
    """
    Represents a custom label definition in the format ".. Label: URL".
    """

    #: The label name (e.g., "My Label")
    label: str
    #: The URL associated with the label
    url: str
    #: Absolute path to the source ``.rst`` file containing the definition.
    file_path: Path
    #: 1-based line number where the definition was found.
    line_number: int


class RSTLinkChecker:
    """
    Scan RST files for hyperlinks and validate them.

    - External http(s) links
    - :ref: labels: checked against explicit ``.. _label:`` indexes
    - :doc: targets: resolved relative to a root or file and checked for existence
    - Custom label references: checked against explicit ``.. Label: URL`` definitions
    """

    def __init__(self, root: Path) -> None:
        """
        Initialize a new link checker.

        Args:
            root: Directory to recursively scan for ``.rst`` files.

        """
        self.root = root
        self.settings: Settings = Settings()

        self.code_like_directives = set(CODE_LIKE_DIRECTIVES_DEFAULT)
        if self.settings and getattr(
            self.settings, "check_rst_links_extra_skip_directives", None
        ):
            self.code_like_directives.update(
                set(self.settings.check_rst_links_extra_skip_directives)
            )

        self.skip_domain_substrings = set()
        if self.settings and getattr(
            self.settings, "check_rst_links_skip_domains", None
        ):
            self.skip_domain_substrings.update(
                set(self.settings.check_rst_links_skip_domains)
            )

    def scan_rst_files(self) -> list[Path]:
        """
        Discover ``.rst`` files under the configured root.

        Returns:
            Sorted list of absolute file paths for all discovered ``.rst`` files.

        """
        return sorted(self.root.rglob("*.rst"))

    # ---- Indexing
    def build_label_index(self, files: list[Path]) -> dict[str, Path]:
        """
        Build an index of explicit Sphinx labels.

        The index maps label names (from ``.. _label:``) to the file that
        defines them. Labels discovered inside fenced code blocks are ignored.

        Args:
            files: List of files to scan.

        Returns:
            Mapping from label to the path of the file that declares it.

        """
        label_re = re.compile(r"^\s*\.\.\s+_([A-Za-z0-9\s_.-]+):\s*$")
        labels: dict[str, Path] = {}
        for p in files:
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = text.splitlines()
            in_fence = False
            for line in lines:
                if _FENCE_OPEN_PATTERN.match(line):
                    in_fence = True
                    continue
                if in_fence and _FENCE_LINE_PATTERN.match(line):
                    in_fence = False
                    continue
                if in_fence:
                    continue
                m = label_re.match(line)
                if m:
                    labels[m.group(1)] = p
        return labels

    def build_custom_label_index(self, files: list[Path]) -> dict[str, LabelDefinition]:
        """
        Build an index of custom label definitions in the format ".. Label: URL".

        The index maps label names to their definitions. Labels discovered inside
        fenced code blocks are ignored.

        Args:
            files: List of files to scan.

        Returns:
            Mapping from label to the LabelDefinition object.

        """
        # Regex to match ".. Label: URL" format
        # Allows spaces in label names and captures everything after the colon
        # as the URL
        custom_label_re = re.compile(r"^\s*\.\.\s+([A-Za-z0-9\s_-]+):\s*(.+)$")
        labels: dict[str, LabelDefinition] = {}

        for p in files:
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = text.splitlines()
            in_fence = False
            for idx, line in enumerate(lines, start=1):
                # Fenced code skip - check closing pattern first
                if in_fence and _FENCE_LINE_PATTERN.match(line):
                    in_fence = False
                    # Don't continue here - process this line normally
                elif _FENCE_OPEN_PATTERN.match(line):
                    in_fence = True
                    continue
                elif in_fence:
                    continue

                m = custom_label_re.match(line)
                if m:
                    label = m.group(1).strip()
                    url = m.group(2).strip()
                    labels[label] = LabelDefinition(
                        label=label, url=url, file_path=p, line_number=idx
                    )
        return labels

    # ---- Collection
    def collect_occurrences(  # noqa: PLR0912, PLR0915
        self, p: Path
    ) -> tuple[
        list[LinkOccurrence],
        list[LinkOccurrence],
        list[LinkOccurrence],
        list[LinkOccurrence],
    ]:
        """
        Collect link occurrences in a file.

        This scans the file line-by-line and returns four lists of occurrences:
        external HTTP(S) links, ``:ref:`` roles, ``:doc:`` roles, and custom label
        references. Links found within fenced code blocks are ignored, as are links
        inside code-like directive content. Admonitions are included.

        Args:
            p: Path to the file to scan.

        Returns:
            A tuple of (external_links, ref_roles, doc_roles, custom_labels),
            each a list of ``LinkOccurrence`` items with file, line number, and
            raw link text.

        """
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            return [], [], [], []

        lines = text.splitlines()
        occurrences_http: list[LinkOccurrence] = []
        occurrences_ref: list[LinkOccurrence] = []
        occurrences_doc: list[LinkOccurrence] = []
        occurrences_custom: list[LinkOccurrence] = []

        in_fence = False
        in_directive: str | None = None
        directive_indent = 0

        directive_open_re = re.compile(r"^(\s*)\.\.\s+([A-Za-z0-9_-]+)::")

        for idx, line in enumerate(lines, start=1):
            # Fenced code skip - check closing pattern first
            if in_fence and _FENCE_LINE_PATTERN.match(line):
                in_fence = False
                # Don't continue here - process this line normally
            elif _FENCE_OPEN_PATTERN.match(line):
                in_fence = True
                continue
            elif in_fence:
                continue

            # Directives: open/close tracking
            mdir = directive_open_re.match(line)
            just_opened = False
            if mdir:
                directive_indent = len(mdir.group(1))
                directive_name = mdir.group(2).strip()
                in_directive = directive_name
                just_opened = True

            # NEW: Collect links from directive arguments (do this before skipping)
            if just_opened and in_directive:
                # Extract links from directive arguments
                directive_links = self._extract_directive_links(line, in_directive)
                for link in directive_links:
                    if link.startswith(("http://", "https://")):
                        # External URL - add to HTTP occurrences
                        occurrences_http.append(
                            LinkOccurrence(file_path=p, line_number=idx, link_text=link)
                        )
                    else:
                        # Local file path - add to doc occurrences for validation
                        occurrences_doc.append(
                            LinkOccurrence(file_path=p, line_number=idx, link_text=link)
                        )

            # Determine if we are in a directive content that should be skipped
            skip_due_to_directive = False
            if in_directive:
                # We are inside a directive until indentation drops back to <=
                # directive_indent and line is not blank However, admonitions
                # should NOT be skipped; only code-like directives
                if in_directive in self.code_like_directives:
                    current_indent = len(line) - len(line.lstrip(" "))
                    if just_opened:
                        # Always skip the directive declaration line and remain inside
                        skip_due_to_directive = True
                    else:  # noqa: PLR5501
                        if line.strip() == "":
                            # blank line within directive: still inside and skip
                            skip_due_to_directive = True
                        elif current_indent > directive_indent:
                            # content line of directive: skip
                            skip_due_to_directive = True
                        else:
                            # indentation reduced: directive ended before this line
                            in_directive = None
                else:
                    # For non code-like directives (admonitions), we consider
                    # them visible; only manage end
                    current_indent = len(line) - len(line.lstrip(" "))
                    if (
                        not just_opened
                        and current_indent <= directive_indent
                        and line.strip() != ""
                    ):
                        in_directive = None

            if skip_due_to_directive:
                continue

            # Collect external links (trim trailing punctuation common in prose)
            # Skip if we're on a directive line to avoid duplication
            if not just_opened:
                for m in re.finditer(r"(?<!`)\bhttps?://[^\s`<>]+", line):
                    url = m.group(0).rstrip(".,);:")
                    occurrences_http.append(
                        LinkOccurrence(file_path=p, line_number=idx, link_text=url)
                    )

            # Collect :ref: role occurrences, keep full role text
            for m in re.finditer(r":ref:`([^`]+)`", line):
                full = m.group(0)
                occurrences_ref.append(
                    LinkOccurrence(file_path=p, line_number=idx, link_text=full)
                )

            # Collect :doc: role occurrences
            for m in re.finditer(r":doc:`([^`]+)`", line):
                full = m.group(0)
                occurrences_doc.append(
                    LinkOccurrence(file_path=p, line_number=idx, link_text=full)
                )

            # Collect custom label references in the format `Label`_
            # This regex matches `Label`_ where Label can contain spaces and
            # alphanumeric characters
            for m in re.finditer(r"`([A-Za-z0-9\s_-]+)`_", line):
                full = m.group(0)
                occurrences_custom.append(
                    LinkOccurrence(file_path=p, line_number=idx, link_text=full)
                )

        return occurrences_http, occurrences_ref, occurrences_doc, occurrences_custom

    # ---- Validation helpers
    def _should_skip_domain(self, url: str) -> bool:
        """
        Return True if the given URL should be skipped based on configured
        domain substrings.

        Args:
            url: Absolute URL to evaluate.

        Returns:
            True when any configured skip substring appears within the URL.

        """
        return any(frag and frag in url for frag in self.skip_domain_substrings)

    def _extract_ref_label(self, ref_markup: str) -> str | None:
        """
        Extract the target label from a ``:ref:`` role.

        Supports both ``:ref:`label``` and ``:ref:`Title <label>``` forms.

        Args:
            ref_markup: The full role markup including backticks.

        Returns:
            The label string if parsable, otherwise ``None``.

        """
        # :ref:`label` or :ref:`Title <label>`
        m = re.match(r"^:ref:`\s*([^`<]+?)\s*`$", ref_markup)
        if m:
            return m.group(1).strip()
        m = re.match(r"^:ref:`\s*([^`<>]+?)\s*<\s*([^`<>]+?)\s*>\s*`$", ref_markup)
        if m:
            return m.group(2).strip()
        return None

    def _extract_doc_target(self, doc_markup: str) -> str | None:
        """
        Extract the target path from a ``:doc:`` role.

        Supports both ``:doc:`path``` and ``:doc:`Title <path>``` forms.

        Args:
            doc_markup: The full role markup including backticks.

        Returns:
            The document target (without ``.rst``) if parsable, else ``None``.

        """
        # :doc:`path` or :doc:`Title <path>`
        m = re.match(r"^:doc:`\s*([^`<]+?)\s*`$", doc_markup)
        if m:
            return m.group(1).strip()
        m = re.match(r"^:doc:`\s*([^`<>]+?)\s*<\s*([^`<>]+?)\s*>\s*`$", doc_markup)
        if m:
            return m.group(2).strip()
        return None

    def _extract_custom_label(self, custom_markup: str) -> str | None:
        """
        Extract the target label from a custom label reference.

        Supports the format `Label`_ where Label can contain spaces and
        alphanumeric characters.

        Args:
            custom_markup: The full markup including backticks and underscore.

        Returns:
            The label string if parsable, otherwise ``None``.

        """
        # `Label`_ format - strip whitespace first, then match
        stripped = custom_markup.strip()
        m = re.match(r"^`([A-Za-z0-9\s_-]+)`_$", stripped)
        if m:
            return m.group(1).strip()
        return None

    def _extract_directive_links(self, line: str, directive_name: str) -> list[str]:
        """
        Extract links from directive arguments.

        Args:
            line: The directive line to parse
            directive_name: Name of the directive

        Returns:
            List of extracted links/URLs

        """
        links = []

        # Check if this is one of our target directives
        if directive_name in {
            "literalinclude",
            "include",
            "download",
            "image",
            "figure",
            "thumbnail",
        }:
            # Extract the argument after the directive
            match = re.search(
                r"\.\.\s+" + re.escape(directive_name) + r"::\s+(.+)$", line
            )
            if match:
                arg = match.group(1).strip()
                if arg:  # Only add non-empty arguments
                    links.append(arg)

        return links

    def _resolve_doc_paths(self, source_file: Path, target: str) -> list[Path]:
        """
        Compute candidate filesystem paths for a ``:doc:`` target.

        Resolution rules:
        - Absolute targets (starting with ``/``) are interpreted relative to
          the Sphinx source directory
          (:attr:`~rstbuddy.settings.Settings.documentation_dir`).
        - Relative targets are resolved relative to the current file's
          directory; if not found, a second attempt is made relative to
          :attr:`~rstbuddy.settings.Settings.documentation_dir`.

        Args:
            source_file: The file where the role appears.
            target: The parsed role target, without an extension.

        Returns:
            Candidate absolute paths with ``.rst`` appended, in resolution order.

        """
        doc_source = Path(self.settings.documentation_dir).resolve()
        candidates: list[Path] = []
        if target.startswith("/"):
            rel = target.lstrip("/")
            candidates.append((doc_source / (rel + ".rst")).resolve())
        else:
            rel = target
            candidates.append((source_file.parent / (rel + ".rst")).resolve())
            candidates.append((doc_source / (rel + ".rst")).resolve())
        return candidates

    def _resolve_directive_paths(self, source_file: Path, target: str) -> list[Path]:
        """
        Compute candidate filesystem paths for a directive target.

        Resolution rules:
        - Absolute targets (starting with ``/``) are interpreted relative to
          the Sphinx source directory
          (:attr:`~rstbuddy.settings.Settings.documentation_dir`).
        - Relative targets are resolved relative to the current file's
          directory; if not found, a second attempt is made relative to
          :attr:`~rstbuddy.settings.Settings.documentation_dir`.

        Args:
            source_file: The file where the directive appears.
            target: The directive target (may include file extension).

        Returns:
            Candidate absolute paths, in resolution order.

        """
        doc_source = Path(self.settings.documentation_dir).resolve()
        candidates: list[Path] = []
        if target.startswith("/"):
            rel = target.lstrip("/")
            candidates.append((doc_source / rel).resolve())
        else:
            rel = target
            candidates.append((source_file.parent / rel).resolve())
            candidates.append((doc_source / rel).resolve())
        return candidates

    # ---- Main API
    def check(  # noqa: PLR0912
        self,
        timeout: int = 5,
        max_workers: int = 8,
        check_robots: bool = True,
        user_agent: str = "rstbuddy-linkcheck/1.0",
    ) -> list[LinkOccurrence]:
        """
        Perform link checking for all discovered files.

        Args:
            timeout: Per-link network timeout in seconds for external checks.
            max_workers: Maximum number of concurrent workers for network
                checks.
            check_robots: Whether to consult robots.txt for failed external
                links and annotate results accordingly.
            user_agent: User-Agent string to use for HTTP requests and
                robots.txt.

        Returns:
            A sorted list of broken link occurrences (by file, then line).

        """
        files = self.scan_rst_files()
        label_index = self.build_label_index(files)
        custom_label_index = self.build_custom_label_index(files)

        all_http: list[LinkOccurrence] = []
        all_ref: list[LinkOccurrence] = []
        all_doc: list[LinkOccurrence] = []
        all_custom: list[LinkOccurrence] = []

        for p in files:
            h, r, d, c = self.collect_occurrences(p)
            all_http.extend(h)
            all_ref.extend(r)
            all_doc.extend(d)
            all_custom.extend(c)

        # External link validation (dedup for network requests)
        url_to_occurrences: dict[str, list[LinkOccurrence]] = {}
        for occ in all_http:
            if self._should_skip_domain(occ.link_text):
                continue
            url_to_occurrences.setdefault(occ.link_text, []).append(occ)

        broken_occurrences: list[LinkOccurrence] = []
        robots_by_url: dict[str, bool | None] = {}
        if url_to_occurrences:
            statuses = self._check_links(
                url_to_occurrences.keys(),
                timeout=timeout,
                max_workers=max_workers,
                check_robots=check_robots,
                user_agent=user_agent,
            )
            # Gather broken ones by URL
            for st in statuses:
                robots_by_url[st.url] = getattr(st, "robots_disallowed", None)
                if st.status_code != 200:  # noqa: PLR2004
                    for occ in url_to_occurrences.get(st.url, []):
                        occ.robots_disallowed = robots_by_url.get(st.url)
                        broken_occurrences.append(occ)

        # :ref: occurrences
        for occ in all_ref:
            label = self._extract_ref_label(occ.link_text)
            if not label or label not in label_index:
                broken_occurrences.append(occ)

        # :doc: occurrences and directive paths
        for occ in all_doc:
            # Check if this is a :doc: role or a directive path
            if occ.link_text.startswith(":doc:"):
                # Handle :doc: roles
                target = self._extract_doc_target(occ.link_text)
                if not target:
                    broken_occurrences.append(occ)
                    continue
                candidates = self._resolve_doc_paths(occ.file_path, target)
                if not any(p.exists() for p in candidates):
                    broken_occurrences.append(occ)
            else:
                # Handle directive paths (they're already in the correct format)
                target = occ.link_text
                candidates = self._resolve_directive_paths(occ.file_path, target)
                if not any(p.exists() for p in candidates):
                    broken_occurrences.append(occ)

        # Custom label occurrences
        for occ in all_custom:
            label = self._extract_custom_label(occ.link_text)
            if not label or label not in custom_label_index:
                broken_occurrences.append(occ)

        # Sort deterministically: by file then line
        broken_occurrences.sort(key=lambda o: (str(o.file_path), o.line_number))
        return broken_occurrences

    # ---- Rendering helpers
    @staticmethod
    def relative_to_doc_source(path: Path) -> str:
        """
        Convert an absolute path to a path relative to ``doc/source`` for
        display in CLI output.

        If the file is outside of ``doc/source``, a relative path from
        ``doc/source`` to the file is computed.

        Args:
            path: Absolute file path.

        Returns:
            Relative string path suitable for display.

        """
        settings = Settings()
        doc_source = Path(settings.documentation_dir).resolve()
        try:
            return str(path.resolve().relative_to(doc_source))
        except ValueError:
            # If not under doc/source, compute a relative path from doc/source
            # to the file
            return os.path.relpath(path.resolve(), doc_source)

    def render_table(self, broken: list[LinkOccurrence]) -> str:
        """
        Render a simple pipe-delimited table representation of broken links.

        Note: The CLI typically uses Rich to present tabular data; this method
        exists primarily for parity with CSV/JSON renderers and testing.

        Args:
            broken: List of broken link occurrences.

        Returns:
            Table text with header and one row per occurrence.

        """
        lines = ["File | Line | Link"]
        for occ in broken:
            rel = self.relative_to_doc_source(occ.file_path)
            lines.append(f"{rel} | {occ.line_number} | {occ.link_text}")
        return "\n".join(lines)

    def render_csv(self, broken: list[LinkOccurrence]) -> str:
        """
        Render broken link occurrences as CSV.

        Columns: ``file``, ``line``, ``link``, ``robots_disallowed``.

        Args:
            broken: List of broken link occurrences.

        Returns:
            CSV-formatted string including a header row.

        """
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            ["file", "line", "link", "robots_disallowed"]
        )  # robots flag only applies to external links
        for occ in broken:
            rel = self.relative_to_doc_source(occ.file_path)
            robots_flag = (
                "true"
                if isinstance(occ.robots_disallowed, bool) and occ.robots_disallowed
                else ""
            )
            writer.writerow([rel, occ.line_number, occ.link_text, robots_flag])
        return buf.getvalue()

    def render_json(self, broken: list[LinkOccurrence]) -> dict:
        """
        Render broken link occurrences as a JSON-serializable mapping.

        The returned structure is a dict keyed by file path (relative to
        ``doc/source``), where each value is a list of entries with keys
        ``line``, ``link``, and ``robots_disallowed``.

        Args:
            broken: List of broken link occurrences.

        Returns:
            JSON-serializable dict.

        """
        out: dict[str, list[dict]] = {}
        for occ in broken:
            rel = self.relative_to_doc_source(occ.file_path)
            out.setdefault(rel, []).append(
                {
                    "line": occ.line_number,
                    "link": occ.link_text,
                    "robots_disallowed": bool(occ.robots_disallowed)
                    if occ.robots_disallowed is not None
                    else None,
                }
            )
        return out

    def _check_links(
        self,
        links: Iterable[str],
        timeout: int = 5,
        max_workers: int = 8,
        check_robots: bool = True,
        user_agent: str = "rstbuddy-linkcheck/1.0",
    ) -> list[LinkStatus]:
        """
        Validate external links concurrently.

        Args:
            links: URLs to validate

        Keyword Args:
            timeout: Per-request timeout (seconds)
            max_workers: Maximum worker threads
            check_robots: Whether to honor robots.txt
            user_agent: User-Agent to use for HTTP validation and robots.txt

        Returns:
            A list of per-link results

        """

        def worker(url: str) -> LinkStatus:
            try:
                return self._check_single_link(
                    url, timeout, check_robots=check_robots, user_agent=user_agent
                )
            except Exception as e:  # noqa: BLE001
                return LinkStatus(url=url, error=str(e))

        results: list[LinkStatus] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            fut_to_url = {ex.submit(worker, u): u for u in links}
            results.extend(fut.result() for fut in as_completed(fut_to_url))
        return results

    def _check_single_link(
        self,
        url: str,
        timeout: int,
        *,
        check_robots: bool = True,
        user_agent: str = "rstbuddy-linkcheck/1.0",
    ) -> LinkStatus:
        """
        Validate a single http(s) link with HEAD then GET fallback.

        Args:
            url: The target URL
            timeout: Per-request timeout (seconds)

        Keyword Args:
            check_robots: Whether to honor robots.txt
            user_agent: User-Agent to use for HTTP validation and robots.txt

        Returns:
            The link status including final URL and status code

        """
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        def do_request(method: str, target: str) -> tuple[int, str]:
            """
            Do a request with the given method and target URL.

            Args:
                method: The HTTP method to use
                target: The target URL

            Returns:
                A tuple of the status code and the final URL

            """
            if not target.startswith(("http://", "https://")):
                return 400, "Invalid URL"

            # Do a quick DNS lookup first to fail fast for invalid domains
            try:
                parsed_url = urlparse(target)
                socket.gethostbyname(parsed_url.netloc)
            except socket.gaierror:
                # DNS lookup failed - domain doesn't exist
                return 404, f"DNS lookup failed for {parsed_url.netloc}"

            req = Request(target, method=method, headers=headers)  # noqa: S310
            try:
                with urlopen(req, timeout=timeout) as resp:  # noqa: S310
                    return resp.getcode(), resp.geturl()
            except HTTPError as e:
                return e.code, target
            except (URLError, socket.timeout):
                raise

        status, final_url = None, url
        try:
            status, final_url = do_request("HEAD", url)
        except socket.timeout:
            return LinkStatus(
                url=url, final_url=None, status_code=408, error="Socket Timeout"
            )
        except (HTTPError, URLError):
            # Fallback to GET once
            try:
                status, final_url = do_request("GET", url)
            except (HTTPError, URLError) as e:
                st = LinkStatus(
                    url=url, final_url=final_url, status_code=None, error=str(e)
                )
                if check_robots:
                    st.robots_disallowed = self._is_disallowed_by_robots(
                        url, user_agent
                    )
                return st

        if status != 200:  # noqa: PLR2004
            st = LinkStatus(
                url=url, final_url=final_url, status_code=status, error=None
            )
            if check_robots:
                st.robots_disallowed = self._is_disallowed_by_robots(url, user_agent)
            return st
        return LinkStatus(
            url=url,
            final_url=final_url,
            status_code=status,
            error=None,
        )

    def _is_disallowed_by_robots(self, url: str, user_agent: str) -> bool:
        """
        Check if a URL is disallowed by robots.txt.

        Args:
            url: The target URL
            user_agent: User-Agent to use for HTTP validation and robots.txt

        Returns:
            True if the URL is disallowed by robots.txt

        """
        try:
            parsed = urlparse(url)
            robots_url = urlunparse(
                (parsed.scheme, parsed.netloc, "/robots.txt", "", "", "")
            )
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            # robotparser has no native timeout; we rely on default opener settings
            rp.read()
            return not rp.can_fetch(user_agent, url)
        except (HTTPError, URLError):
            return False
