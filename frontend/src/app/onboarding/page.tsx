"use client";

/**
 * Veri Kurulumu (onboarding sihirbazı) — usability sprint.
 *
 * Boş DB'li yeni kullanıcının terminal/cURL görmeden dolu ekrana ulaşma yolu:
 *   1. Lig + sezon seç
 *   2. "Veriyi Çek" → POST /admin/sync-league (arka planda run_job)
 *   3. İlerleme: GET /admin/jobs poll'u + GET /admin/db-stats sayaçları
 *   4. Bitti → Kontrol Paneli'ne git
 *
 * DEMO_MODE açıkken bilgilendirir ama engellemez — sihirbaz backend'e proxy
 * üzerinden gerçek istek atar; backend fixture modundaysa sentetik veri gelir.
 */

import * as React from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { DEMO_MODE } from "@/lib/demo-mode";
import { EmptyState } from "@/components/ui";
import { ConsoleShell } from "../_console/shell";

const LEAGUES = [
  { id: 203, name: "Süper Lig (Türkiye)" },
  { id: 39, name: "Premier League (İngiltere)" },
  { id: 140, name: "La Liga (İspanya)" },
  { id: 135, name: "Serie A (İtalya)" },
  { id: 78, name: "Bundesliga (Almanya)" },
];
const SEASONS = [2026, 2025, 2024];

type Phase = "idle" | "starting" | "running" | "done" | "failed";

interface JobRow {
  id: number;
  job_name: string;
  status: string;
  error?: string | null;
  started_at: string;
}

interface DbStats {
  leagues: number;
  teams: number;
  matches: number;
  [k: string]: number;
}

const card: React.CSSProperties = {
  background: "var(--panel, #fff)",
  border: "1px solid var(--line, #d8dee6)",
  borderRadius: 12,
  padding: 20,
  maxWidth: 560,
};

const label: React.CSSProperties = { fontSize: 12.5, fontWeight: 600, opacity: 0.75 };

const select: React.CSSProperties = {
  width: "100%",
  padding: "9px 10px",
  marginTop: 4,
  borderRadius: 8,
  border: "1px solid var(--line, #d8dee6)",
  background: "var(--panel, #fff)",
  color: "var(--ink, #1a2233)",
  fontSize: 13.5,
};

const primaryBtn: React.CSSProperties = {
  padding: "10px 18px",
  borderRadius: 8,
  border: "none",
  background: "var(--accent, #e11d48)",
  color: "#fff",
  fontSize: 13.5,
  fontWeight: 700,
  cursor: "pointer",
};

function StepDot({ done, active, label: text }: { done: boolean; active: boolean; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, opacity: done || active ? 1 : 0.45 }}>
      <span
        style={{
          width: 22, height: 22, borderRadius: "50%", display: "inline-flex",
          alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
          background: done ? "var(--low, #16a34a)" : active ? "var(--accent, #e11d48)" : "var(--line, #d8dee6)",
          color: done || active ? "#fff" : "var(--ink, #1a2233)",
        }}
      >
        {done ? <i className="ti ti-check" aria-hidden="true" /> : null}
      </span>
      <span style={{ fontSize: 13, fontWeight: 600 }}>{text}</span>
    </div>
  );
}

export default function OnboardingPage() {
  const [leagueId, setLeagueId] = React.useState(203);
  const [season, setSeason] = React.useState(2025);
  const [phase, setPhase] = React.useState<Phase>("idle");
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [stats, setStats] = React.useState<DbStats | null>(null);
  const startedAtRef = React.useRef<number>(0);

  // Sync bittiğinde tabloların dolduğunu göster.
  const refreshStats = React.useCallback(async () => {
    try {
      setStats(await apiFetch<DbStats>("/admin/db-stats"));
    } catch {
      /* stats gösterilemezse akış yine tamamlanır */
    }
  }, []);

  // running fazında /admin/jobs poll'u — sync_league son koşusunun durumu.
  React.useEffect(() => {
    if (phase !== "running") return undefined;
    const t = window.setInterval(async () => {
      try {
        const jobs = await apiFetch<JobRow[]>("/admin/jobs?since_hours=1");
        const sync = (jobs ?? []).find((j) => j.job_name === "sync_league");
        if (!sync) return; // satır henüz görünmüyor olabilir
        if (sync.status === "success") {
          setPhase("done");
          void refreshStats();
        } else if (sync.status === "failed") {
          setErrorMsg(sync.error ?? "Sync başarısız — /admin/jobs'a bakın.");
          setPhase("failed");
        }
      } catch {
        /* geçici ağ hatası — poll devam */
      }
      // 5 dakikadan uzun sürdüyse kullanıcıyı bilgilendirip poll'u bırak.
      if (Date.now() - startedAtRef.current > 5 * 60_000) {
        setErrorMsg("Sync 5 dakikayı aştı — arka planda sürüyor olabilir; Ayarlar → İşler'den durumu izleyin.");
        setPhase("failed");
      }
    }, 3000);
    return () => window.clearInterval(t);
  }, [phase, refreshStats]);

  const start = async () => {
    setErrorMsg(null);
    setPhase("starting");
    startedAtRef.current = Date.now();
    try {
      const r = await apiFetch<{ status: string }>(
        `/admin/sync-league?league_id=${leagueId}&season=${season}`,
        { method: "POST" },
      );
      if (r.status === "started" || r.status === "already_running") {
        setPhase("running");
      } else {
        setErrorMsg(`Beklenmeyen yanıt: ${r.status}`);
        setPhase("failed");
      }
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Backend'e ulaşılamadı");
      setPhase("failed");
    }
  };

  const running = phase === "starting" || phase === "running";

  return (
    <ConsoleShell
      active="/onboarding"
      title="Veri Kurulumu"
      desc="Lig verisini çek, ekranları doldur — terminal gerekmez. Günlük güncelleme sonrası otomatik sürer."
    >
      {DEMO_MODE && (
        <div
          style={{
            ...card, maxWidth: 560, marginBottom: 12, borderStyle: "dashed",
            fontSize: 12.5, lineHeight: 1.55, opacity: 0.85,
          }}
        >
          <b>Demo modu açık.</b> Bu sihirbaz backend&apos;e gerçek istek atar; backend
          fixture modundaysa (API anahtarı yoksa) sentetik veri yüklenir. Gerçek
          veri için backend&apos;de <code>API_FOOTBALL_KEY</code> +{" "}
          <code>USE_FIXTURES=false</code> gerekir (bkz. README &quot;Gerçek veri&quot;).
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ ...card, display: "flex", gap: 18, flexWrap: "wrap" }}>
          <StepDot done={phase === "done" || running} active={phase === "idle"} label="1 — Lig seç" />
          <StepDot done={phase === "done"} active={running} label="2 — Veriyi çek" />
          <StepDot done={false} active={phase === "done"} label="3 — Panele git" />
        </div>

        {phase !== "done" && (
          <div style={card}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 12 }}>
              <label style={label}>
                Lig
                <select
                  style={select}
                  value={leagueId}
                  disabled={running}
                  onChange={(e) => setLeagueId(Number(e.target.value))}
                >
                  {LEAGUES.map((l) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </label>
              <label style={label}>
                Sezon
                <select
                  style={select}
                  value={season}
                  disabled={running}
                  onChange={(e) => setSeason(Number(e.target.value))}
                >
                  {SEASONS.map((s) => (
                    <option key={s} value={s}>{s}–{(s + 1) % 100}</option>
                  ))}
                </select>
              </label>
            </div>
            <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12 }}>
              <button type="button" style={{ ...primaryBtn, opacity: running ? 0.6 : 1 }} disabled={running} onClick={start}>
                {running ? "Veri çekiliyor…" : "Veriyi Çek"}
              </button>
              {running && (
                <span style={{ fontSize: 12.5, opacity: 0.7 }}>
                  <i className="ti ti-loader-2" aria-hidden="true" /> Sync arka planda koşuyor — bu sayfada bekleyin (~1-2 dk).
                </span>
              )}
            </div>
            {phase === "failed" && errorMsg && (
              <div style={{ marginTop: 12, fontSize: 12.5, color: "var(--crit, #dc2626)", lineHeight: 1.5 }}>
                <b>Olmadı:</b> {errorMsg}
                <div style={{ opacity: 0.75, marginTop: 4 }}>
                  Backend çalışıyor mu? <code>API_BASE_URL</code> doğru mu? Detay:{" "}
                  <Link href="/admin">Ayarlar → İşler</Link>.
                </div>
              </div>
            )}
          </div>
        )}

        {phase === "done" && (
          <div style={card}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>
              <i className="ti ti-circle-check" style={{ color: "var(--low, #16a34a)" }} aria-hidden="true" />{" "}
              Veri hazır
            </div>
            {stats && (
              <div style={{ display: "flex", gap: 18, fontSize: 13, marginBottom: 14 }}>
                <span><b>{stats.leagues}</b> lig</span>
                <span><b>{stats.teams}</b> takım</span>
                <span><b>{stats.matches}</b> maç</span>
              </div>
            )}
            <div style={{ fontSize: 12.5, opacity: 0.75, lineHeight: 1.55, marginBottom: 14 }}>
              Günlük sync scheduler&apos;da tanımlıysa veriler her sabah kendiliğinden
              tazelenir. Form, rating, tahmin ve rakip analizi ekranları artık dolu.
            </div>
            <Link href="/overview" style={{ ...primaryBtn, textDecoration: "none", display: "inline-block" }}>
              Kontrol Paneline git →
            </Link>
          </div>
        )}

        {phase === "idle" && (
          <EmptyState
            icon="ti-info-circle"
            title="Bu adım neden gerekli?"
            description="Analiz motorları (form, rating, tahmin, rakip analizi) maç verisiyle beslenir. İlk kurulumda seçtiğin ligin son maçları çekilir; sonrası günlük otomatik güncellenir."
            ctaHref={null}
          />
        )}
      </div>
    </ConsoleShell>
  );
}
