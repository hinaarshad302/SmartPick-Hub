from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript"}


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)

        for attribute in ("href", "src"):
            value = values.get(attribute)
            if value:
                self.references.append(value)


def main() -> int:
    errors: list[str] = []
    pages = sorted(ROOT.glob("*.html"))

    if not pages:
        errors.append("No HTML pages were found in the repository root.")

    for page in pages:
        inspector = PageInspector()
        try:
            inspector.feed(page.read_text(encoding="utf-8"))
            inspector.close()
        except Exception as exc:
            errors.append(f"{page.name}: HTML parsing failed: {exc}")
            continue

        for duplicate in sorted(inspector.duplicates):
            errors.append(f"{page.name}: duplicate id '{duplicate}'")

        for reference in inspector.references:
            parsed = urlsplit(reference.strip())
            if parsed.scheme.lower() in IGNORED_SCHEMES or parsed.netloc:
                continue
            if not parsed.path:
                continue
            if parsed.path.startswith("/"):
                continue

            target = (page.parent / unquote(parsed.path)).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"{page.name}: reference escapes project root: {reference}"
                )
                continue

            if not target.is_file():
                errors.append(
                    f"{page.name}: missing local file reference: {reference}"
                )

    if errors:
        print("SmartPick Hub validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"SmartPick Hub validation passed: checked {len(pages)} HTML pages, "
        "duplicate IDs, and local href/src file references."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
