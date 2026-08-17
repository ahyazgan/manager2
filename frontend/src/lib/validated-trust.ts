/**
 * Doğrulanmış güven FALLBACK snapshot'ı — canlı kaynak artık backend
 * (GET /admin/calibration/report → /api/trust proxy → TrustBadge). Bu sabit
 * yalnızca backend'e ulaşılamadığında devreye girer; rozet asla boş kalmaz
 * ve 1.4MB sonuç JSON'u hafif sayfaların bundle'ına girmez.
 *
 * KAYNAK: app/engine/strength.compute_calibration_report() — görülmemiş
 * 2022-23 sezonu (1826 maç), top-5 Avrupa ligi. (Python portu bu sayıları
 * birebir yeniden üretir: result 76 / over 56 / btts 45.)
 */

export const VALIDATED_TRUST = {
  result: 76,   // Maç Sonucu (1/X/2)
  over: 56,     // Üst/Alt 2.5 gol
  btts: 45,     // Karşılıklı gol
} as const;

export const VALIDATED_META = {
  season: "2022-23",
  matches: 1826,
  method: "Ensemble: Atak/Defans·xG·Dixon-Coles (%70) + Elo (%30)",
  outOfSample: true,
} as const;

export type TrustMarket = keyof typeof VALIDATED_TRUST;
