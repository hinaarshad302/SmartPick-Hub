from __future__ import annotations

from html.parser import HTMLParser
import re
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

    cloudflare_workflow = ROOT / ".github" / "workflows" / "cloudflare-pages-deploy.yml"
    headers_config = ROOT / "_headers"
    if not cloudflare_workflow.is_file():
        errors.append("Cloudflare Pages deployment workflow is missing.")
    else:
        workflow_source = cloudflare_workflow.read_text(encoding="utf-8")
        if "workflow_dispatch:" not in workflow_source or "pages deploy dist" not in workflow_source:
            errors.append("Cloudflare Pages workflow must be manual and deploy the curated dist directory.")
    if not headers_config.is_file():
        errors.append("Cloudflare Pages _headers security configuration is missing.")

    for env_file in ROOT.glob(".env*"):
        if env_file.name != ".env.example":
            errors.append(
                f"{env_file.name}: environment files must not be committed."
            )

    secret_patterns = (
        re.compile(r"sb_secret_[A-Za-z0-9_-]{12,}"),
        re.compile(r"re_[A-Za-z0-9]{20,}"),
        re.compile(r"SUPABASE_SECRET_KEY\s*=\s*", re.IGNORECASE),
    )
    frontend_files = list(ROOT.glob("*.html")) + list(ROOT.glob("*.js"))
    for frontend_file in frontend_files:
        source = frontend_file.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            if pattern.search(source):
                errors.append(
                    f"{frontend_file.name}: possible server-side secret in frontend source."
                )
                break

    catalogue_path = ROOT / "products.json"
    if not catalogue_path.is_file():
        errors.append("Product catalogue products.json is missing.")
    else:
        import json

        try:
            catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
            if not isinstance(catalogue, list):
                errors.append("products.json: expected a JSON array of products.")
                catalogue = []
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"products.json: could not read valid JSON: {exc}")
            catalogue = []

        product_ids: set[str] = set()
        published_count = 0
        departments: set[str] = set()
        required_fields = ("id", "name", "category", "department", "description", "merchant", "image", "productUrl", "status", "markets")

        for index, product in enumerate(catalogue, start=1):
            label = f"products.json product #{index}"
            if not isinstance(product, dict):
                errors.append(f"{label}: expected a JSON object.")
                continue

            missing = [field for field in required_fields if product.get(field) in (None, "", [])]
            if missing:
                errors.append(f"{label}: missing required fields: {', '.join(missing)}.")

            product_id = product.get("id")
            if isinstance(product_id, str) and product_id:
                if product_id in product_ids:
                    errors.append(f"{label}: duplicate product id '{product_id}'.")
                product_ids.add(product_id)

            status = product.get("status")
            if status not in {"published", "draft", "archived"}:
                errors.append(f"{label}: unsupported status '{status}'.")

            if status == "published":
                published_count += 1
                department = product.get("department")
                if isinstance(department, str) and department:
                    departments.add(department)

                for field in ("image", "productUrl"):
                    value = product.get(field)
                    parsed = urlsplit(value if isinstance(value, str) else "")
                    if parsed.scheme != "https" or not parsed.netloc:
                        errors.append(f"{label}: '{field}' must be a valid HTTPS URL.")

                markets = product.get("markets")
                if not isinstance(markets, list) or not markets or not all(isinstance(market, str) and market.strip() for market in markets):
                    errors.append(f"{label}: published products must list at least one valid market.")

                affiliate_url = product.get("affiliateUrl") or ""
                if affiliate_url:
                    parsed_affiliate = urlsplit(affiliate_url)
                    if parsed_affiliate.scheme != "https" or not parsed_affiliate.netloc:
                        errors.append(f"{label}: 'affiliateUrl' must be a valid HTTPS URL when provided.")
                if not isinstance(product.get("isAffiliate"), bool):
                    errors.append(f"{label}: 'isAffiliate' must be true or false.")
                elif bool(affiliate_url) != product.get("isAffiliate"):
                    errors.append(f"{label}: 'isAffiliate' must match whether 'affiliateUrl' is populated.")

        if not catalogue:
            errors.append("products.json: catalogue must contain at least one product.")
        if catalogue and published_count == 0:
            errors.append("products.json: at least one product must be published.")
        if published_count and not departments:
            errors.append("products.json: published products must belong to a department.")


    click_migration = ROOT / "database" / "migrations" / "004_affiliate_click_events.sql"
    outbound_config = ROOT / "outbound-config.js"
    backend_source = ROOT / "backend" / "main.py"
    if not click_migration.is_file():
        errors.append("Affiliate click-events database migration is missing.")
    if not outbound_config.is_file():
        errors.append("Optional outbound tracking configuration is missing.")
    if not backend_source.is_file() or '"/out/{product_id}"' not in backend_source.read_text(encoding="utf-8"):
        errors.append("Backend outbound product redirect endpoint is missing.")

    for page in pages:
        page_source = page.read_text(encoding="utf-8")
        if page_source.lower().count("<!doctype html>") != 1:
            errors.append(f"{page.name}: expected exactly one HTML doctype declaration.")
        description_count = page_source.lower().count('name="description"') + page_source.lower().count("name='description'")
        if description_count > 1:
            errors.append(f"{page.name}: duplicate meta description tags.")

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
        "duplicate IDs, local href/src references, Cloudflare deployment configuration, and frontend secret patterns."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
