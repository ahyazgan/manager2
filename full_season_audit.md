# Full Season Engine Audit

StatsBomb Open üzerinde 149 maç ingest + 22 team-level engine audit (La Liga 2018/19 + WC 2022 + Euro 2024).

IC = Spearman(metrik, maçın gol farkı) — concurrent validity.
CV mean≈0 metriklerde tanımsızdır ('—').

## Engine Rankings (signal → noise)

| Engine | Verdict | IC | Predictive | CV | n | Team Spread | Mean |
|---|---|---|---|---|---|---|---|
| `match_dominance` | **STRONG_SIGNAL** | +0.450 | PREDICTIVE | — | 298 | 13.840 | 0.000 |
| `team_xt` | **STRONG_SIGNAL** | +0.401 | PREDICTIVE | 5.359 | 298 | 4.199 | 0.276 |
| `field_tilt` | **STRONG_SIGNAL** | +0.310 | PREDICTIVE | 0.418 | 298 | 0.579 | 0.500 |
| `tempo` | **STRONG_SIGNAL** | +0.281 | WEAK | 0.306 | 298 | 5.525 | 5.957 |
| `press_resistance` | **STRONG_SIGNAL** | +0.271 | WEAK | 0.109 | 298 | 0.366 | 0.862 |
| `final_third_entries` | **STRONG_SIGNAL** | +0.244 | WEAK | 0.311 | 298 | 57.400 | 68.336 |
| `transition` | **STRONG_SIGNAL** | +0.230 | WEAK | 0.489 | 298 | 0.215 | 0.172 |
| `possession_quality` | **STRONG_SIGNAL** | +0.217 | WEAK | 0.280 | 298 | 3.774 | 5.616 |
| `ppda` | **STRONG_SIGNAL** | -0.206 | WEAK | 0.637 | 298 | 8.527 | 3.159 |
| `direct_play` | **STRONG_SIGNAL** | -0.195 | WEAK | 0.142 | 298 | 0.190 | 0.347 |
| `recovery_zone_heat` | **STRONG_SIGNAL** | +0.164 | WEAK | 0.390 | 298 | 0.348 | 0.224 |
| `defensive_line` | **STRONG_SIGNAL** | +0.143 | NONE | 0.191 | 298 | 24.613 | 35.983 |
| `cutback_frequency` | **STRONG_SIGNAL** | +0.117 | NONE | 0.656 | 298 | 13.500 | 4.728 |
| `channel_preference` | **STRONG_SIGNAL** | -0.112 | NONE | 0.236 | 298 | 0.278 | 0.417 |
| `pressing_trigger` | **STRONG_SIGNAL** | +0.111 | NONE | 0.508 | 298 | 0.264 | 0.157 |
| `counter_press_triggers` | **STRONG_SIGNAL** | -0.105 | NONE | 0.249 | 298 | 45.500 | 43.933 |
| `set_piece_zones` | **STRONG_SIGNAL** | +0.095 | NONE | 0.717 | 298 | 5.000 | 2.802 |
| `defensive_duels` | **STRONG_SIGNAL** | +0.005 | NONE | 0.186 | 298 | 0.500 | 0.966 |
| `cross_effectiveness` | **STRONG_SIGNAL** | +0.003 | NONE | 0.469 | 298 | 21.500 | 11.463 |
| `compactness` | **MODERATE** | +0.022 | NONE | 0.057 | 298 | 4.704 | 23.994 |

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