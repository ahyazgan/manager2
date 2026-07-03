"use client";

/**
 * LiveRecordPanel — BU kurulumun canlı tahmin sicili (usability sprint).
 *
 * /calibration'daki walk-forward rapor açık-veri benchmark'ıdır; bu panel ise
 * deploy'un KENDİ tahminlerinin gerçekleşen maçlarla uzlaştırılmış (reconciled)
 * sicilini gösterir: GET /admin/predict-accuracy. Veri yoksa "sayı uydurmak"
 * yerine sicilin nasıl birikeceğini söyler.
 */

import * as React from "react";
import Link from "next/link";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { DEMO_MODE } from "@/lib/demo-mode";

interface AccuracyResp {
  value: {
    sample_count: number;
    brier_score: number | null;
    log_loss: number | null;
    expected_calibration_error: number | null;
  };
  filter?: { days: number; reconciled_count: number; valid_samples: number };
}

const strip: React.CSSProperties = {
  fontSize: 12.5,
  color: "var(--muted)",
  lineHeight: 1.6,
};

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="kpi" style={{ minWidth: 120 }}>
      <div className="kl">{label}</div>
      <div className="kn" style={{ fontSize: 20 }}>{value}</div>
      {hint && <div className="kd">{hint}</div>}
    </div>
  );
}

export function LiveRecordPanel() {
  const { data, error, isLoading } = useSWR<AccuracyResp>(
    DEMO_MODE ? null : "/admin/predict-accuracy?days=365",
    apiFetch,
    { shouldRetryOnError: false, revalidateOnFocus: false },
  );

  let body: React.ReactNode;
  if (DEMO_MODE) {
    body = (
      <div style={strip}>
        Demo modda canlı sicil kapalı. Backend bağlanıp tahminler üretilmeye ve{" "}
        <code>reconcile_predictions</code> günlük koşmaya başlayınca, bu kurulumun
        kendi maçlarındaki isabet/Brier/ECE rakamları burada birikir.
      </div>
    );
  } else if (isLoading) {
    body = <div style={strip}>Canlı sicil yükleniyor…</div>;
  } else if (error) {
    body = (
      <div style={strip}>
        Backend&apos;e ulaşılamadı — canlı sicil gösterilemiyor.{" "}
        <Link href="/onboarding">Veri kurulumu →</Link>
      </div>
    );
  } else if (!data || data.value.sample_count === 0) {
    body = (
      <div style={strip}>
        <b style={{ color: "var(--ink)" }}>Sicil birikiyor — henüz uzlaştırılmış tahmin yok.</b>{" "}
        Sıra şöyle işler: (1) lig verisi çekilir (<Link href="/onboarding">veri kurulumu</Link>),
        (2) maç öncesi tahmin üretilir, (3) maç bitince <code>reconcile_predictions</code> job&apos;u
        gerçek sonucu yazar. Birkaç maç haftasından sonra bu panelde kurulumun kendi
        Brier/ECE rakamları görünür — sahte sayı gösterilmez.
      </div>
    );
  } else {
    const v = data.value;
    const f = data.filter;
    body = (
      <>
        <div className="kpis" style={{ marginBottom: 8 }}>
          <Metric label="Örneklem" value={String(v.sample_count)} hint={`son ${f?.days ?? 365} gün`} />
          <Metric label="Brier" value={v.brier_score != null ? v.brier_score.toFixed(3) : "—"} hint="↓ iyi (3-sınıf)" />
          <Metric label="ECE" value={v.expected_calibration_error != null ? v.expected_calibration_error.toFixed(3) : "—"} hint="↓ dürüst güven" />
          <Metric label="Log loss" value={v.log_loss != null ? v.log_loss.toFixed(3) : "—"} hint="↓ iyi" />
        </div>
        <div style={strip}>
          Bu rakamlar bu kurulumun <b>kendi</b> tahminlerinin gerçekleşen maçlarla
          uzlaştırılmış sicili — açık-veri benchmark&apos;ından bağımsız.
        </div>
      </>
    );
  }

  return (
    <>
      <div className="st">
        <h2>Bu Kurulumun Canlı Sicili</h2>
        <span className="ep">GET /admin/predict-accuracy · reconciled tahminler</span>
      </div>
      <div className="rc" style={{ margin: "0 0 14px" }}>{body}</div>
    </>
  );
}
