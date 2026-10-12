#!/usr/bin/env python3
"""Fail unless index.html has exactly one accessibility-statement link.

The link must point to the exact statement URL, carry the exact text
"הצהרת נגישות", and have no target attribute.
It also fails if a CSS rule whose selector names a `.footer` class sets `opacity`:
opacity dims footer text below the 4.5:1 WCAG AA contrast.
Run from the repo root.
"""
import re
import sys
from html.parser import HTMLParser

URL = "https://aimprove.co.il/accessibility-statement/"
TEXT = "הצהרת נגישות"


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self._open = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._open = {"attrs": dict(attrs), "has_target": any(k == "target" for k, _ in attrs), "text": ""}

    def handle_data(self, data):
        if self._open is not None:
            self._open["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._open is not None:
            self.anchors.append(self._open)
            self._open = None


def footer_opacity_problems(source):
    """Return one problem per CSS rule naming a `.footer` class that sets opacity."""
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", source, re.S | re.I))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    problems = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if ".footer" not in selector:
            continue
        if re.search(r"(?:^|;)\s*opacity\s*:", body.strip(), re.I):
            problems.append("CSS rule %r sets opacity, which dims footer text below 4.5:1 contrast" % " ".join(selector.split()))
    return problems


def main():
    with open("index.html", encoding="utf-8") as f:
        source = f.read()
    collector = Collector()
    collector.feed(source)
    matches = [a for a in collector.anchors if a["attrs"].get("href") == URL]
    problems = []
    if len(matches) != 1:
        problems.append("expected exactly 1 anchor with href %s, found %d" % (URL, len(matches)))
    for a in matches:
        if a["text"] != TEXT:
            problems.append("anchor text is %r, expected %r" % (a["text"], TEXT))
        if a["has_target"]:
            problems.append("anchor has a target attribute")
    problems.extend(footer_opacity_problems(source))
    if problems:
        for p in problems:
            print("check-a11y-link: FAIL - " + p)
        return 1
    print("check-a11y-link: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
