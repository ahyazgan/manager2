"""Backtest veri setini openfootball'dan güncelle (ücretsiz, GitHub raw).

Mevcut match_results.json (football-data.co.uk şeması, 2017-2023) üzerine
openfootball/football.json sezonlarını ekler:
- Takım adları ALIAS tablosuyla mevcut kısa adlara eşlenir (walk-forward
  güç sürekliliği için şart — "Man City" ile "Manchester City FC" aynı takım).
- Yeni gelen (küme yükselen) takımlar kısa kanonik adla girer.
- openfootball'da şut verisi yok → hst/ast alanları eklenmez; model
  (engine.strength / calibration.ts) şut yoksa gol-tabanlı gözleme düşer.
- Dedupe anahtarı: (comp, date, home, away).

Kullanım:
    python -m scripts.update_match_results [--cache-dir .cache/openfootball]

Çıktı: app/data/static/match_results.json (kanonik) +
       frontend/src/lib/match-results.json (frontend fallback kopyası).
Bilinmeyen takım adı görürse HATA verir (sessizce yeni takım uydurma yok) —
yeni sezon eklerken ALIAS tablosunu genişlet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_JSON = REPO_ROOT / "app" / "data" / "static" / "match_results.json"
FRONTEND_JSON = REPO_ROOT / "frontend" / "src" / "lib" / "match-results.json"

RAW_BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"

# Top-5 lig: SADECE 2023-24+ (öncesi football-data kaynağından zaten var;
# eski sezonları openfootball'dan çekmek ad-eşleme kapsamını patlatır).
_TOP5 = ("en.1", "es.1", "de.1", "it.1", "fr.1")
# Ek ligler: openfootball adları olduğu gibi kanonik — tüm mevcut sezonlar
# denenir, olmayan (404) sessizce atlanır.
PASSTHROUGH_LEAGUES = ("tr.1", "nl.1", "pt.1", "gr.1", "be.1", "at.1")
_ALL_SEASONS = (
    "2017-18", "2018-19", "2019-20", "2020-21", "2021-22", "2022-23",
    "2023-24", "2024-25", "2025-26",
)
SEASONS: list[tuple[str, str]] = [
    (season, lg)
    for season in ("2023-24", "2024-25", "2025-26")
    for lg in _TOP5
] + [
    (season, lg) for season in _ALL_SEASONS for lg in PASSTHROUGH_LEAGUES
]

# openfootball adı → mevcut veri setindeki (football-data tarzı) kısa ad.
# Değeri None olanlar: veri setine yeni giren takımlar — kısa kanonik ad
# openfootball adından "olduğu gibi" değil, buradaki açık karşılıkla girer.
ALIAS: dict[str, dict[str, str]] = {
    "en.1": {
        "AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal",
        "Aston Villa FC": "Aston Villa", "Brentford FC": "Brentford",
        "Brighton & Hove Albion FC": "Brighton", "Burnley FC": "Burnley",
        "Chelsea FC": "Chelsea", "Crystal Palace FC": "Crystal Palace",
        "Everton FC": "Everton", "Fulham FC": "Fulham",
        "Ipswich Town FC": "Ipswich", "Leeds United FC": "Leeds",
        "Leicester City FC": "Leicester", "Liverpool FC": "Liverpool",
        "Luton Town FC": "Luton", "Manchester City FC": "Man City",
        "Manchester United FC": "Man United",
        "Newcastle United FC": "Newcastle",
        "Nottingham Forest FC": "Nott'm Forest",
        "Sheffield United FC": "Sheffield United",
        "Southampton FC": "Southampton", "Sunderland AFC": "Sunderland",
        "Tottenham Hotspur FC": "Tottenham",
        "West Ham United FC": "West Ham",
        "Wolverhampton Wanderers FC": "Wolves",
    },
    "es.1": {
        "Athletic Club": "Ath Bilbao", "CA Osasuna": "Osasuna",
        "CD Leganés": "Leganes", "Club Atlético de Madrid": "Ath Madrid",
        "Cádiz CF": "Cadiz", "Deportivo Alavés": "Alaves",
        "Elche CF": "Elche", "FC Barcelona": "Barcelona",
        "Getafe CF": "Getafe", "Girona FC": "Girona",
        "Granada CF": "Granada", "Levante UD": "Levante",
        "RC Celta de Vigo": "Celta",
        "RCD Espanyol de Barcelona": "Espanol", "RCD Mallorca": "Mallorca",
        "Rayo Vallecano de Madrid": "Vallecano",
        "Real Betis Balompié": "Betis", "Real Madrid CF": "Real Madrid",
        "Real Oviedo": "Oviedo", "Real Sociedad de Fútbol": "Sociedad",
        "Real Valladolid CF": "Valladolid", "Sevilla FC": "Sevilla",
        "UD Almería": "Almeria", "UD Las Palmas": "Las Palmas",
        "Valencia CF": "Valencia", "Villarreal CF": "Villarreal",
    },
    "de.1": {
        "1. FC Heidenheim 1846": "Heidenheim", "1. FC Köln": "FC Koln",
        "1. FC Union Berlin": "Union Berlin", "1. FSV Mainz 05": "Mainz",
        "Bayer 04 Leverkusen": "Leverkusen",
        "Borussia Dortmund": "Dortmund",
        "Borussia Mönchengladbach": "M'gladbach",
        "Eintracht Frankfurt": "Ein Frankfurt", "FC Augsburg": "Augsburg",
        "FC Bayern München": "Bayern Munich",
        "FC St. Pauli 1910": "St Pauli", "Hamburger SV": "Hamburg",
        "Holstein Kiel": "Holstein Kiel", "RB Leipzig": "RB Leipzig",
        "SC Freiburg": "Freiburg", "SV Darmstadt 98": "Darmstadt",
        "SV Werder Bremen": "Werder Bremen",
        "TSG 1899 Hoffenheim": "Hoffenheim", "VfB Stuttgart": "Stuttgart",
        "VfL Bochum 1848": "Bochum", "VfL Wolfsburg": "Wolfsburg",
    },
    "fr.1": {
        "AJ Auxerre": "Auxerre", "AS Monaco FC": "Monaco",
        "AS Saint-Étienne": "St Etienne", "Angers SCO": "Angers",
        "Clermont Foot 63": "Clermont", "FC Lorient": "Lorient",
        "FC Metz": "Metz", "FC Nantes": "Nantes",
        "Le Havre AC": "Le Havre", "Lille OSC": "Lille",
        "Montpellier HSC": "Montpellier", "OGC Nice": "Nice",
        "Olympique Lyonnais": "Lyon",
        "Olympique de Marseille": "Marseille", "Paris FC": "Paris FC",
        "Paris Saint-Germain FC": "Paris SG",
        "RC Strasbourg Alsace": "Strasbourg",
        "Racing Club de Lens": "Lens", "Stade Brestois 29": "Brest",
        "Stade Rennais FC 1901": "Rennes", "Stade de Reims": "Reims",
        "Toulouse FC": "Toulouse",
    },
    "it.1": {
        "AC Milan": "Milan", "AC Monza": "Monza",
        "AC Pisa 1909": "Pisa", "ACF Fiorentina": "Fiorentina",
        "AS Roma": "Roma", "Atalanta BC": "Atalanta",
        "Bologna FC 1909": "Bologna", "Cagliari Calcio": "Cagliari",
        "Como 1907": "Como", "Empoli FC": "Empoli",
        "FC Internazionale Milano": "Inter",
        "Frosinone Calcio": "Frosinone", "Genoa CFC": "Genoa",
        "Hellas Verona FC": "Verona", "Juventus FC": "Juventus",
        "Parma Calcio 1913": "Parma", "SS Lazio": "Lazio",
        "SSC Napoli": "Napoli", "Torino FC": "Torino",
        "US Cremonese": "Cremonese", "US Lecce": "Lecce",
        "US Salernitana 1919": "Salernitana",
        "US Sassuolo Calcio": "Sassuolo", "Udinese Calcio": "Udinese",
        "Venezia FC": "Venezia",
    },
}


# Pass-through liglerde openfootball'un sezonlar arası ad kaymaları →
# tek kanonik ad (walk-forward güç sürekliliği için). Hem yeni gelen hem
# mevcut satırlara uygulanır (idempotent).
NORMALIZE: dict[str, dict[str, str]] = {
    "nl.1": {
        "AZ Alkmaar": "AZ", "FC Twente '65": "FC Twente",
        "Feyenoord Rotterdam": "Feyenoord", "NEC Nijmegen": "NEC",
        "PSV Eindhoven": "PSV", "Willem II Tilburg": "Willem II",
        "sc Heerenveen": "SC Heerenveen", "SBV Vitesse": "Vitesse",
    },
    "pt.1": {
        "Boavista FC": "Boavista", "GD Estoril Praia": "GD Estoril",
        "Gil Vicente FC": "Gil Vicente",
        "Sport Lisboa e Benfica": "SL Benfica",
        "Sporting Clube de Braga": "Sporting Braga",
        "Sporting Clube de Portugal": "Sporting CP",
    },
    "tr.1": {
        "Atiker Konyaspor": "Konyaspor",
        "Gazişehir Gaziantep FK": "Gaziantep FK",
    },
}


def _canon(lg: str, name: str) -> str:
    return NORMALIZE.get(lg, {}).get(name, name)


def _fetch(season: str, lg: str, cache_dir: Path | None) -> list[dict] | None:
    path = f"{season}/{lg}.json"
    cache_file = cache_dir / season / f"{lg}.json" if cache_dir else None
    if cache_file is not None and cache_file.is_file():
        return json.loads(cache_file.read_text(encoding="utf-8"))["matches"]
    url = f"{RAW_BASE}/{path}"
    r = httpx.get(url, timeout=30.0)
    if r.status_code == 404:
        print(f"  yok (404): {path}")
        return None
    r.raise_for_status()
    data = r.json()
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    return data["matches"]


def _season_tag(season: str) -> str:
    a, b = season.split("-")
    return a[2:] + b  # "2023-24" -> "2324"


def convert(
    matches: list[dict], lg: str, season: str, errors: list[str],
) -> list[dict]:
    """openfootball maçları → veri seti şeması (ad eşleme + sadece FT skorlu)."""
    alias = ALIAS.get(lg, {})
    passthrough = lg in PASSTHROUGH_LEAGUES
    out: list[dict] = []
    for m in matches:
        score = m.get("score") or {}
        ft = score.get("ft") if isinstance(score, dict) else None
        if not ft or len(ft) != 2:
            continue  # oynanmamış / skorsuz
        rows = []
        for raw_name in (m["team1"], m["team2"]):
            if passthrough:
                rows.append(_canon(lg, raw_name))
            elif raw_name in alias:
                rows.append(alias[raw_name])
            else:
                errors.append(f"{lg} {season}: eşlenmemiş takım adı {raw_name!r}")
                rows.append(None)
        if None in rows:
            continue
        out.append({
            "date": m["date"], "home": rows[0], "away": rows[1],
            "hg": int(ft[0]), "ag": int(ft[1]),
            "comp": lg, "season": _season_tag(season),
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="openfootball veri güncelleme")
    parser.add_argument(
        "--cache-dir", type=Path, default=REPO_ROOT / ".cache" / "openfootball",
    )
    args = parser.parse_args()

    existing = json.loads(BACKEND_JSON.read_text(encoding="utf-8"))
    # Önceki koşulardan kalan normalize edilmemiş adları düzelt (idempotent).
    for m in existing:
        m["home"] = _canon(m["comp"], m["home"])
        m["away"] = _canon(m["comp"], m["away"])
    seen = {(m["comp"], m["date"], m["home"], m["away"]) for m in existing}
    print(f"Mevcut: {len(existing)} maç (son: {max(m['date'] for m in existing)})")

    errors: list[str] = []
    added = 0
    for season, lg in SEASONS:
        matches = _fetch(season, lg, args.cache_dir)
        if matches is None:
            continue
        rows = convert(matches, lg, season, errors)
        fresh = [
            r for r in rows
            if (r["comp"], r["date"], r["home"], r["away"]) not in seen
        ]
        for r in fresh:
            seen.add((r["comp"], r["date"], r["home"], r["away"]))
        existing.extend(fresh)
        added += len(fresh)
        print(f"  {season} {lg}: {len(rows)} skorlu, {len(fresh)} yeni")

    if errors:
        print("\nHATA — eşlenmemiş takım adları (ALIAS tablosunu genişlet):")
        for e in sorted(set(errors)):
            print("  ·", e)
        return 1

    existing.sort(key=lambda m: (m["date"], m["comp"], m["home"]))
    payload = json.dumps(existing, ensure_ascii=False, separators=(",", ":"))
    BACKEND_JSON.write_text(payload, encoding="utf-8")
    FRONTEND_JSON.write_text(payload, encoding="utf-8")
    print(f"\nToplam: {len(existing)} maç (+{added}) → iki kopya da yazıldı")
    print(f"  {BACKEND_JSON.relative_to(REPO_ROOT)}")
    print(f"  {FRONTEND_JSON.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
