"""Walk-forward Maher/Dixon-Coles takım gücü modeli + out-of-sample kalibrasyon.

`frontend/src/lib/calibration.ts` v2'nin birebir Python portu. Üç katman:

1. DERİN MODEL: takım başına ayrı HÜCUM/SAVUNMA gücü (bivariate Poisson +
   Dixon-Coles τ düşük-skor düzeltmesi). Online (walk-forward) öğrenilir;
   güç güncellemesi gol ile isabetli-şut xG-proxy'sinin harmanına dayanır.
2. OUT-OF-SAMPLE: hiperparametreler SADECE train sezonlarında (2017-2022)
   ayarlandı; manşet metrikler görülmemiş 2022-23 test sezonunda raporlanır.
3. BELİRSİZLİK: seeded-PRNG bootstrap ile %95 güven aralıkları.

Her tahmin maçtan ÖNCE, sadece o ana kadarki bilgiyle yapılır (sızıntı yok).
Saf/deterministik — random modülü YOK (mulberry32 portu, frontend ile aynı
tohum). Engine kuralı: veri parametre olarak gelir; DB/dosya erişimi caller'da
(`app/data/backtest_results.py`).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any, TypedDict

from app.engine.predict.compute import _dixon_coles_tau

ENGINE_NAME = "engine.strength"
ENGINE_VERSION = "1"

# Train/test sınırı: bu tarihten itibaren = görülmemiş test (2022-23 sezonu).
SPLIT = "2022-07-01"
# Hiperparametreler — SADECE train (2017-2022) log-loss'una göre seçildi
# (frontend calibration.ts ile aynı değerler; tek kaynak artık burası).
LR = 0.03  # hücum/savunma online öğrenme hızı
RHO = -0.08  # Dixon-Coles düşük-skor korelasyonu
WD = 0.0  # ağırlık sönümü (regularizasyon)
BLEND = 0.4  # güç güncellemesinde gol ağırlığı (kalan: SoT xG-proxy)
# Ensemble: Atak/Defans-DC %70 + eski Elo %30 — train Brier'ına göre seçildi.
ENS_W = 0.7
# Eski Elo modeli sabitleri (karşılaştırma bileşeni).
ELO_HA = 65.0
ELO_EPG = 150.0
ELO_AVG = 2.7
ELO_K = 20.0
ELO_SHRINK = 0.8

_MAX_GOALS = 8  # skor gridi 0..8 (frontend ile aynı)
_BOOT_B = 600
_BOOT_SEED = 20260613

LEAGUE_LABEL: dict[str, str] = {
    "en.1": "Premier League",
    "es.1": "La Liga",
    "de.1": "Bundesliga",
    "it.1": "Serie A",
    "fr.1": "Ligue 1",
    "tr.1": "Süper Lig",
}


def league_label(comp: str) -> str:
    return LEAGUE_LABEL.get(comp, comp)


class MatchResult(TypedDict, total=False):
    """Ham maç satırı — app/data/static/match_results.json şeması."""

    date: str
    home: str
    away: str
    hg: int
    ag: int
    comp: str
    hst: int  # isabetli şut (ev) — opsiyonel
    ast: int  # isabetli şut (dep) — opsiyonel


def _round(x: float, d: int = 4) -> float:
    return round(x, d)


def _outcome_of(hg: int, ag: int) -> str:
    return "H" if hg > ag else ("D" if hg == ag else "A")


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _pois_vec(lam: float, kmax: int = _MAX_GOALS) -> list[float]:
    """[P(X=0)..P(X=kmax)] — tek exp ile artımlı (performans: grid başına 1 çağrı)."""
    out = [math.exp(-lam)]
    for k in range(1, kmax + 1):
        out.append(out[-1] * lam / k)
    return out


def _probs(lam_h: float, lam_a: float, rho: float) -> tuple[float, float, float]:
    """λ_ev, λ_dep → (P_1, P_X, P_2), Dixon-Coles düzeltmeli, normalize."""
    ph_v = _pois_vec(lam_h)
    pa_v = _pois_vec(lam_a)
    p_h = p_d = p_a = 0.0
    for i in range(_MAX_GOALS + 1):
        for j in range(_MAX_GOALS + 1):
            p = ph_v[i] * pa_v[j]
            if i <= 1 and j <= 1:
                p *= max(1e-4, _dixon_coles_tau(i, j, lam_h, lam_a, rho))
            if i > j:
                p_h += p
            elif i == j:
                p_d += p
            else:
                p_a += p
    s = (p_h + p_d + p_a) or 1.0
    return p_h / s, p_d / s, p_a / s


def _goal_markets(lam_h: float, lam_a: float, rho: float) -> tuple[float, float]:
    """Aynı λ'lardan (P(toplam≥3), P(karşılıklı gol))."""
    ph_v = _pois_vec(lam_h)
    pa_v = _pois_vec(lam_a)
    total = over = btts = 0.0
    cells: list[tuple[int, int, float]] = []
    for i in range(_MAX_GOALS + 1):
        for j in range(_MAX_GOALS + 1):
            p = ph_v[i] * pa_v[j]
            if i <= 1 and j <= 1:
                p *= max(1e-4, _dixon_coles_tau(i, j, lam_h, lam_a, rho))
            cells.append((i, j, p))
            total += p
    for i, j, p in cells:
        pn = p / total
        if i + j >= 3:
            over += pn
        if i >= 1 and j >= 1:
            btts += pn
    return over, btts


_OUT = ("H", "D", "A")


def _to_row(m: MatchResult, p: tuple[float, float, float]) -> dict[str, Any]:
    idx = 0 if (p[0] >= p[1] and p[0] >= p[2]) else (1 if p[1] >= p[2] else 2)
    actual = _outcome_of(m["hg"], m["ag"])
    return {
        "date": m["date"], "home": m["home"], "away": m["away"], "comp": m["comp"],
        "pH": _round(p[0]), "pD": _round(p[1]), "pA": _round(p[2]),
        "pick": _OUT[idx], "conf": _round(p[idx]),
        "actual": actual, "scoreline": f"{m['hg']}-{m['ag']}",
        "hit": _OUT[idx] == actual,
    }


def _sorted_matches(matches: Sequence[MatchResult]) -> list[MatchResult]:
    return sorted(matches, key=lambda m: m["date"])


def run_core(
    matches: Sequence[MatchResult], blend: float = BLEND,
) -> dict[str, Any]:
    """Derin model çekirdeği — walk-forward hücum/savunma öğrenimi.

    Döndürür: {"ledger", "atk", "def", "muH", "muA", "conv"}.
    """
    ms = _sorted_matches(matches)
    # Lig log-ortalama gol oranları + SoT→gol dönüşümü (SADECE train'den).
    lg: dict[str, list[float]] = {}
    tot_goals = 0.0
    tot_sot = 0.0
    for m in ms:
        if m["date"] < SPLIT:
            g = lg.setdefault(m["comp"], [0.0, 0.0, 0.0])
            g[0] += m["hg"]
            g[1] += m["ag"]
            g[2] += 1
            tot_goals += m["hg"] + m["ag"]
            tot_sot += (m.get("hst") or 0) + (m.get("ast") or 0)
    mu_h = {c: math.log(g[0] / g[2]) for c, g in lg.items() if g[2] and g[0]}
    mu_a = {c: math.log(g[1] / g[2]) for c, g in lg.items() if g[2] and g[1]}
    conv = (tot_goals / tot_sot) if tot_sot else 0.31

    atk: dict[str, float] = {}
    dfn: dict[str, float] = {}
    ledger: list[dict[str, Any]] = []
    for m in ms:
        k_h = m["comp"] + "|" + m["home"]
        k_a = m["comp"] + "|" + m["away"]
        a_h = atk.setdefault(k_h, 0.0)
        a_a = atk.setdefault(k_a, 0.0)
        d_h = dfn.setdefault(k_h, 0.0)
        d_a = dfn.setdefault(k_a, 0.0)
        lam_h = _clamp(math.exp(mu_h.get(m["comp"], 0.3) + a_h - d_a), 0.05, 7)
        lam_a = _clamp(math.exp(mu_a.get(m["comp"], 0.1) + a_a - d_h), 0.05, 7)
        row = _to_row(m, _probs(lam_h, lam_a, RHO))
        over, btts = _goal_markets(lam_h, lam_a, RHO)
        row["pOver"] = _round(over)
        row["pBTTS"] = _round(btts)
        row["yOver"] = 1 if m["hg"] + m["ag"] >= 3 else 0
        row["yBTTS"] = 1 if m["hg"] >= 1 and m["ag"] >= 1 else 0
        ledger.append(row)
        # Gözlem = gol ile şut-tabanlı xG-proxy harmanı (şut daha az gürültülü).
        # Şut verisi YOKSA (openfootball 2023+ satırları) saf gol kullanılır —
        # 0-şutla harmanlamak gücü sistematik aşağı çekerdi. (hst=0 geçerli
        # veridir, sadece alanın hiç olmaması düşürür.)
        h_sot = m.get("hst")
        a_sot = m.get("ast")
        obs_h = (
            blend * m["hg"] + (1 - blend) * h_sot * conv
            if h_sot is not None else float(m["hg"])
        )
        obs_a = (
            blend * m["ag"] + (1 - blend) * a_sot * conv
            if a_sot is not None else float(m["ag"])
        )
        g_h = obs_h - lam_h
        g_a = obs_a - lam_a
        atk[k_h] = a_h + LR * g_h - LR * WD * a_h
        dfn[k_a] = d_a - LR * g_h - LR * WD * d_a
        atk[k_a] = a_a + LR * g_a - LR * WD * a_a
        dfn[k_h] = d_h - LR * g_a - LR * WD * d_h
    return {
        "ledger": ledger, "atk": atk, "def": dfn,
        "muH": mu_h, "muA": mu_a, "conv": conv,
    }


def run_elo(matches: Sequence[MatchResult]) -> list[dict[str, Any]]:
    """ESKİ tek-güç Elo modeli (karşılaştırma bileşeni) — düz Poisson, DC yok."""
    ms = _sorted_matches(matches)
    r: dict[str, float] = {}
    ledger: list[dict[str, Any]] = []
    for m in ms:
        k_h = m["comp"] + "|" + m["home"]
        k_a = m["comp"] + "|" + m["away"]
        r_h = r.setdefault(k_h, 1500.0)
        r_a = r.setdefault(k_a, 1500.0)
        drift = r_h + ELO_HA - r_a
        sup = (drift * ELO_SHRINK) / ELO_EPG
        lam_h = _clamp((ELO_AVG + sup) / 2, 0.15, 6)
        lam_a = _clamp((ELO_AVG - sup) / 2, 0.15, 6)
        ph_v = _pois_vec(lam_h)
        pa_v = _pois_vec(lam_a)
        p_h = p_d = p_a = 0.0
        for i in range(_MAX_GOALS + 1):
            for j in range(_MAX_GOALS + 1):
                p = ph_v[i] * pa_v[j]
                if i > j:
                    p_h += p
                elif i == j:
                    p_d += p
                else:
                    p_a += p
        s = (p_h + p_d + p_a) or 1.0
        ledger.append(_to_row(m, (p_h / s, p_d / s, p_a / s)))
        s_h = 1.0 if m["hg"] > m["ag"] else (0.5 if m["hg"] == m["ag"] else 0.0)
        e_h = 1 / (1 + 10 ** (-drift / 400))
        mov = math.log(abs(m["hg"] - m["ag"]) + 1)
        d = ELO_K * mov * (s_h - e_h)
        r[k_h] = r_h + d
        r[k_a] = r_a - d
    return ledger


def _final_elo_ratings(matches: Sequence[MatchResult]) -> dict[str, float]:
    """Elo'nun öğrendiği NİHAİ rating'ler (canlı ensemble için)."""
    r: dict[str, float] = {}
    for m in _sorted_matches(matches):
        k_h = m["comp"] + "|" + m["home"]
        k_a = m["comp"] + "|" + m["away"]
        r_h = r.setdefault(k_h, 1500.0)
        r_a = r.setdefault(k_a, 1500.0)
        drift = r_h + ELO_HA - r_a
        s_h = 1.0 if m["hg"] > m["ag"] else (0.5 if m["hg"] == m["ag"] else 0.0)
        e_h = 1 / (1 + 10 ** (-drift / 400))
        mov = math.log(abs(m["hg"] - m["ag"]) + 1)
        d = ELO_K * mov * (s_h - e_h)
        r[k_h] = r_h + d
        r[k_a] = r_a - d
    return r


def _blend_ledgers(
    a: list[dict[str, Any]], b: list[dict[str, Any]], w_a: float,
) -> list[dict[str, Any]]:
    """İki defteri (aynı maç sırası) olasılık düzeyinde harmanlar."""
    w_b = 1 - w_a
    out: list[dict[str, Any]] = []
    for r, o in zip(a, b, strict=True):
        p_h = w_a * r["pH"] + w_b * o["pH"]
        p_d = w_a * r["pD"] + w_b * o["pD"]
        p_a = w_a * r["pA"] + w_b * o["pA"]
        idx = 0 if (p_h >= p_d and p_h >= p_a) else (1 if p_d >= p_a else 2)
        ps = (p_h, p_d, p_a)
        merged = dict(r)
        merged.update({
            "pH": _round(p_h), "pD": _round(p_d), "pA": _round(p_a),
            "pick": _OUT[idx], "conf": _round(ps[idx]),
            "hit": _OUT[idx] == r["actual"],
        })
        # Gol marketleri: karşı defterde görüş yoksa (Elo market üretmez)
        # mevcut görüş AYNEN taşınır — 0 ile harmanlamak olasılığı 0.7×
        # küçültüp market kalibrasyonunu bozuyordu.
        if r.get("pOver") is not None:
            o_over = o["pOver"] if o.get("pOver") is not None else r["pOver"]
            merged["pOver"] = _round(w_a * r["pOver"] + w_b * o_over)
        if r.get("pBTTS") is not None:
            o_btts = o["pBTTS"] if o.get("pBTTS") is not None else r["pBTTS"]
            merged["pBTTS"] = _round(w_a * r["pBTTS"] + w_b * o_btts)
        out.append(merged)
    return out


# ── metrikler ────────────────────────────────────────────────────────────────

def _metrics_of(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    n = len(rows) or 1
    cnt = {"H": 0, "D": 0, "A": 0}
    for r in rows:
        cnt[r["actual"]] += 1
    base = {k: v / n for k, v in cnt.items()}
    eps = 1e-9
    acc = brier = ll = b_b = b_l = 0.0
    for r in rows:
        if r["hit"]:
            acc += 1
        y = {"H": 0.0, "D": 0.0, "A": 0.0}
        y[r["actual"]] = 1.0
        brier += (r["pH"] - y["H"]) ** 2 + (r["pD"] - y["D"]) ** 2 + (r["pA"] - y["A"]) ** 2
        b_b += (base["H"] - y["H"]) ** 2 + (base["D"] - y["D"]) ** 2 + (base["A"] - y["A"]) ** 2
        p_act = {"H": r["pH"], "D": r["pD"], "A": r["pA"]}[r["actual"]]
        ll += -math.log(_clamp(p_act, eps, 1))
        b_l += -math.log(_clamp(base[r["actual"]], eps, 1))
    acc /= n
    brier /= n
    ll /= n
    b_b /= n
    b_l /= n
    # ECE — 3 sınıf × n olasılık çiftini 10 kovaya böl.
    nb = 10
    eb = [[0.0, 0.0, 0] for _ in range(nb)]
    for r in rows:
        for p, yy in (
            (r["pH"], 1 if r["actual"] == "H" else 0),
            (r["pD"], 1 if r["actual"] == "D" else 0),
            (r["pA"], 1 if r["actual"] == "A" else 0),
        ):
            bi = min(nb - 1, int(p * nb))
            eb[bi][0] += p
            eb[bi][1] += yy
            eb[bi][2] += 1
    ece = 0.0
    tot = n * 3
    for sp, sy, c in eb:
        if c:
            ece += (c / tot) * abs(sp / c - sy / c)
    return {
        "name": name, "accuracy": acc, "brier": brier, "logLoss": ll,
        "baselineBrier": b_b, "baselineLogLoss": b_l,
        "brierSkill": (1 - brier / b_b) if b_b else 0.0, "ece": ece,
        "baseRates": {"h": base["H"], "d": base["D"], "a": base["A"]},
    }


def _mulberry32(seed: int) -> Callable[[], float]:
    """Seeded PRNG — frontend mulberry32'nin birebir portu (deterministik)."""
    state = seed & 0xFFFFFFFF

    def rng() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = ((t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng


def _bootstrap_ci(rows: list[dict[str, Any]], b: int = _BOOT_B) -> dict[str, list[float]]:
    """Bootstrap %95 güven aralıkları (test setini yeniden örnekle)."""
    rng = _mulberry32(_BOOT_SEED)
    accs: list[float] = []
    bris: list[float] = []
    lls: list[float] = []
    eces: list[float] = []
    n = len(rows)
    for _ in range(b):
        s = [rows[int(rng() * n)] for _ in range(n)]
        m = _metrics_of(s, "")
        accs.append(m["accuracy"])
        bris.append(m["brier"])
        lls.append(m["logLoss"])
        eces.append(m["ece"])

    def ci(arr: list[float]) -> list[float]:
        a = sorted(arr)
        return [_round(a[int(b * 0.025)]), _round(a[int(b * 0.975)])]

    return {"accuracy": ci(accs), "brier": ci(bris), "logLoss": ci(lls), "ece": ci(eces)}


def _binary_market(
    rows: list[dict[str, Any]], key: str, name: str,
    p_key: str, y_key: str, note: str,
) -> dict[str, Any]:
    """İkili market (üst/alt, btts) kalibrasyonu → kendi güven rakamı."""
    n = len(rows) or 1
    acc = brier = base_sum = 0.0
    for r in rows:
        p_raw = r.get(p_key)
        p = float(p_raw) if p_raw is not None else 0.5
        y = int(r.get(y_key) or 0)
        if (1 if p >= 0.5 else 0) == y:
            acc += 1
        brier += (p - y) ** 2
        base_sum += y
    base_rate = base_sum / n
    b_brier = 0.0
    for r in rows:
        y = int(r.get(y_key) or 0)
        b_brier += (base_rate - y) ** 2
    acc /= n
    brier /= n
    b_brier /= n
    brier_skill = (1 - brier / b_brier) if b_brier else 0.0
    nb = 10
    eb = [[0.0, 0.0, 0] for _ in range(nb)]
    for r in rows:
        p_raw = r.get(p_key)
        p = float(p_raw) if p_raw is not None else 0.5
        y = int(r.get(y_key) or 0)
        bi = min(nb - 1, int(p * nb))
        eb[bi][0] += p
        eb[bi][1] += y
        eb[bi][2] += 1
    ece = 0.0
    for sp, sy, c in eb:
        if c:
            ece += (c / n) * abs(sp / c - sy / c)
    calib_comp = 1 - min(ece / 0.10, 1)
    skill_comp = _clamp(brier_skill / 0.12, 0, 1)
    trust = round(100 * (0.6 * calib_comp + 0.4 * skill_comp))
    return {
        "key": key, "name": name, "status": "validated", "trust": trust,
        "accuracy": _round(acc), "ece": _round(ece),
        "brierSkill": _round(brier_skill), "baseRate": _round(base_rate, 3),
        "n": n, "note": note,
    }


def _reliability_bins(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges = [0.33, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0001]
    out: list[dict[str, Any]] = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        in_b = [r for r in rows if lo <= r["conf"] < hi]
        if not in_b:
            continue
        out.append({
            "lo": lo, "hi": min(1.0, hi),
            "predicted": _round(sum(r["conf"] for r in in_b) / len(in_b)),
            "actual": _round(sum(1 for r in in_b if r["hit"]) / len(in_b)),
            "count": len(in_b),
        })
    return out


def _slim(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": m["name"], "accuracy": _round(m["accuracy"]),
        "brier": _round(m["brier"]), "logLoss": _round(m["logLoss"]),
        "baselineBrier": _round(m["baselineBrier"]),
        "baselineLogLoss": _round(m["baselineLogLoss"]),
        "brierSkill": _round(m["brierSkill"]), "ece": _round(m["ece"]),
    }


def compute_calibration_report(matches: Sequence[MatchResult]) -> dict[str, Any]:
    """Tam kalibrasyon raporu — frontend CalibrationReport şemasıyla aynı JSON."""
    ad_full = run_core(matches)["ledger"]
    elo_full = run_elo(matches)
    ens_full = _blend_ledgers(ad_full, elo_full, ENS_W)
    test = [r for r in ens_full if r["date"] >= SPLIT]
    ad_test = [r for r in ad_full if r["date"] >= SPLIT]
    elo_test = [r for r in elo_full if r["date"] >= SPLIT]
    train_matches = len(ens_full) - len(test)

    m = _metrics_of(test, "Ensemble (Atak/Defans·xG·DC %70 + Elo %30)")
    g = _metrics_of(ad_test, "Atak/Defans + Şut(xG) + Dixon-Coles (bileşen)")
    e = _metrics_of(elo_test, "Elo tek güç (bileşen)")
    ci = _bootstrap_ci(test) if test else {
        "accuracy": [0, 0], "brier": [0, 0], "logLoss": [0, 0], "ece": [0, 0],
    }

    # Güven Skoru: kalibrasyon (ECE düşük) + beceri (baseline'ı geçmek).
    calib_comp = 1 - min(m["ece"] / 0.12, 1)
    skill_comp = _clamp(m["brierSkill"] / 0.15, 0, 1)
    trust = round(100 * (0.6 * calib_comp + 0.4 * skill_comp))

    bc: dict[str, list[int]] = {}
    for r in test:
        c = bc.setdefault(r["comp"], [0, 0])
        c[0] += 1
        if r["hit"]:
            c[1] += 1
    by_comp: list[dict[str, Any]] = [
        {"comp": league_label(comp), "matches": v[0],
         "accuracy": _round(v[1] / v[0], 3)}
        for comp, v in sorted(bc.items(), key=lambda kv: -kv[1][0])
    ]

    # Test penceresi etiketi veriyle büyür: son test yılına göre "2022-26" gibi.
    last_test = max((r["date"] for r in test), default="")
    split_season = (
        f"2022-{int(last_test[:4]) % 100:02d}" if last_test else "2022-23"
    )

    return {
        "matches": len(test), "trainMatches": train_matches,
        "splitSeason": split_season,
        "accuracy": _round(m["accuracy"]), "brier": _round(m["brier"]),
        "logLoss": _round(m["logLoss"]),
        "baselineBrier": _round(m["baselineBrier"]),
        "baselineLogLoss": _round(m["baselineLogLoss"]),
        "brierSkill": _round(m["brierSkill"]), "ece": _round(m["ece"]),
        "trust": trust, "ci": ci, "bins": _reliability_bins(test),
        "byComp": by_comp,
        "baseRates": {
            "h": _round(m["baseRates"]["h"], 3),
            "d": _round(m["baseRates"]["d"], 3),
            "a": _round(m["baseRates"]["a"], 3),
        },
        "sample": list(reversed(test[-14:])),
        "models": [_slim(m), _slim(g), _slim(e)],
        "markets": [
            {
                "key": "result", "name": "Maç Sonucu (1/X/2)",
                "status": "validated", "trust": trust,
                "accuracy": _round(m["accuracy"]), "ece": _round(m["ece"]),
                "brierSkill": _round(m["brierSkill"]),
                "baseRate": None, "n": len(test),
                "note": "Hangi takım kazanır / berabere — en güçlü katman.",
            },
            _binary_market(
                test, "over", "Çok Gollü Maç (Üst/Alt 2.5)", "pOver", "yOver",
                "Maçta 3+ gol olur mu — orta güç.",
            ),
            _binary_market(
                test, "btts", "Karşılıklı Gol", "pBTTS", "yBTTS",
                "İki takım da gol atar mı — zayıf, tahminden az iyi.",
            ),
            {
                "key": "lineup", "name": "Kadro / Rotasyon Kararı",
                "status": "pending", "trust": 0, "accuracy": 0, "ece": 0,
                "brierSkill": 0, "baseRate": None, "n": 0,
                "note": "Doğrulanamaz: kimin gerçekten oynadığı + maç sonucu "
                        "eşli veri gerekir (Süper Lig kadro+sonuç akışı).",
            },
            {
                "key": "injury", "name": "Sakatlık Riski",
                "status": "pending", "trust": 0, "accuracy": 0, "ece": 0,
                "brierSkill": 0, "baseRate": None, "n": 0,
                "note": "Doğrulanamaz: gerçek sakatlık zaman serisi + "
                        "yük/giyilebilir veri gerekir (Sportmonks haberi yetmez).",
            },
        ],
        "params": {"lr": LR, "rho": RHO, "wd": WD},
    }


def predictor_data(matches: Sequence[MatchResult]) -> list[dict[str, Any]]:
    """Modelin öğrendiği NİHAİ takım güçleri (lig bazında) — canlı tahmin için.

    Sadece son sezonda (SPLIT sonrası) oynayan takımlar (güncel güç).
    """
    st = run_core(matches)
    elo = _final_elo_ratings(matches)
    last_season: dict[str, set[str]] = {}
    for m in matches:
        if m["date"] >= SPLIT:
            s = last_season.setdefault(m["comp"], set())
            s.add(m["home"])
            s.add(m["away"])
    out: list[dict[str, Any]] = []
    for comp, names in last_season.items():
        teams = sorted(
            (
                {
                    "name": name,
                    "atk": _round(st["atk"].get(comp + "|" + name, 0.0), 3),
                    "def": _round(st["def"].get(comp + "|" + name, 0.0), 3),
                    "rating": round(
                        (st["atk"].get(comp + "|" + name, 0.0)
                         + st["def"].get(comp + "|" + name, 0.0)) * 100
                    ),
                    "elo": round(elo.get(comp + "|" + name, 1500.0)),
                }
                for name in names
            ),
            key=lambda t: -t["rating"],
        )
        out.append({
            "comp": comp, "label": league_label(comp),
            "muH": _round(st["muH"].get(comp, 0.0)),
            "muA": _round(st["muA"].get(comp, 0.0)),
            "rho": RHO, "ensW": ENS_W,
            "eloHA": ELO_HA, "eloEPG": ELO_EPG, "eloAvg": ELO_AVG,
            "teams": teams,
        })
    return sorted(out, key=lambda x: x["label"])
