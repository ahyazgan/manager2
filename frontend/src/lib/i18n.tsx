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
  // Nav
  "Genel Bakış": { en: "Overview" },
  Ligler: { en: "Leagues" },
  Takımlar: { en: "Teams" },
  Kadro: { en: "Squad" },
  Maçlar: { en: "Matches" },
  Scout: { en: "Scout" },
  "Maç Planı": { en: "Match Plan" },
  Antrenman: { en: "Training" },
  "Performans Testi": { en: "Performance Test" },
  Performans: { en: "Performance" },
  "Yük Riski": { en: "Load Risk" },
  "Tıbbi Merkez": { en: "Medical" },
  "Sözleşmeler": { en: "Contracts" },
  Kararlar: { en: "Decisions" },
  "xG Analiz": { en: "xG Analysis" },
  Kalibrasyon: { en: "Calibration" },
  Asistan: { en: "Assistant" },
  Bildirimler: { en: "Notifications" },
  "Rakip Raporu": { en: "Opponent Report" },
  "TD Performansı": { en: "Manager Rating" },
  "Erişim Denetimi": { en: "Access Audit" },
  Admin: { en: "Admin" },
  // Sayfa başlıkları (ConsoleShell title — shell t() ile sarar)
  "AI Asistan": { en: "AI Assistant" },
  "Admin Paneli": { en: "Admin Panel" },
  "Antrenman Odağı": { en: "Training Focus" },
  "Antrenman Planı": { en: "Training Plan" },
  "Canlı Maç": { en: "Live Match" },
  "Canlı Veri — Sportmonks": { en: "Live Data — Sportmonks" },
  "Devre Arası Brief": { en: "Half-time Brief" },
  "Devre Arası Modu": { en: "Half-time Mode" },
  "Duran Top Rutini": { en: "Set-piece Routine" },
  "Fiziksel Durum": { en: "Physical Status" },
  "Gerçek Veri Taktik Analizi": { en: "Real-data Tactical Analysis" },
  "Haftalık Rapor": { en: "Weekly Report" },
  "Kafa Kafaya": { en: "Head to Head" },
  "Kalibrasyon & Güven": { en: "Calibration & Trust" },
  "Karar Takip": { en: "Decision Tracking" },
  "Komuta Merkezi": { en: "Command Center" },
  "Maç Değerlendirmesi": { en: "Match Review" },
  "Maç Modu": { en: "Match Mode" },
  "Maç Öncesi Modu": { en: "Pre-match Mode" },
  Maç: { en: "Match" },
  "Maç-içi Karar": { en: "In-match Decision" },
  "Oyuncu Keşif": { en: "Player Discovery" },
  "Performans Analizi": { en: "Performance Analysis" },
  "Scout — Benzerlik": { en: "Scout — Similarity" },
  "Skaut Raporları": { en: "Scout Reports" },
  "Sportmonks Bağlantı Planı": { en: "Sportmonks Integration Plan" },
  "Taktik Tahtası": { en: "Tactics Board" },
  "Taktik Trend": { en: "Tactical Trend" },
  "Teknik Direktör Brifingi": { en: "Manager Briefing" },
  "Test Hesaplayıcı": { en: "Test Calculator" },
  Transfer: { en: "Transfers" },
  Yoklama: { en: "Attendance" },
  "Yük Takibi": { en: "Load Tracking" },
  // Sık kullanılan sayfa alt-başlıkları (ConsoleShell sub)
  "Canlı maç konsolu": { en: "Live match console" },
  "Out-of-sample · derin model": { en: "Out-of-sample · deep model" },
  "Tahmin & konsollar": { en: "Predictions & consoles" },
  "Yaklaşan program": { en: "Upcoming schedule" },
  "Fikstür & Sonuçlar": { en: "Fixtures & Results" },
  "Geçmiş karşılaşmalar": { en: "Past encounters" },
  "Oyuncu listesi ve durum": { en: "Player list & status" },
  "Sakatlık & dönüş takibi": { en: "Injury & return tracking" },
  "Teknik ekip kontrol paneli": { en: "Coaching staff control panel" },
  "Tüm zeka tek ekranda": { en: "All intelligence on one screen" },
  "Lig bazlı liste": { en: "By-league list" },
  "Agent çıktıları": { en: "Agent outputs" },
  // TopBar / genel
  Çıkış: { en: "Log out" },
  Sezon: { en: "Season" },
  "Giriş yap": { en: "Sign in" },
  "Hızlı erişim": { en: "Quick access" },
  "Gösterge tablosu": { en: "Dashboard" },
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
