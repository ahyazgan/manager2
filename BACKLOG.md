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

### Veri turu (dış açık veri — ücretsiz kaynaklar)

- [x] Backtest verisi 2026'ya güncellendi + Süper Lig (openfootball)  (edc6c66)
  Done when: 2023-26 sezonları eşlenmiş adlarla birleşik, model şutsuz satırlarda gole düşüyor, rapor yeniden üretildi. → trust 76→83.
- [x] 6 ek lig + Süper Lig train sezonları + numpy bootstrap  (01070f5)
  Done when: 26k maç, 11 ligde out-of-sample rapor <5 sn. → trust 85, Süper Lig %55.4.
- [x] Motor audit'i çok-turnuvalı (La Liga 18/19 + WC 2022 + Euro 2024) — IC n=68→298
  Done when: full_season_audit --competitions ile koşuldu, rapor commit'li. → tempo IC +0.57→+0.28 (Barca yanlılığıymış); match_dominance +0.45 / team_xt +0.40 gerçek sinyal.

### Kalibrasyon turu 2 (sonraki oturum — API'siz devam)

- [x] full_season_audit'i cache'le yeniden koş — IC kolonlu gerçek rapor üret  (89dd187)
  Done when: STATSBOMB_CACHE_DIR ile 34 maç audit, full_season_audit.md IC'li güncel, committed.
- [x] xG eğitim verisini büyüt (StatsBomb Open ücretsiz sezonlar)  (bkz. models/xg_v1_metadata.json)
  Done when: ≥5k şutla eğitim, metrikler metadata'da, README tablosu güncel. → ~18k şut, Brier 0.078.
- [x] Dixon-Coles modelini backend'e tam taşı — frontend API'den okusun (ROADMAP Ufuk 3)  (d5ab9f8, efec2d5)
  Done when: takım atk/def güçleri backend'de öğreniliyor (app/engine/strength), frontend calibration sayfası API tüketiyor (yerel hesap fallback). → port yayımlanmış sayıları birebir üretti (76/56/45); market blend bug'ı iki tarafta düzeltildi.
- [x] validated-trust rozetlerini canlı kalibrasyon verisine bağla  (efec2d5)
  Done when: frontend rozet gerçek kalibrasyonu gösteriyor, elle senkron sabit kalkıyor. → TrustBadge /api/trust'tan canlı okuyor (backend raporu + karar defteri isabeti); snapshot sadece fallback.

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

- [x] PDF report export for scout raporu (opponent_scout)  (e0266ea)
  → GET /reports/scout/{team_id}/pdf — bölümlü A4 (brief/form/rating/h2h/sinyaller).
- [x] Push/email delivery for digests  (22920e7)
  → run_weekly_digest artık Email/Telegram/WhatsApp kanallarına kısa özet gönderiyor (best-effort).
- [x] i18n scaffold for English UI  (bkz. shell t() + DICT genişletmesi)
  → ConsoleShell başlıkları t() ile sarıldı; 47 sayfa başlığı + sık alt-başlıklar EN sözlükte; topbar TR/EN toggle zaten vardı.
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
