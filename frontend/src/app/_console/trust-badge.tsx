"use client";

/**
 * Doğrulama Rozeti — bir tahminin yanına "bu yöntem out-of-sample güven X'te
 * doğrulandı" provenance'ı koyar ve /calibration'a link verir.
 *
 * Güven rakamı CANLI kaynaktan gelir: /api/trust backend kalibrasyon
 * raporunu proxy'ler; backend yoksa lib/validated-trust snapshot'ına düşer
 * (rozet asla boş kalmaz). Karar defterinde gerçek sonuç birikmişse tooltip'e
 * "karar defteri: %X isabet (n)" eklenir.
 */

import * as React from "react";
import Link from "next/link";
import { VALIDATED_TRUST, VALIDATED_META, type TrustMarket } from "@/lib/validated-trust";

interface LiveTrust {
  source: "backend" | "snapshot";
  result: number;
  over: number;
  btts: number;
  meta: { season: string; matches: number };
  decisions: { n: number; hitRate: number; wellCalibrated: boolean } | null;
}

// Modül düzeyi tek fetch — sayfadaki her rozet aynı promise'i paylaşır.
let livePromise: Promise<LiveTrust | null> | null = null;
function loadLiveTrust(): Promise<LiveTrust | null> {
  livePromise ??= fetch("/api/trust")
    .then((r) => (r.ok ? (r.json() as Promise<LiveTrust>) : null))
    .catch(() => null);
  return livePromise;
}

const COLOR = (t: number) => (t >= 70 ? "var(--low)" : t >= 50 ? "var(--mid)" : "var(--high)");

export function TrustBadge({ market = "result", note }: { market?: TrustMarket; note?: string }) {
  const [live, setLive] = React.useState<LiveTrust | null>(null);
  React.useEffect(() => {
    let on = true;
    loadLiveTrust().then((d) => { if (on) setLive(d); });
    return () => { on = false; };
  }, []);

  const trust = live?.[market] ?? VALIDATED_TRUST[market];
  const season = live?.meta.season ?? VALIDATED_META.season;
  const matches = live?.meta.matches ?? VALIDATED_META.matches;
  const src = live?.source === "backend" ? "canlı backend kalibrasyonu" : "doğrulanmış snapshot";
  const decNote = live?.decisions
    ? ` Karar defteri: %${Math.round(live.decisions.hitRate * 100)} isabet (${live.decisions.n} karar).`
    : "";
  return (
    <Link
      href="/calibration"
      title={`Yöntem ${VALIDATED_META.method}, görülmemiş ${season} sezonunda (${matches} maç) doğrulandı — ${src}.${decNote} Detay için tıkla.`}
      style={{ display: "inline-flex", alignItems: "center", gap: 7, textDecoration: "none", background: "var(--panel3)", border: "1px solid var(--line)", borderRadius: 7, padding: "5px 9px", fontSize: 11 }}
    >
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: COLOR(trust), flexShrink: 0 }} />
      <span style={{ color: "var(--muted)" }}>
        Doğrulanmış yöntem · out-of-sample güven{" "}
        <b style={{ color: COLOR(trust), fontFamily: "JetBrains Mono" }}>{trust}</b>
        {note ? <span style={{ color: "var(--dim)" }}> · {note}</span> : null}
      </span>
      <span style={{ color: "var(--dim)", fontSize: 10 }}>kanıt →</span>
    </Link>
  );
}
