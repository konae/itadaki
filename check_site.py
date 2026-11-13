"""Validate the static publication directory without external dependencies."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

SITE = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f"Duplicate id: {attrs['id']}")
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == "img" and "alt" not in attrs:
            self.errors.append("Image missing alt text")


def check():
    errors = []
    pages = list(SITE.rglob("*.html"))
    if not (SITE / "index.html").is_file():
        errors.append("Missing index.html")
    for path in pages:
        parser = Page()
        source = path.read_text()
        parser.feed(source)
        errors.extend(parser.errors)
        if "__VINEXT" in source or "<script" in source:
            errors.append(f"Unexpected runtime script: {path.name}")
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if link.startswith("/"):
                errors.append(f"Root-relative path breaks project Pages: {link}")
            target = path.parent / unquote(url.path) if url.path else path
            if not target.is_file():
                errors.append(f"Missing local file: {link}")
            if not url.path and url.fragment and url.fragment not in parser.ids:
                errors.append(f"Missing section: {link}")
    for path in SITE.rglob("*.css"):
        for link in re.findall(r"url\(['\"]?([^)'\"]+)", path.read_text()):
            if not urlsplit(link).scheme and not (path.parent / link).is_file():
                errors.append(f"Missing CSS asset: {link}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(pages)} HTML page(s), local assets and section links verified")


if __name__ == "__main__":
    check()
