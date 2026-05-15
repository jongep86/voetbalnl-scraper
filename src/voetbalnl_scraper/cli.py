"""voetbalnl_scraper.cli — zie README voor gebruik."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.voetbal.nl"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

NL_MONTHS = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10,
    "november": 11, "december": 12,
}


@dataclass
class Match:
    kind: str
    match_id: str | None
    date: str
    start: str | None = None
    round: str | None = None
    home: str = ""
    away: str = ""
    score_home: int | None = None
    score_away: int | None = None
    location: str | None = None
    field: str | None = None
    kleedkamer: str | None = None
    wedstrijdnummer: str | None = None
    detail_url: str | None = None


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    })
    s.get(BASE, timeout=15)
    return s


def parse_dutch_date(text: str) -> datetime | None:
    m = re.search(r"(\d{1,2})\s+([a-zé]+)\s+(\d{4})", text, re.IGNORECASE)
    if not m:
        return None
    month = NL_MONTHS.get(m.group(2).lower())
    if not month:
        return None
    return datetime(int(m.group(3)), month, int(m.group(1)))


def parse_center_value(text: str):
    text = text.strip()
    m_time = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if m_time:
        return ("time", f"{int(m_time.group(1)):02d}:{m_time.group(2)}")
    m_score = re.match(r"^(\d+)\s*-\s*(\d+)$", text)
    if m_score:
        return ("score", m_score.group(1), m_score.group(2))
    return ("unknown", text)


def fetch_team_page(session: requests.Session, team_id: str, tab: str) -> list[Match]:
    assert tab in ("programma", "uitslagen")
    url = f"{BASE}/team/{team_id}/{tab}"
    soup = BeautifulSoup(session.get(url, timeout=15).text, "html.parser")

    out: list[Match] = []
    content = soup.select_one(".ScheduleResults-content")
    if not content:
        return out

    current_date: datetime | None = None
    current_round: str | None = None
    kind = "programma" if tab == "programma" else "uitslag"

    for el in content.select(".header, .row"):
        cls = " ".join(el.get("class", []))
        if "header" in cls:
            title = el.select_one(".title")
            subtitle = el.select_one(".subtitle")
            if title:
                current_date = parse_dutch_date(title.get_text(strip=True))
            current_round = subtitle.get_text(strip=True) if subtitle else None
            continue

        home = el.select_one(".value.home .team")
        away = el.select_one(".value.away .team")
        center = el.select_one(".value.center")
        link = el.find("a", href=re.compile(r"/wedstrijd/M\d+"))
        if not (home and away and center and current_date):
            continue

        match_id = None
        detail_url = None
        if link and link.get("href"):
            mm = re.search(r"/wedstrijd/(M\d+)", link["href"])
            if mm:
                match_id = mm.group(1)
            detail_url = urljoin(BASE, link["href"])

        m = Match(
            kind=kind,
            match_id=match_id,
            date=current_date.strftime("%Y-%m-%d"),
            round=current_round,
            home=home.get_text(strip=True),
            away=away.get_text(strip=True),
            detail_url=detail_url,
        )

        parsed = parse_center_value(center.get_text(strip=True))
        if parsed[0] == "time":
            hh, mi = parsed[1].split(":")
            m.start = current_date.replace(
                hour=int(hh), minute=int(mi)
            ).strftime("%Y-%m-%dT%H:%M:%S")
        elif parsed[0] == "score":
            m.score_home = int(parsed[1])
            m.score_away = int(parsed[2])

        out.append(m)

    return out


def enrich_match(session: requests.Session, match: Match) -> None:
    if not match.match_id:
        return
    url = f"{BASE}/wedstrijd/{match.match_id}/uitslag"
    try:
        text = BeautifulSoup(session.get(url, timeout=15).text,
                             "html.parser").get_text("\n", strip=True)
    except requests.RequestException:
        return

    if not match.start:
        mt = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
        if mt:
            base = datetime.strptime(match.date, "%Y-%m-%d")
            match.start = base.replace(
                hour=int(mt.group(1)), minute=int(mt.group(2))
            ).strftime("%Y-%m-%dT%H:%M:%S")

    loc_node = re.search(r"(Sportpark[^\n]*|Sportcomplex[^\n]*)", text, re.IGNORECASE)
    if loc_node:
        match.location = loc_node.group(1).strip()

    for label, attr in (("Wedstrijdnr.", "wedstrijdnummer"),
                        ("Veld", "field"),
                        ("Kleedkamer", "kleedkamer")):
        mm = re.search(rf"{re.escape(label)}\s*\n([^\n]+)", text)
        if mm:
            setattr(match, attr, mm.group(1).strip())


def to_json(matches: list[Match]) -> str:
    return json.dumps([asdict(m) for m in matches], ensure_ascii=False, indent=2)


def to_ics(matches: list[Match], calendar_name: str) -> str:
    def fmt_local(dt): return dt.strftime("%Y%m%dT%H%M%S")
    def fmt_date(dt):  return dt.strftime("%Y%m%d")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//voetbalnl-scraper//NL",
        f"X-WR-CALNAME:{calendar_name}",
        "X-WR-TIMEZONE:Europe/Amsterdam",
    ]
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for m in matches:
        summary = f"{m.home} - {m.away}"
        if m.kind == "uitslag" and m.score_home is not None:
            summary += f" ({m.score_home}-{m.score_away})"

        desc = []
        if m.round: desc.append(f"Ronde: {m.round}")
        if m.wedstrijdnummer: desc.append(f"Wedstrijdnr.: {m.wedstrijdnummer}")
        if m.field: desc.append(f"Veld: {m.field}")
        if m.kleedkamer: desc.append(f"Kleedkamer: {m.kleedkamer}")
        if m.detail_url: desc.append(m.detail_url)

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{m.match_id or uuid.uuid4()}@voetbal.nl")
        lines.append(f"DTSTAMP:{now_utc}")
        if m.start:
            start = datetime.fromisoformat(m.start)
            end = start + timedelta(minutes=90)
            lines.append(f"DTSTART;TZID=Europe/Amsterdam:{fmt_local(start)}")
            lines.append(f"DTEND;TZID=Europe/Amsterdam:{fmt_local(end)}")
        else:
            day = datetime.strptime(m.date, "%Y-%m-%d")
            lines.append(f"DTSTART;VALUE=DATE:{fmt_date(day)}")
            lines.append(f"DTEND;VALUE=DATE:{fmt_date(day + timedelta(days=1))}")
        lines.append(f"SUMMARY:{summary}")
        lines.append(f"LOCATION:{m.location or ''}")
        lines.append("DESCRIPTION:" + "\\n".join(desc))
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="voetbalnl-scraper",
                                description="Voetbal.nl team scraper")
    p.add_argument("team_id", help="Team-ID, bv. T1413246730")
    p.add_argument("--include", choices=("programma", "uitslagen", "alles"),
                   default="alles")
    p.add_argument("--format", choices=("ics", "json"), default="ics")
    p.add_argument("--out", help="Outputbestand (default: stdout)")
    p.add_argument("--no-enrich", action="store_true",
                   help="Sla detail-requests over")
    p.add_argument("--delay", type=float, default=0.8,
                   help="Wachttijd (s) tussen detail-requests")
    args = p.parse_args(argv)

    session = make_session()
    matches: list[Match] = []
    if args.include in ("programma", "alles"):
        matches += fetch_team_page(session, args.team_id, "programma")
    if args.include in ("uitslagen", "alles"):
        matches += fetch_team_page(session, args.team_id, "uitslagen")

    if not args.no_enrich:
        for m in matches:
            enrich_match(session, m)
            time.sleep(args.delay)

    matches.sort(key=lambda m: (m.start or m.date))

    output = to_json(matches) if args.format == "json" \
        else to_ics(matches, calendar_name=f"Team {args.team_id}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"{len(matches)} wedstrijden geschreven naar {args.out}",
              file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
