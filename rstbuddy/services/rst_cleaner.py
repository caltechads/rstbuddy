from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from ..models import CleanReport
from ..settings import Settings

if TYPE_CHECKING:
    from pathlib import Path

#: Mapping from Markdown heading level to RST underline character.
_HEADING_UNDERLINES = {1: "=", 2: "-", 3: "^"}


def _heading_char_for_level(level: int) -> str:
    """
    Resolve the RST underline character for a given Markdown heading level.

    Args:
        level: Markdown heading depth (number of ``#`` characters)

    Returns:
        The RST underline character. Levels 1, 2, 3 map to ``=``, ``-``, ``^``
        respectively. Levels greater than 3 map to ``~``.

    """
    if level in _HEADING_UNDERLINES:
        return _HEADING_UNDERLINES[level]
    return "~"


#: Supported bullet prefixes treated as list items.
_LIST_BULLETS = ("- ", "* ", "+ ")
#: Regex for detecting numbered list markers (1., a), i), #., etc.).
_LIST_NUM_PATTERN = re.compile(
    r"^(?:\s*)(?:\d+\.|#\.|[a-zA-Z]\)|[ivxlcdmIVXLCDM]+\))\s+"
)

#: Regex for a fenced code block opening line, optionally with a language.
_FENCE_OPEN_PATTERN = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_+-]+)?\s*$")
#: Regex for a fenced code block closing (or any lone fence) line.
_FENCE_LINE_PATTERN = re.compile(r"^\s*```\s*$")

#: Regex to find single-backtick inline code spans not already double-backticked.
_INLINE_CODE_PATTERN = re.compile(r"(?<!`)`([^`]+)`(?!`)")


@dataclass
class _FenceState:
    """
    Internal state while converting a fenced code block.

    Tracks the current fence context, collected lines, and destination index in
    the output buffer so we can recover gracefully if a closing fence is
    missing.
    """

    #: Whether we are currently inside a fenced code block
    in_fence: bool = False
    #: The detected code language (defaults to ``text``)
    lang: str = "text"
    #: Collected content lines inside the fence (unindented)
    content: list[str] = field(default_factory=list)
    #: Index in the output buffer where the fence began
    start_index: int = -1


class RSTCleaner:
    """
    Single-file RST cleaner applying pragmatic, conservative fixes.

    The cleaning pipeline converts fenced code blocks first, then transforms
    Markdown headings to RST, normalizes RST heading rules, fixes inline code
    spans, removes stray fences, ensures list spacing, and finally performs
    optional link validation.
    """

    def __init__(self) -> None:
        # Load settings for optional protections
        self._settings: Settings | None = Settings()

        # Precompile any extra protected regexes from settings
        self._extra_protected_regexes: list[re.Pattern[str]] = []
        if self._settings and getattr(
            self._settings, "clean_rst_extra_protected_regexes", None
        ):
            for pattern in self._settings.clean_rst_extra_protected_regexes:
                try:
                    self._extra_protected_regexes.append(re.compile(pattern))
                except re.error:  # noqa: PERF203
                    # Ignore invalid patterns to keep cleaner resilient
                    continue

    def clean_file(
        self,
        path: Path,
        dry_run: bool = False,
    ) -> CleanReport:
        """
        Clean a single RST file on disk.

        Args:
            path: Path to the RST file

        Keyword Args:
            dry_run: If True, do not write changes or create backups

        Returns:
            A report with counters and link validation results

        """
        text = path.read_text(encoding="utf-8")
        cleaned_text, report = self.clean_text(text)

        if not dry_run:
            # backup with timestamp in local timezone
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # noqa: DTZ005
            backup_path = path.with_suffix(path.suffix + f".{timestamp}.bak")
            backup_path.write_text(text, encoding="utf-8")
            path.write_text(cleaned_text, encoding="utf-8")

        return report

    def clean_text(self, text: str) -> tuple[str, CleanReport]:
        """
        Clean RST content in-memory and return the updated text and report.

        Args:
            text: Original RST content

        Keyword Args:
            check_links: If True, validate external HTTP(S) links
            timeout: Per-request timeout (seconds) for link validation
            max_workers: Maximum worker threads for link validation

        Returns:
            Tuple of (cleaned_text, report)

        """
        lines = text.splitlines()
        report = CleanReport()

        # Convert code fences first to avoid misinterpreting fence lines as headings
        lines, code_blocks_converted = self._convert_markdown_code_blocks(lines)
        report.code_blocks_converted += code_blocks_converted

        # Then handle markdown headings to RST
        lines, count_md_headings = self._convert_markdown_headings(lines)
        report.md_headings_converted += count_md_headings

        # Normalize existing RST headings
        lines, count_headings_fixed = self._normalize_rst_headings(lines)
        report.headings_fixed += count_headings_fixed

        # Convert inline code spans
        lines, inline_code_fixed = self._convert_inline_code_spans(lines)
        report.inline_code_fixed += inline_code_fixed

        # Remove stray fences
        lines, stray_fences_removed = self._remove_stray_fences(lines)
        report.stray_fences_removed += stray_fences_removed

        # Ensure blank line after lists
        lines, lists_spaced = self._ensure_blank_line_after_lists(lines)
        report.lists_spaced += lists_spaced

        # Ensure a blank line exists between adjacent code-block directives
        lines = self._ensure_blank_line_after_code_blocks(lines)

        cleaned_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

        return cleaned_text, report

    # --- Transformations ---
    def _convert_markdown_headings(self, lines: list[str]) -> tuple[list[str], int]:
        """
        Convert Markdown ATX headings to RST headings.

        Converts ``#``, ``##``, ``###`` to RST headings with underline
        characters ``=``, ``-``, ``^`` respectively, and deeper levels to ``~``.
        Ensures a blank line before and after headings when needed.

        Args:
            lines: Input lines

        Returns:
            Updated lines and the number of headings converted

        """
        out: list[str] = []
        converted = 0
        i = 0
        protected = self._compute_protected_mask(lines)
        while i < len(lines):
            # Skip any transformation inside protected regions
            if protected[i]:
                out.append(lines[i])
                i += 1
                continue
            line = lines[i]
            m = re.match(r"^(\s*)(#{1,12})\s*(.+?)\s*#*\s*$", line)
            if m and not line.lstrip().startswith("#."):
                indent, hashes, title = m.groups()
                level = len(hashes)
                underline_char = _heading_char_for_level(level)
                underline = underline_char * len(title)
                # ensure one blank line before
                if out and out[-1].strip() != "":
                    out.append("")
                out.append(f"{indent}{title}")
                out.append(f"{indent}{underline}")
                # ensure one blank line after
                if i + 1 < len(lines) and lines[i + 1].strip() != "":
                    # Do not add a blank if the next line is a summary directive
                    if not lines[i + 1].lstrip().startswith(".. summary::"):
                        out.append("")
                converted += 1
                i += 1
                continue
            out.append(line)
            i += 1
        return out, converted

    def _normalize_rst_headings(self, lines: list[str]) -> tuple[list[str], int]:  # noqa: PLR0912
        """
        Ensure RST heading rules exactly match the title length.

        Supports title+underline and overline+title+underline forms. Adds a
        blank line after the heading if it is immediately followed by content.

        Args:
            lines: Input lines

        Returns:
            Updated lines and the number of headings fixed

        """
        out: list[str] = []
        fixed = 0
        i = 0
        protected = self._compute_protected_mask(lines)
        while i < len(lines):
            # Look for overline+title+underline or title+underline
            if i + 1 < len(lines):
                # title+underline
                title = lines[i]
                underline = lines[i + 1]
                if (
                    not protected[i]
                    and not protected[i + 1]
                    and title.strip()
                    and self._is_underline(underline)
                ):
                    ul_char = underline.strip()[0]
                    desired = ul_char * len(title.strip())
                    if underline.strip() != desired:
                        out.append(title)
                        out.append(desired)
                        fixed += 1
                        i += 2
                        # ensure one blank after heading
                        if i < len(lines) and lines[i].strip() != "":
                            # Do not add a blank if the next line is a summary directive
                            if not lines[i].lstrip().startswith(".. summary::"):
                                out.append("")
                        continue
                # overline+title+underline
                if i + 2 < len(lines):
                    overline = lines[i]
                    title = lines[i + 1]
                    underline = lines[i + 2]
                    if (
                        not protected[i]
                        and not protected[i + 1]
                        and not protected[i + 2]
                        and self._is_underline(overline)
                        and title.strip()
                        and self._is_underline(underline)
                        and overline.strip()[0] == underline.strip()[0]
                    ):
                        char = underline.strip()[0]
                        desired = char * len(title.strip())
                        changed = False
                        if overline.strip() != desired:
                            overline = desired
                            changed = True
                        if underline.strip() != desired:
                            underline = desired
                            changed = True
                        if changed:
                            out.append(overline)
                            out.append(title)
                            out.append(underline)
                            fixed += 1
                            i += 3
                            if i < len(lines) and lines[i].strip() != "":
                                if not lines[i].lstrip().startswith(".. summary::"):
                                    out.append("")
                            continue
            out.append(lines[i])
            i += 1
        return out, fixed

    def _is_underline(self, line: str) -> bool:
        """
        Determine whether a line is an RST heading rule.

        The check is conservative and excludes backticks to avoid picking up
        Markdown fences as heading rules.

        Args:
            line: Line to evaluate

        Returns:
            True if the line appears to be a heading rule

        """
        s = line.strip()
        # Do not treat an empty Sphinx comment as a heading rule
        if s == "..":
            return False
        # Exclude backticks to avoid confusing markdown fences ``` as headings
        return bool(s) and len(set(s)) == 1 and s[0] in "=-^~'\"+*#<>:_" and s[0] != "."

    def _convert_markdown_code_blocks(self, lines: list[str]) -> tuple[list[str], int]:  # noqa: PLR0912
        """
        Convert fenced Markdown code blocks to RST code-block directives.

        Args:
            lines: Input lines

        Returns:
            Updated lines and number of code blocks converted

        """
        out: list[str] = []
        i = 0
        converted = 0
        state = _FenceState(in_fence=False, lang="text", content=[], start_index=-1)
        while i < len(lines):
            line = lines[i]
            if not state.in_fence:
                m = _FENCE_OPEN_PATTERN.match(line)
                if m:
                    state.in_fence = True
                    state.lang = m.group("lang") or "text"
                    state.content = []
                    state.start_index = len(out)
                    i += 1
                    continue
                out.append(line)
                i += 1
            # inside fence
            elif _FENCE_LINE_PATTERN.match(line):
                # close block
                # emit directive
                out.append(f".. code-block:: {state.lang}")
                out.append("")
                # normalize indent
                content = state.content
                # strip leading/trailing empty lines inside code block for cleanliness
                while content and content[0].strip() == "":
                    content.pop(0)
                while content and content[-1].strip() == "":
                    content.pop()
                min_indent = None
                for c in content:
                    if c.strip() == "":
                        continue
                    leading = len(c) - len(c.lstrip(" "))
                    if min_indent is None or leading < min_indent:
                        min_indent = leading
                if min_indent is None:
                    min_indent = 0
                for c in content:
                    stripped = (
                        c[min_indent:] if min_indent and len(c) >= min_indent else c
                    )
                    out.append("    " + stripped)
                converted += 1
                # reset state
                state = _FenceState(
                    in_fence=False, lang="text", content=[], start_index=-1
                )
                i += 1
            else:
                state.content.append(line)
                i += 1
        # if file ended while in fence, treat as stray fences and just emit
        # original content back
        if state.in_fence:
            # push back the original opening fence and its content to out
            out.insert(
                state.start_index,
                f"```{state.lang if state.lang != 'text' else ''}".rstrip(),
            )
            out.extend(state.content)
        return out, converted

    def _convert_inline_code_spans(self, lines: list[str]) -> tuple[list[str], int]:
        """
        Convert Markdown single-backtick spans to RST inline literals.

        A conservative heuristic is used to avoid converting interpreted text or
        links.

        Args:
            lines: Input lines

        Returns:
            Updated lines and number of inline spans converted

        """
        converted = 0

        def looks_like_code(span: str) -> bool:
            return any(ch in span for ch in "_./\\[]()<>:=-")

        # Precompute protected mask for this pass
        protected = self._compute_protected_mask(lines)

        out: list[str] = []
        for idx, line in enumerate(lines):
            if protected[idx]:
                out.append(line)
                continue

            def repl(m: re.Match[str]) -> str:
                start, end = m.start(), m.end()
                content = m.group(1)

                # Skip Sphinx roles like :doc:`target` or :ref:`label`
                before = line[:start]  # noqa: B023
                if re.search(r":[A-Za-z0-9_]+:\s*$", before):
                    return m.group(0)

                # Skip hyperlink references: `text`_ or `text`__
                after = line[end:]  # noqa: B023
                if after.startswith(("__", "_")):
                    return m.group(0)

                # Skip inline links: `text <url>`_
                if re.search(r"<[^>]+>", content):
                    return m.group(0)

                if looks_like_code(content):
                    nonlocal converted
                    converted += 1
                    return f"``{content}``"
                return m.group(0)

            new_line = _INLINE_CODE_PATTERN.sub(repl, line)
            out.append(new_line)
        return out, converted

    def _remove_stray_fences(self, lines: list[str]) -> tuple[list[str], int]:
        """
        Remove lines that consist solely of triple backticks.

        Args:
            lines: Input lines

        Returns:
            Updated lines and number of fences removed

        """
        removed = 0
        out: list[str] = []
        protected = self._compute_protected_mask(lines)
        for idx, line in enumerate(lines):
            if protected[idx]:
                out.append(line)
                continue
            if _FENCE_LINE_PATTERN.match(line):
                removed += 1
                continue
            out.append(line)
        return out, removed

    def _ensure_blank_line_after_lists(self, lines: list[str]) -> tuple[list[str], int]:
        """
        Ensure there is exactly one blank line following a list block.
        Also ensures sublists have blank lines before and after them.

        The detection is conservative and considers continuation lines and
        indentation. Sublists are detected by indentation of 2-4 spaces.

        Args:
            lines: Input lines

        Returns:
            Updated lines and number of blank lines inserted

        """
        out: list[str] = []
        inserted = 0
        i = 0
        while i < len(lines):
            out.append(lines[i])
            # detect end of a list block
            if self._is_list_item_line(lines[i]):
                j = i + 1
                # walk through list items and their sub-items/continuations
                while j < len(lines) and (
                    self._is_list_item_line(lines[j]) or lines[j].startswith(" ")
                ):
                    out.append(lines[j])
                    j += 1
                # now j is first non-list line
                if j < len(lines) and lines[j].strip() != "":
                    # Do not insert a blank line if the next line is a summary directive
                    next_line = lines[j].lstrip()
                    if not next_line.startswith(".. summary::"):
                        out.append("")
                        inserted += 1
                i = j
                continue
            i += 1

        # Now process the output to handle sublist blank lines
        final_out: list[str] = []
        i = 0
        while i < len(out):
            line = out[i]
            final_out.append(line)

            # Check if this line starts a sublist (indented list item)
            if self._is_list_item_line(line) and line.startswith(" "):
                # Check if we need a blank line before the sublist
                if len(final_out) > 1 and final_out[-2].strip() != "":
                    # Insert blank line before sublist
                    final_out.insert(-1, "")
                    inserted += 1

                # Find the end of the sublist
                j = i + 1
                while j < len(out) and (
                    self._is_list_item_line(out[j]) and out[j].startswith(" ")
                ):
                    final_out.append(out[j])
                    j += 1

                # Check if we need a blank line after the sublist
                if j < len(out) and out[j].strip() != "":
                    # Insert blank line after sublist
                    final_out.append("")
                    inserted += 1

                i = j
                continue
            i += 1

        return final_out, inserted

    def _is_list_item_line(self, line: str) -> bool:
        """
        Return True if a line appears to start a list item.

        Args:
            line: Line to evaluate

        Returns:
            True if the line appears to start a list item

        """
        s = line.lstrip()
        return s.startswith(_LIST_BULLETS) or bool(_LIST_NUM_PATTERN.match(s))

    # --- Links ---
    def _collect_links(self, lines: list[str]) -> list[str]:
        """
        Collect distinct http(s) URLs outside code blocks and inline code.

        Args:
            lines: Input lines

        Returns:
            Ordered de-duplicated list of URLs found

        """
        links: list[str] = []
        in_code_fence = False
        # Also skip any links that appear inside directive content
        protected = self._compute_protected_mask(lines)
        for idx, line in enumerate(lines):
            if _FENCE_OPEN_PATTERN.match(line):
                in_code_fence = True
                continue
            if in_code_fence and _FENCE_LINE_PATTERN.match(line):
                in_code_fence = False
                continue
            if protected[idx]:
                continue
            # find http(s) URLs; avoid ones inside backticks
            for m in re.finditer(r"(?<!`)\bhttps?://[^\s`<>]+", line):
                links.append(m.group(0).rstrip(".,);:"))  # noqa: PERF401
        # de-duplicate preserving order
        seen = set()
        uniq: list[str] = []
        for u in links:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq

    # --- Helpers ---
    def _is_directive_line(self, line: str) -> tuple[bool, int]:
        """
        Return (is_directive, indent) for a potential directive line.

        A directive is matched by ".. name::" at any indentation.

        Args:
            line: Line to evaluate

        Returns:
            A tuple of (is_directive, indent)

        """
        m = re.match(r"^(\s*)\.\.\s+[A-Za-z0-9_-]+::.*$", line)
        if m:
            return True, len(m.group(1))
        return False, 0

    def _compute_protected_mask(self, lines: list[str]) -> list[bool]:
        """
        Compute a mask of lines that should not be modified because they are
        inside the content of any RST/Sphinx directive, or match extra
        protected regexes from settings.

        Args:
            lines: Input lines

        Returns:
            A mask of lines that should not be modified

        """
        n = len(lines)
        protected = [False] * n
        i = 0
        while i < n:
            line = lines[i]
            is_dir, indent = self._is_directive_line(line)
            if is_dir:
                # Mark the directive line itself as protected
                protected[i] = True
                j = i + 1
                # The directive content continues while lines are blank or more indented
                while j < n:
                    nxt = lines[j]
                    if nxt.strip() == "":
                        protected[j] = True
                        j += 1
                        continue
                    next_indent = len(nxt) - len(nxt.lstrip(" "))
                    if next_indent > indent:
                        protected[j] = True
                        j += 1
                        continue
                    break
                i = j
                continue
            i += 1

        # Apply extra protected regexes
        if self._extra_protected_regexes:
            for idx, line in enumerate(lines):
                for rx in self._extra_protected_regexes:
                    if rx.search(line):
                        protected[idx] = True
                        break

        return protected

    def _ensure_blank_line_after_code_blocks(self, lines: list[str]) -> list[str]:
        """
        Ensure a blank line exists after every code-block directive.

        Args:
            lines: Input lines

        Returns:
            Updated lines

        """
        out: list[str] = []
        i = 0
        while i < len(lines):
            out.append(lines[i])
            if lines[i].lstrip().startswith(".. code-block::"):
                # Ensure there's a blank line after this code-block directive
                if i + 1 < len(lines) and lines[i + 1].strip() != "":
                    # Next line is not blank, so add a blank line
                    out.append("")
            i += 1
        return out
