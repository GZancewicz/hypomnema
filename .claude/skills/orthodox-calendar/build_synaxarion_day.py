#!/usr/bin/env python3
"""Build one synaxarion day folder from an OLD-STYLE (Julian) date.

The Holy Trinity calendar.php endpoint only ever returns *today's* saints, so it
cannot back/forward-fill arbitrary dates. The Lives-of-Saints pages, however,
are addressable directly by old-style date:

    /calendar/los/<MonthName>/<DD>-<NN>.htm      (DD and NN both zero-padded)

This tool enumerates <NN> = 01, 02, ... (missing indices 404) for the given
old-style date, parses each life page (title, commemorated_on, text,
source_note, image_url), downloads each icon, and writes:

    synaxarion/calendar/<MM-Month>/<MM-DD>/commemorations.json
    synaxarion/calendar/<MM-Month>/<MM-DD>/<DD>-<NN>.jpg ...

Usage:
    python build_synaxarion_day.py 06-29
    python build_synaxarion_day.py June 29
    python build_synaxarion_day.py 6 29
    python build_synaxarion_day.py 06-29 --out /some/other/dir   # write elsewhere
    python build_synaxarion_day.py 06-29 --no-images             # skip icon download
    python build_synaxarion_day.py 06-29 --stdout                # print JSON, write nothing
"""
import argparse
import calendar
import importlib.util
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_CAL = os.path.join(REPO_ROOT, "synaxarion", "calendar")

_spec = importlib.util.spec_from_file_location(
    "fc", os.path.join(HERE, "fetch_commemorations.py"))
fc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fc)

BASE_LOS = "http://www.holytrinityorthodox.com/calendar/los"


def parse_old_style(tokens):
    """Accept '06-29', '6 29', or 'June 29' -> (month:int, day:int)."""
    if len(tokens) == 1 and "-" in tokens[0]:
        mm, dd = tokens[0].split("-")
        return int(mm), int(dd)
    if len(tokens) == 2:
        mtok, dtok = tokens
        mm = fc.MONTHS.get(mtok.lower()) if not mtok.isdigit() else int(mtok)
        if mm is None:
            raise ValueError(f"Unknown month: {mtok}")
        return mm, int(dtok)
    raise ValueError("Give an old-style date as MM-DD, 'Month DD', or 'MM DD'.")


def enumerate_lives(month, day, miss_tolerance=1):
    """Yield (url, life_dict) for NN=01,02,... until indices run out."""
    month_name = calendar.month_name[month]
    consecutive_misses = 0
    nn = 1
    while consecutive_misses <= miss_tolerance:
        url = f"{BASE_LOS}/{month_name}/{day:02d}-{nn:02d}.htm"
        try:
            life = fc.fetch_life(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                consecutive_misses += 1
                nn += 1
                continue
            raise
        consecutive_misses = 0
        yield url, life
        nn += 1


def download_image(image_url, folder):
    name = image_url.rsplit("/", 1)[-1]
    req = urllib.request.Request(image_url, headers={"User-Agent": "hypomnema-orthodox-calendar/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(os.path.join(folder, name), "wb") as f:
        f.write(data)
    return name


def build(month, day, cal_dir=DEFAULT_CAL, download_images=True, write=True,
          skip_existing=False):
    mmdd = f"{month:02d}-{day:02d}"
    month_name = calendar.month_name[month]
    folder = os.path.join(cal_dir, f"{month:02d}-{month_name}", mmdd)

    # Resume support: if this day is already built, don't re-fetch anything.
    if skip_existing and write and os.path.exists(os.path.join(folder, "commemorations.json")):
        return folder, {"old_style_mmdd": mmdd, "count": None, "skipped_existing": True}

    commems = []
    for url, life in enumerate_lives(month, day):
        commems.append({
            "url": url,
            "title": life["title"],
            "commemorated_on": life["commemorated_on"],
            "text": life["text"],
            "source_note": life["source_note"],
            "image_url": life["image_url"],
        })
        time.sleep(0.3)

    payload = {
        "old_style_date": f"{month_name} {day}",
        "old_style_mmdd": mmdd,
        "source": f"{BASE_LOS}/{month_name}/",
        "count": len(commems),
        "commemorations": commems,
    }

    # Nothing found (e.g. a day past the month's real length) — don't create a
    # spurious empty folder/file. Safe for month-long loops.
    if not commems or not write:
        return folder, payload

    os.makedirs(folder, exist_ok=True)
    if download_images:
        for entry in commems:
            if entry["image_url"]:
                try:
                    entry["image_file"] = download_image(entry["image_url"], folder)
                except Exception as e:  # noqa: BLE001
                    entry["image_error"] = str(e)
                time.sleep(0.3)
    with open(os.path.join(folder, "commemorations.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return folder, payload


def _report(folder, payload):
    if payload.get("skipped_existing"):
        print(f"{payload['old_style_mmdd']}: already built — skipped")
    elif payload["count"] == 0:
        print(f"{payload['old_style_mmdd']}: no commemorations — skipped")
    else:
        print(f"wrote {folder}/commemorations.json  ({payload['count']} commemorations)")


def build_month(month, cal_dir, download_images, skip_existing):
    ndays = calendar.monthrange(2000, month)[1]  # 2000 is leap, so Feb=29
    print(f"Building {calendar.month_name[month]} (old style), days 1–{ndays}…")
    for day in range(1, ndays + 1):
        folder, payload = build(month, day, cal_dir=cal_dir,
                                download_images=download_images, write=True,
                                skip_existing=skip_existing)
        _report(folder, payload)
        if not payload.get("skipped_existing"):
            time.sleep(1)


def main():
    ap = argparse.ArgumentParser(description="Build synaxarion day/month/year folders from an old-style date.")
    ap.add_argument("date", nargs="*", help="old-style date: MM-DD, 'Month DD', or 'MM DD'")
    ap.add_argument("--month", help="build a WHOLE old-style month (e.g. --month 6 or --month June); loops all its days")
    ap.add_argument("--year", action="store_true", help="build the ENTIRE old-style year (all 12 months) in one run")
    ap.add_argument("--out", default=DEFAULT_CAL, help="calendar dir to write into (default: repo synaxarion/calendar)")
    ap.add_argument("--no-images", action="store_true", help="do not download icon images")
    ap.add_argument("--skip-existing", action="store_true", help="skip days whose commemorations.json already exists (resume)")
    ap.add_argument("--stdout", action="store_true", help="print JSON only; write nothing to disk")
    args = ap.parse_args()

    if args.year:
        for month in range(1, 13):
            build_month(month, args.out, not args.no_images, args.skip_existing)
        return

    if args.month:
        mtok = args.month
        month = fc.MONTHS.get(mtok.lower()) if not mtok.isdigit() else int(mtok)
        if not month or not (1 <= month <= 12):
            ap.error(f"bad --month: {args.month}")
        build_month(month, args.out, not args.no_images, args.skip_existing)
        return

    if not args.date:
        ap.error("give a date (MM-DD / 'Month DD' / 'MM DD'), --month, or --year")

    month, day = parse_old_style(args.date)
    folder, payload = build(
        month, day,
        cal_dir=args.out,
        download_images=not args.no_images,
        write=not args.stdout,
        skip_existing=args.skip_existing,
    )
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload.get("skipped_existing"):
        print(f"{payload['old_style_mmdd']}: already built — skipped")
    elif payload["count"] == 0:
        print(f"{payload['old_style_mmdd']}: no commemorations found — skipped (no folder written)")
    else:
        print(f"wrote {os.path.join(folder, 'commemorations.json')}  "
              f"({payload['count']} commemorations)")
        for c in payload["commemorations"]:
            print(f"  - {c['title'][:60]:60}  img={c.get('image_file', '-')}")


if __name__ == "__main__":
    main()
