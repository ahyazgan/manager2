"use client";

/**
 * Hafif i18n — context + `useI18n()` + `t(key)`.
 *
 * Varsayılan dil Türkçe; sözlükte karşılığı yoksa anahtar (TR metin) aynen
 * döner — yani additive, mevcut render'ı bozmaz. Dil seçimi localStorage'da
 * tutulur. SSR-güvenli: ilk render TR, dil tercihi mount sonrası okunur.
 */

import * as React from "react";

export type Lang = "tr" | "en";

const STORAGE_KEY = "manager2_lang";

// Anahtar = TR metin (default). İngilizce karşılık `en` altında.
// Karşılığı olmayan string `t()` ile aynen döner — kademeli çeviri mümkün.
const DICT: Record<string, Partial<Record<Lang, string>>> = {
  // ── Sidebar grupları (IA v3) ──
  "Bu Hafta": { en: "This Week" },
  Takım: { en: "Team" },
  Zekâ: { en: "Intelligence" },
  Sistem: { en: "System" },
  Labs: { en: "Labs" },
  Arşiv: { en: "Archive" },
  // ── Çekirdek nav öğeleri ──
  "Kontrol Paneli": { en: "Dashboard" },
  "Rakip Analizi": { en: "Opponent Analysis" },
  "Maç Öncesi Plan": { en: "Pre-Match Plan" },
  "Canlı Maç": { en: "Live Match" },
  "Maç Değerlendirmesi": { en: "Match Review" },
  "Haftalık Rapor": { en: "Weekly Report" },
  Kadro: { en: "Squad" },
  "Fiziksel Durum": { en: "Physical Status" },
  "Yük Takibi": { en: "Load Tracking" },
  "Sakatlık & Sağlık": { en: "Injuries & Health" },
  "AI Asistan": { en: "AI Assistant" },
  "Komuta Merkezi": { en: "Command Center" },
  "Performans Analizi": { en: "Performance Analysis" },
  Kararlar: { en: "Decisions" },
  "Veri Kurulumu": { en: "Data Setup" },
  "Sistemin Sicili": { en: "Track Record" },
  Bildirimler: { en: "Notifications" },
  Ayarlar: { en: "Settings" },
  // ── Labs ──
  "Maç Merkezi": { en: "Match Center" },
  "Taktik Tahtası": { en: "Tactics Board" },
  "Gerçek Veri Analizi": { en: "Real Data Analysis" },
  "Maç Öncesi Modu": { en: "Pre-Match Mode" },
  "Maç Modu": { en: "Match Mode" },
  "Devre Arası Modu": { en: "Halftime Mode" },
  "Teknik Direktör": { en: "Head Coach" },
  "Antrenman Odağı": { en: "Training Focus" },
  "Antrenman Planı": { en: "Training Plan" },
  "Maç-içi Karar": { en: "In-Match Decisions" },
  "Karar Takip": { en: "Decision Tracking" },
  "Sportmonks Planı": { en: "Sportmonks Plan" },
  // ── Arşiv ──
  "Oyuncu Keşif": { en: "Player Discovery" },
  "Skaut Raporları": { en: "Scout Reports" },
  Transfer: { en: "Transfers" },
  Fikstür: { en: "Fixtures" },
  "Kafa Kafaya": { en: "Head to Head" },
  Ligler: { en: "Leagues" },
  Takımlar: { en: "Teams" },
  "Sözleşmeler": { en: "Contracts" },
  "TD Performansı": { en: "Manager Rating" },
  "Veri Girişi & Batarya": { en: "Data Entry & Battery" },
  "Test Hesaplayıcı": { en: "Test Calculator" },
  Yoklama: { en: "Attendance" },
  "Erişim Denetimi": { en: "Access Audit" },
  // ── Mobil alt bar ──
  Portal: { en: "Portal" },
  Perf: { en: "Perf" },
  Maç: { en: "Match" },
  Scout: { en: "Scout" },
  // ── Genel ──
  Çıkış: { en: "Log out" },
  Sezon: { en: "Season" },
  "Giriş yap": { en: "Sign in" },
  Dil: { en: "Language" },
};

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = React.createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = React.useState<Lang>("tr");

  // Dil tercihini mount sonrası oku (SSR uyumu: ilk render her zaman TR).
  React.useEffect(() => {
    const saved = typeof window !== "undefined"
      ? window.localStorage.getItem(STORAGE_KEY)
      : null;
    if (saved === "tr" || saved === "en") {
      setLangState(saved);
    }
  }, []);

  const setLang = React.useCallback((l: Lang) => {
    setLangState(l);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, l);
    }
  }, []);

  const t = React.useCallback(
    (key: string) => {
      if (lang === "tr") return key;
      return DICT[key]?.[lang] ?? key;
    },
    [lang],
  );

  const value = React.useMemo(
    () => ({ lang, setLang, t }),
    [lang, setLang, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = React.useContext(I18nContext);
  if (ctx === null) {
    // Provider dışında çağrılırsa güvenli no-op (TR passthrough).
    return { lang: "tr", setLang: () => {}, t: (k: string) => k };
  }
  return ctx;
}
