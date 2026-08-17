# BACKLOG.md — Work Queue

> Claude Code pulls the next unchecked item from here automatically (see CLAUDE.md §7).
> Format per item: `- [ ] <goal>` then a `Done when:` line.
> Check off completed items with the commit SHA: `- [x] <goal>  (abc1234)`
> Append new sub-tasks here instead of stopping to ask.

-----

## Now (current session — work top to bottom, don't pause between items)

- [x] Kalibrasyon turu 1: audit metriği — CV=inf fix + Spearman IC  (19aab61)
  Done when: mean≈0 motorlar inf CV ile tepeye oturmuyor, IC kolonu raporda, saf testler yeşil, committed.
- [x] Kalibrasyon turu 1: StatsBomb Open disk cache  (d294442)
  Done when: STATSBOMB_CACHE_DIR ile indirilen JSON diske yazılıyor, tekrar çalıştırma offline, testler yeşil, committed.
- [x] Kalibrasyon turu 1: xG train --competitions/--max-matches CLI  (5376ca6)
  Done when: docstring'in vadettiği argümanlar gerçekten loader'a ulaşıyor, testli, committed.
- [x] Kalibrasyon turu 1: xG gerçek-veri eğitimi + class_weight fix  (8d11c87)
  Done when: StatsBomb Open ile eğitim uçtan uca; Brier literatür bandında (0.087), metadata commit'li.
- [x] Kalibrasyon turu 1: GET /admin/decisions/calibration  (d061d8c)
  Done when: confidence↔outcome Brier + binler genel ve decision_type bazında, testli, committed.
- [x] Kalibrasyon turu 1: Dixon-Coles ρ backend/frontend hizalama (-0.08)  (5f67df8)
  Done when: DEFAULT_RHO tek kaynak, çağıranlar import ediyor, testler güncel, committed.

### Kalibrasyon turu 2 (sonraki oturum — API'siz devam)

- [ ] full_season_audit'i cache'le yeniden koş — IC kolonlu gerçek rapor üret
  Done when: STATSBOMB_CACHE_DIR ile 34 maç audit, full_season_audit.md IC'li güncel, committed.
- [ ] xG eğitim verisini büyüt (StatsBomb Open ücretsiz sezonlar: La Liga 04-20, WC, Euro)
  Done when: ≥5k şutla eğitim, metrikler metadata'da, README tablosu güncel.
- [ ] Dixon-Coles modelini app/engine/predict'e tam taşı — frontend API'den okusun (ROADMAP Ufuk 3)
  Done when: takım atk/def güçleri backend'de öğreniliyor, frontend calibration sayfası API tüketiyor.
- [ ] validated-trust rozetlerini /admin/decisions/calibration verisine bağla
  Done when: frontend rozet gerçek karar defteri kalibrasyonunu gösteriyor, elle senkron sabit kalkıyor.

- [x] Mobile sidebar drawer  (ba07618)
  Done when: drawer opens/closes on mobile breakpoints, nav items reachable, tsc+build clean, committed.
- [x] Decisions API load-perf cache  (b2c55d6)
  Done when: /decisions endpoints cached with sane TTL, repeat-load latency measurably lower, tests cover cache hit/miss, committed.
- [x] End-to-end smoke run — La Liga match  (bc44854)
  Done when: full decision flow (live → apply → track → reconcile) runs green on a La Liga fixture in demo mode, no console errors, committed.

-----

## Next (pull these once "Now" is clear)

- [x] return_to_play engine  (ceec769)
  Done when: engine implemented in engine layer, wired api→ai→engine→domain, unit tests green, committed.
- [x] minutes_management engine  (8a9f839)
  Done when: as above.
- [x] congestion_risk engine  (a94952d)
  Done when: as above.
- [x] weekly_digest output motor  (3951a49)
  Done when: generates digest from real engine outputs, rendered in UI, tested, committed.
- [x] prematch_brief output motor  (b2083cf)
  Done when: as above.

-----

## Later (lower priority — only if Now + Next clear)

- [ ] PDF report export for scout_report_generator
- [ ] Push/email delivery for digests (currently pull-only)
- [ ] i18n scaffold for English UI
- [x] Security headers (CSP / HSTS / X-Frame-Options / X-Content-Type-Options)  (b067175)
- [x] Retry + circuit-breaker on external API calls  (868f289)
- [x] Liveness/readiness split on /health  (pre-existing — /healthz + /readyz)

-----

## Done (archive — keep last ~10 for context)

- [x] LiveDecisionDigestAgent → AI brief paneli  (5b36b56, PR #193)
- [x] Video clip stub + PWA offline shell + pilot pitch  (97d6eba, PR #192)
- [x] Audit fixes — replay commit + docs eksikleri  (dd08676, PR #191)
- [x] 3 yeni engine (hot_hand/set_piece/referee) + La Liga smoke  (d2da3d1, PR #190)
- [x] Decisions UI cilası — hub tiles + tooltipler + Karar Yansıt  (9f6646b, PR #189)
- [x] Closing/foul/star engines + frontend + ingest derinliği  (cad18bc, PR #188)

-----

## Notes / blockers (anything needing human eyes)

- (none currently)
