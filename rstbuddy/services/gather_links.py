"""
RST link gathering service.

This module provides `RSTLinkGatherer`, a service that consolidates all external
hyperlinks from RST documentation into a single `_links.rst` file and replaces
inline links with references to this centralized file.

The service:
1. Recursively scans RST files for external hyperlinks
2. Generates unique labels for each URL
3. Creates/updates `_links.rst` with consolidated links
4. Replaces inline links with label references
5. Updates conf.py with rst_epilog configuration
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from ..settings import Settings


class RSTLinkGatherer:
    """
    Consolidate RST hyperlinks into a centralized _links.rst file.

    This service scans RST documentation, extracts external hyperlinks,
    generates unique labels, and replaces inline links with references.

    Attributes:
        documentation_dir: Root directory containing RST documentation
        links_file: Path to the _links.rst file
        links: Dictionary mapping URLs to their generated labels
        labels: Dictionary mapping labels to their URLs
        files_to_modify: List of files that will be modified
        link_patterns: Regex patterns for detecting RST hyperlinks

    """

    def __init__(self, documentation_dir: Path | str) -> None:
        """
        Initialize the link gatherer.

        Args:
            documentation_dir: Root directory containing RST documentation

        """
        self.documentation_dir = Path(documentation_dir)
        self.settings = Settings()
        self.links_file = self.documentation_dir / "_links.rst"

        # Regex patterns for RST hyperlinks
        self.link_patterns = [
            # <scheme://domain/path>_
            re.compile(r"<([^>]+)>_"),
            # Label <scheme://domain/path>_ (with optional backticks)
            re.compile(r"`?([^<`]+)\s+<([^>]+)>`?_"),
        ]

        # Track discovered links and their labels
        self.links: dict[str, str] = {}  # url -> label
        self.labels: dict[str, str] = {}  # label -> url

        # Track files to be modified
        self.files_to_modify: list[Path] = []

    def gather_links(self, dry_run: bool = False) -> dict[str, str]:
        """
        Gather all external hyperlinks from RST documentation.

        Args:
            dry_run: If True, show what would be done without making changes

        Returns:
            Dictionary mapping URLs to their generated labels

        """
        if not dry_run:
            print(f"Scanning RST files in {self.documentation_dir}")

        # Scan all RST files
        rst_files = list(self.documentation_dir.rglob("*.rst"))
        rst_files = [f for f in rst_files if f.name != "_links.rst"]

        if not dry_run:
            print(f"Found {len(rst_files)} RST files to process")

            # Process each file
        for rst_file in rst_files:
            self._process_file(rst_file)

        print(f"Discovered {len(self.links)} unique external links")

        return self.links

    def _process_file(self, file_path: Path) -> None:
        """
        Process a single RST file for hyperlinks.

        Args:
            file_path: Path to the RST file to process

        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ["latin-1", "cp1252"]:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"Warning: Could not read {file_path} with any encoding")
                return

        # Check if we're in a References section
        in_references_section = self._is_in_references_section(content)

        # Extract links
        links_found = self._extract_links(content, in_references_section)

        if links_found and not in_references_section:
            self.files_to_modify.append(file_path)

    def _is_in_references_section(self, content: str) -> bool:
        """
        Check if content contains a References section.

        Args:
            content: The RST content to check

        Returns:
            True if the content contains a References section, False otherwise

        """
        # Look for section headers containing "references" (case-insensitive)
        section_pattern = re.compile(r'^[=~^"\'\-]+$', re.MULTILINE)
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if section_pattern.match(line) and i > 0:
                # Check if previous line contains "references"
                prev_line = lines[i - 1].strip()
                if "references" in prev_line.lower():
                    return True

        return False

    def _extract_links(self, content: str, skip_links: bool) -> bool:
        """
        Extract hyperlinks from RST content.

        Args:
            content: The RST content to extract links from
            skip_links: If True, skip link extraction

        Returns:
            True if links were found, False otherwise

        """
        links_found = False

        for pattern in self.link_patterns:
            for match in pattern.finditer(content):
                if skip_links:
                    continue

                if len(match.groups()) == 1:
                    # <scheme://domain/path>_
                    url = match.group(1)
                    label = None
                else:
                    # Label <scheme://domain/path>_
                    label = match.group(1).strip()
                    url = match.group(2)

                # Validate URL
                if self._is_valid_external_url(url):
                    self._add_link(url, label)
                    links_found = True

        return links_found

    def _is_valid_external_url(self, url: str) -> bool:
        """
        Check if URL is a valid external hyperlink.

        Args:
            url: The URL string to validate

        Returns:
            True if the URL is a valid external hyperlink, False otherwise

        """
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ("http", "https")  # type: ignore[return-value]
                and parsed.netloc
                and not url.startswith("#")
            )
        except (ValueError, TypeError):
            # URL parsing failed due to invalid input
            return False

    def _add_link(self, url: str, label: str | None) -> None:
        """
        Add a link to the collection, generating a label if needed.

        Args:
            url: The URL to add
            label: Optional label for the URL. If None, a label will be generated

        """
        # Normalize URL (remove trailing slash)
        normalized_url = url.rstrip("/")

        # Check if we already have this URL
        if normalized_url in self.links:
            return

        # Generate label if not provided
        if not label:
            label = self._generate_label(normalized_url)

        # Ensure label uniqueness
        original_label = label
        counter = 1
        while label in self.labels:
            if self.labels[label] == normalized_url:
                # Same label, same URL - skip
                return
            # Same label, different URL - generate new label
            label = f"{original_label}{counter}"
            counter += 1

        # Store the link
        self.links[normalized_url] = label
        self.labels[label] = normalized_url

    def _generate_label(self, url: str) -> str:
        """
        Generate a unique label for a URL.

        Args:
            url: The URL to generate a label for

        Returns:
            A unique label string for the URL

        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        domain = domain.removeprefix("www.")

        # Convert domain to CamelCase
        domain_parts = domain.split(".")
        label = "".join(part.capitalize() for part in domain_parts)

        # If URL has a path, add path components for uniqueness
        if parsed.path and parsed.path != "/":
            path_parts = [p for p in parsed.path.split("/") if p]

            # Start with last component, stripping .html
            if path_parts:
                last_part = path_parts[-1]
                last_part = last_part.removesuffix(".html")

                # Add path components until uniqueness is achieved
                for i in range(len(path_parts) - 1, -1, -1):
                    part = path_parts[i]
                    part = part.removesuffix(".html")

                    test_label = f"{label}{part.capitalize()}"
                    if test_label not in self.labels:
                        label = test_label
                        break

                    # Limit to 4 components total
                    if len(path_parts) - i >= 4:  # noqa: PLR2004
                        break

        return label

    def create_links_file(self, dry_run: bool = False) -> None:
        """
        Create or update the _links.rst file.

        Args:
            dry_run: If True, show what would be done without creating the file

        """
        if dry_run:
            print(f"Would create/update {self.links_file}")
            for url, label in self.links.items():
                print(f"  .. _{label}: {url}")
            return

        # Create content
        content = "# External Links\n\n"
        content += (
            "This file contains all external hyperlinks used in the documentation.\n\n"
        )

        for url, label in sorted(self.links.items()):
            content += f".. _{label}: {url}\n"

        # Write file
        self.links_file.write_text(content, encoding="utf-8")
        print(f"Created/updated {self.links_file}")
        return

    def backup_files(self, dry_run: bool = False) -> bool:
        """
        Create backups of all files to be modified.

        Args:
            dry_run: If True, show what would be done without creating backups

        Returns:
            True if backups were created successfully, False otherwise

        """
        if dry_run:
            print(f"Would create backups of {len(self.files_to_modify)} files")
            return True

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # noqa: DTZ005

        for file_path in self.files_to_modify:
            backup_path = file_path.with_suffix(f".{timestamp}.bak")
            try:
                shutil.copy2(file_path, backup_path)
                print(f"Backed up {file_path} to {backup_path}")
            except OSError as e:
                # File system errors: permission denied, disk full, file not found, etc.
                print(f"Error backing up {file_path}: {e}")
                return False

        return True

    def replace_links(self, dry_run: bool = False) -> None:
        """
        Replace inline links with label references.

        Args:
            dry_run: If True, show what would be done without replacing links

        """
        if dry_run:
            print(f"Would replace links in {len(self.files_to_modify)} files")
            return

        for file_path in self.files_to_modify:
            self._replace_links_in_file(file_path)

    def _replace_links_in_file(self, file_path: Path) -> None:
        """
        Replace links in a single file.

        Args:
            file_path: Path to the file to modify

        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Warning: Could not read {file_path} for replacement")
            return

        # Replace each link pattern
        for url, label in self.links.items():
            # Pattern 1: <scheme://domain/path>_
            content = re.sub(rf"<{re.escape(url)}>_", f"`{label}`_", content)

            # Pattern 2: Label <scheme://domain/path>_ (with optional backticks)
            content = re.sub(
                rf"`?([^<`]+)\s+<{re.escape(url)}>`?_", rf"\1 `{label}`_", content
            )

        # Write updated content
        file_path.write_text(content, encoding="utf-8")
        print(f"Updated {file_path}")

    def update_conf_py(self, dry_run: bool = False) -> bool:  # noqa: PLR0911
        """
        Update conf.py with rst_epilog configuration.

        Args:
            dry_run: If True, show what would be done without updating conf.py

        Returns:
            True if conf.py was updated successfully, False otherwise

        """
        conf_py_path = self.documentation_dir / "conf.py"

        if not conf_py_path.exists():
            print(f"Warning: conf.py not found at {conf_py_path}")
            return True

        if dry_run:
            print(f"Would update {conf_py_path} with rst_epilog configuration")
            return True

        # Read the file with specific error handling
        try:
            content = conf_py_path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error reading {conf_py_path}: {e}")
            return False
        except UnicodeDecodeError as e:
            print(f"Error decoding {conf_py_path} (encoding issue): {e}")
            return False

        # Check if rst_epilog already exists
        if "rst_epilog" in content:
            print(f"rst_epilog already configured in {conf_py_path}")
            return True

        # Find extensions list
        extensions_match = re.search(r"extensions\s*=\s*\[", content)

        if extensions_match:
            # Insert after extensions
            insert_pos = content.find("]", extensions_match.end())
            if insert_pos != -1:
                new_content = (
                    content[: insert_pos + 1]
                    + "\n\n"
                    + 'rst_epilog = ""\n'
                    + 'with open("_links.rst", "r", encoding="utf-8") as links:\n'
                    + "    rst_epilog += links.read()\n"
                    + content[insert_pos + 1 :]
                )
            else:
                new_content = content + (
                    '\n\nrst_epilog = ""\n'
                    'with open("_links.rst", "r", encoding="utf-8") as links:\n'
                    "    rst_epilog += links.read()\n"
                )
        else:
            # Add at end of file
            new_content = content + (
                '\n\nrst_epilog = ""\n'
                'with open("_links.rst", "r", encoding="utf-8") as links:\n'
                "    rst_epilog += links.read()\n"
            )

        # Write updated content with specific error handling
        try:
            conf_py_path.write_text(new_content, encoding="utf-8")
            print(f"Updated {conf_py_path}")
        except OSError as e:
            print(f"Error writing to {conf_py_path}: {e}")
            return False
        else:
            return True

    def run(self, dry_run: bool = False) -> bool:  # noqa: PLR0911
        """
        Run the complete link gathering process.

        Args:
            dry_run: If True, show what would be done without making changes

        Returns:
            True if successful, False otherwise

        """
        # Phase 1: Gather links
        try:
            self.gather_links(dry_run)
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error during link gathering phase: {e}")
            return False

        if not self.links:
            print("No external links found")
            return True

        # Phase 2: Create links file
        try:
            self.create_links_file(dry_run)
        except OSError as e:
            print(f"Error creating links file: {e}")
            return False

        if dry_run:
            return True

        # Phase 3: Create backups
        if not self.backup_files(dry_run):
            print("Backup failed - halting process")
            return False

        # Phase 4: Replace links
        try:
            self.replace_links(dry_run)
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error during link replacement phase: {e}")
            return False

        # Phase 5: Update conf.py
        if not self.update_conf_py(dry_run):
            print("Failed to update conf.py")
            return False

        print("Link gathering completed successfully")
        return True
