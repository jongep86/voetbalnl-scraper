# voetbalnl-scraper

Scrape het programma en de uitslagen van een Voetbal.nl-team naar een ICS-agenda
of JSON.

## Installatie

```bash
# vanaf een lokale clone
pipx install .

# of editable tijdens ontwikkelen
pipx install --editable .

# of direct van GitHub
pipx install git+https://github.com/<jouw-user>/voetbalnl-scraper.git
```

Na installatie staat het commando `voetbalnl-scraper` op je PATH.

## Gebruik

```bash
# ICS-agenda van programma + uitslagen
voetbalnl-scraper T1413246730 --out team.ics

# alleen uitslagen als JSON
voetbalnl-scraper T1413246730 --include uitslagen --format json --out uitslagen.json

# zonder de extra detail-requests per wedstrijd
voetbalnl-scraper T1413246730 --no-enrich --out team.ics
```

Vlaggen:

| Flag           | Default  | Betekenis                                              |
|----------------|----------|--------------------------------------------------------|
| `--include`    | `alles`  | `programma`, `uitslagen` of `alles`                    |
| `--format`     | `ics`    | `ics` of `json`                                        |
| `--out`        | stdout   | Outputbestand                                          |
| `--no-enrich`  | uit      | Sla de extra detailpagina-requests over                |
| `--delay`      | `0.8`    | Wachttijd in seconden tussen detail-requests           |

Het team-ID staat in de URL van een Voetbal.nl-teampagina (bv. `T1413246730`).

## Upgraden / verwijderen

```bash
pipx upgrade voetbalnl-scraper
pipx reinstall voetbalnl-scraper
pipx uninstall voetbalnl-scraper
```

## Ontwikkelen

```bash
git clone https://github.com/<jouw-user>/voetbalnl-scraper.git
cd voetbalnl-scraper
pipx install --editable .
```

Met `--editable` linkt pipx naar de werkmap — wijzigingen in `src/` pakt het
commando direct mee.

## Licentie

MIT
