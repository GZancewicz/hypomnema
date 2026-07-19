#!/usr/bin/env python3
"""Fetch the saints commemorated on a given day from the Holy Trinity
Orthodox Church calendar "API" (calendar.php) and return their Lives-of-Saints
links.

Endpoint:  http://www.holytrinityorthodox.com/calendar/calendar.php
Params:    mm, dd, yy (date) + content flags dt/hh/ll/tt/ss (1 to enable).
           ll=1 emits the Lives of Saints, which carry the saint links.
Saint life URL pattern:
           /calendar/los/<MonthName>/<DD>-<NN>.htm

No proxy is needed for server-side requests; the ppp.php proxy in the official
docs only exists to satisfy browser cross-origin rules for in-page JavaScript.

Usage:
    python fetch_commemorations.py 2024-06-29
    python fetch_commemorations.py 6 29 2024
    python fetch_commemorations.py 2024-06-29 --lives   # also fetch page text
    python fetch_commemorations.py 2024-06-29 --raw      # dump raw calendar HTML
"""
import argparse
import datetime
import html
import json
import re
import sys
import urllib.request
from urllib.parse import urljoin

BASE = "http://www.holytrinityorthodox.com/calendar/calendar.php"
LOS_RE = re.compile(
    r'<a[^>]*href="([^"]*?/calendar/los/[^"]+\.htm)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
LOS_DATE_RE = re.compile(r"/calendar/los/([A-Za-z]+)/(\d+)-\d+\.htm", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r'<p class="body10">(.*?)</p>', re.IGNORECASE | re.DOTALL)
IMG_RE = re.compile(r'<img[^>]*\bsrc="([^"]+)"', re.IGNORECASE)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


def old_style_mmdd(commems):
    """Derive the old-calendar (Julian) MM-DD from the los links, which are
    filed under /los/<OldStyleMonth>/<OldStyleDay>-NN.htm. All commemorations
    for one civil day share the same old-style date."""
    for c in commems:
        m = LOS_DATE_RE.search(c["url"])
        if m:
            mm = MONTHS.get(m.group(1).lower())
            if mm:
                return f"{mm:02d}-{int(m.group(2)):02d}"
    return None


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hypomnema-orthodox-calendar/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        # The whole site is declared windows-1251 (Cyrillic); even the English
        # life pages use cp1251 for em-dashes and curly quotes. Decoding as
        # utf-8 mangles those into U+FFFD.
        return resp.read().decode("cp1251", errors="replace")


def _clean(fragment):
    text = TAG_RE.sub("", fragment)
    text = html.unescape(text).strip().strip('"').strip()
    return re.sub(r"\s+", " ", text)


def _clean_block(fragment):
    """Turn one <p class="body10"> block into clean text. Only <br> marks a
    paragraph break; the source's own line-wrapping newlines become spaces."""
    text = BR_RE.sub("\x00", fragment)          # protect real breaks
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    paras = [re.sub(r"\s+", " ", p).strip() for p in text.split("\x00")]
    return "\n\n".join(p for p in paras if p)


def parse_date(argv_dates):
    if len(argv_dates) == 1:
        return datetime.date.fromisoformat(argv_dates[0])
    if len(argv_dates) == 3:
        mm, dd, yy = (int(x) for x in argv_dates)
        return datetime.date(yy, mm, dd)
    raise ValueError("Provide a date as YYYY-MM-DD or as: MM DD YYYY")


def fetch_calendar_html(d):
    url = f"{BASE}?mm={d.month}&dd={d.day}&yy={d.year}&dt=1&ll=1"
    return url, _get(url)


def extract_commemorations(cal_html):
    seen = {}
    for href, label in LOS_RE.findall(cal_html):
        if href not in seen:
            seen[href] = _clean(label)
    return [{"label": v, "url": k} for k, v in seen.items()]


def fetch_life(url):
    """Fetch a Lives-of-Saints page and pull out its structured content:
    title, "Commemorated on" date, body text, translator/source note, and the
    icon image URL (each page has one <img src="NN-NN.jpg"> beside the text)."""
    page = _get(url)
    title_m = TITLE_RE.search(page)
    img_m = IMG_RE.search(page)

    blocks = [_clean_block(b) for b in BODY_RE.findall(page)]
    blocks = [b for b in blocks if b]

    commemorated_on = ""
    source = ""
    body = []
    for b in blocks:
        if not commemorated_on and re.match(r"(?i)commemorated on\b", b):
            commemorated_on = re.sub(r"(?i)^commemorated on\s*", "", b).strip()
        elif b.lstrip().startswith(("©", "(c)", "(C)")):
            source = b
        else:
            body.append(b)

    return {
        "title": _clean(title_m.group(1)) if title_m else "",
        "commemorated_on": commemorated_on,
        "text": "\n\n".join(body),
        "source_note": source,
        "image_url": urljoin(url, img_m.group(1)) if img_m else "",
    }


def main():
    ap = argparse.ArgumentParser(description="Fetch commemorated saints for a date.")
    ap.add_argument("date", nargs="+", help="YYYY-MM-DD, or three ints: MM DD YYYY")
    ap.add_argument("--lives", action="store_true", help="also fetch each life page's title/text")
    ap.add_argument("--raw", action="store_true", help="print the raw calendar HTML and exit")
    args = ap.parse_args()

    d = parse_date(args.date)
    url, cal_html = fetch_calendar_html(d)

    if args.raw:
        sys.stdout.write(cal_html)
        return

    commems = extract_commemorations(cal_html)
    if args.lives:
        for c in commems:
            try:
                c.update(fetch_life(c["url"]))
            except Exception as e:  # noqa: BLE001
                c["error"] = str(e)

    print(json.dumps({
        "date": d.isoformat(),
        "civil_mmdd": f"{d.month:02d}-{d.day:02d}",
        "mmdd": old_style_mmdd(commems) or f"{d.month:02d}-{d.day:02d}",
        "source": url,
        "count": len(commems),
        "commemorations": commems,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
