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

## Inloggen

Voetbal.nl vereist sinds 2026 een login om team-pagina's te bekijken. Je geeft
je inloggegevens op één van deze manieren:

```bash
# 1. via environment variables (aanbevolen — geen credentials in shell-history)
export VOETBALNL_EMAIL="je@email.nl"
export VOETBALNL_PASSWORD="..."
voetbalnl-scraper T1413246730

# 2. via flags
voetbalnl-scraper T1413246730 --email je@email.nl --password '...'

# 3. interactief — laat password leeg en je krijgt een getpass-prompt
voetbalnl-scraper T1413246730 --email je@email.nl
```

De sessie-cookie wordt opgeslagen in
`~/.cache/voetbalnl-scraper/cookies.txt`, zodat volgende runs niet opnieuw
hoeven in te loggen. Cookies wissen:

```bash
voetbalnl-scraper --logout T1413246730   # team_id wordt niet gebruikt
```

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

| Flag           | Default                                | Betekenis                                              |
|----------------|----------------------------------------|--------------------------------------------------------|
| `--include`    | `alles`                                | `programma`, `uitslagen` of `alles`                    |
| `--format`     | `ics`                                  | `ics` of `json`                                        |
| `--out`        | stdout                                 | Outputbestand                                          |
| `--no-enrich`  | uit                                    | Sla de extra detailpagina-requests over                |
| `--delay`      | `0.8`                                  | Wachttijd in seconden tussen detail-requests           |
| `--email`      | env `VOETBALNL_EMAIL`                  | Login email                                            |
| `--password`   | env `VOETBALNL_PASSWORD` of prompt     | Login wachtwoord                                       |
| `--cookies`    | `~/.cache/voetbalnl-scraper/cookies.txt` | Cookie-jar pad                                       |
| `--no-cookies` | uit                                    | Bewaar geen cookies tussen runs                        |
| `--logout`     | —                                      | Verwijder opgeslagen cookies en stop                   |

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
