# Full Season Engine Audit

La Liga 2018/19 üzerinde 34 maç ingest + 22 team-level engine audit.

IC = Spearman(metrik, maçın gol farkı) — concurrent validity.
CV mean≈0 metriklerde tanımsızdır ('—').

## Engine Rankings (signal → noise)

| Engine | Verdict | IC | Predictive | CV | n | Team Spread | Mean |
|---|---|---|---|---|---|---|---|
| `match_dominance` | **STRONG_SIGNAL** | +0.610 | PREDICTIVE | — | 68 | 11.746 | 0.000 |
| `tempo` | **STRONG_SIGNAL** | +0.568 | PREDICTIVE | 0.348 | 68 | 5.053 | 6.104 |
| `team_xt` | **STRONG_SIGNAL** | +0.553 | PREDICTIVE | 2.071 | 68 | 2.550 | 0.673 |
| `direct_play` | **STRONG_SIGNAL** | -0.470 | PREDICTIVE | 0.155 | 68 | 0.171 | 0.352 |
| `field_tilt` | **STRONG_SIGNAL** | +0.455 | PREDICTIVE | 0.485 | 68 | 0.556 | 0.500 |
| `final_third_entries` | **STRONG_SIGNAL** | +0.386 | PREDICTIVE | 0.335 | 68 | 51.676 | 69.868 |
| `possession_quality` | **STRONG_SIGNAL** | +0.359 | PREDICTIVE | 0.343 | 68 | 3.660 | 5.297 |
| `ppda` | **STRONG_SIGNAL** | -0.332 | PREDICTIVE | 0.623 | 68 | 6.520 | 3.104 |
| `press_resistance` | **STRONG_SIGNAL** | +0.325 | PREDICTIVE | 0.103 | 68 | 0.331 | 0.865 |
| `transition` | **STRONG_SIGNAL** | +0.251 | WEAK | 0.439 | 68 | 0.215 | 0.175 |
| `recovery_zone_heat` | **STRONG_SIGNAL** | +0.245 | WEAK | 0.430 | 68 | 0.348 | 0.198 |
| `channel_preference` | **STRONG_SIGNAL** | -0.207 | WEAK | 0.221 | 68 | 0.278 | 0.401 |
| `set_piece_zones` | **STRONG_SIGNAL** | +0.202 | WEAK | 0.752 | 68 | 4.000 | 2.750 |
| `counter_press_triggers` | **STRONG_SIGNAL** | -0.137 | NONE | 0.261 | 68 | 45.500 | 46.029 |
| `pressing_trigger` | **STRONG_SIGNAL** | +0.119 | NONE | 0.537 | 68 | 0.264 | 0.141 |
| `defensive_line` | **STRONG_SIGNAL** | +0.089 | NONE | 0.200 | 68 | 22.545 | 35.672 |
| `cross_effectiveness` | **STRONG_SIGNAL** | -0.047 | NONE | 0.476 | 68 | 21.500 | 10.353 |
| `cutback_frequency` | **STRONG_SIGNAL** | +0.002 | NONE | 0.595 | 68 | 13.500 | 4.618 |
| `defensive_duels` | **STRONG_SIGNAL** | +0.000 | NONE | 0.174 | 68 | 0.500 | 0.971 |
| `compactness` | **MODERATE** | +0.003 | NONE | 0.052 | 68 | 3.800 | 23.408 |

## Barca Sanity Check

- `field_tilt`: OK (mean 0.69 >= 0.6)
- `direct_play`: OK (mean 0.31 < 0.5)
- `tempo`: OK (mean 7.86 >= 6.0)
- `team_xt`: MISS (mean 1.35 < 1.5)
- `match_dominance`: OK (mean 3.42 >= 1.5)

## Barca Coaching Archetype Distribution

- `high_press_possession`: 26 maç
- `low_block_counter`: 4 maç
- `balanced_pragmatic`: 4 maç