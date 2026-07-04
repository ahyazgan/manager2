"use client";

/**
 * EmptyState — boş-durum standardı (usability sprint).
 *
 * Verisi olmayan sayfa boş tablo / NaN / sessiz spinner yerine bunu gösterir:
 * ne eksik + veri NASIL gelir + tek tıkla oraya götüren CTA. Varsayılan CTA
 * /onboarding (veri kurulum sihirbazı).
 *
 * Kullanım:
 *   <EmptyState
 *     title="Henüz maç verisi yok"
 *     description="Süper Lig verisini çekmek için veri kurulumunu çalıştırın."
 *   />
 */

import * as React from "react";
import Link from "next/link";

export interface EmptyStateProps {
  /** Tabler icon adı (ti-*). Default: ti-database-off */
  icon?: string;
  title: string;
  /** "Veri nasıl gelir" açıklaması — kullanıcıya sonraki adımı söyler. */
  description?: React.ReactNode;
  /** CTA hedefi. Default: /onboarding. null → CTA gizle. */
  ctaHref?: string | null;
  ctaLabel?: string;
  /** Ek aksiyonlar / ikincil linkler. */
  children?: React.ReactNode;
}

const wrap: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 10,
  padding: "36px 24px",
  textAlign: "center",
  border: "1px dashed var(--line, #d8dee6)",
  borderRadius: 12,
  background: "var(--panel, #fff)",
};

const btn: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  marginTop: 4,
  padding: "8px 16px",
  borderRadius: 8,
  background: "var(--accent, #e11d48)",
  color: "#fff",
  fontSize: 13,
  fontWeight: 600,
  textDecoration: "none",
};

export function EmptyState({
  icon = "ti-database-off",
  title,
  description,
  ctaHref = "/onboarding",
  ctaLabel = "Veri kurulumunu başlat",
  children,
}: EmptyStateProps) {
  return (
    <div style={wrap} role="status">
      <i className={`ti ${icon}`} style={{ fontSize: 30, opacity: 0.4 }} aria-hidden="true" />
      <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--ink, #1a2233)" }}>{title}</div>
      {description && (
        <div style={{ fontSize: 12.5, opacity: 0.72, maxWidth: 460, lineHeight: 1.55 }}>
          {description}
        </div>
      )}
      {ctaHref && (
        <Link href={ctaHref} style={btn}>
          <i className="ti ti-arrow-right" aria-hidden="true" /> {ctaLabel}
        </Link>
      )}
      {children}
    </div>
  );
}
