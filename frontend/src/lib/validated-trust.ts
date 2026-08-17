/**
 * Doğrulanmış güven FALLBACK snapshot'ı — canlı kaynak artık backend
 * (GET /admin/calibration/report → /api/trust proxy → TrustBadge). Bu sabit
 * yalnızca backend'e ulaşılamadığında devreye girer; rozet asla boş kalmaz
 * ve 1.4MB sonuç JSON'u hafif sayfaların bundle'ına girmez.
 *
 * KAYNAK: app/engine/strength.compute_calibration_report() — görülmemiş
 * 2022-26 sezonları (7376 maç), top-5 Avrupa ligi + Süper Lig (openfootball
 * ile güncellenen veri seti).
 */

export const VALIDATED_TRUST = {
  result: 85,   // Maç Sonucu (1/X/2)
  over: 20,     // Üst/Alt 2.5 gol (şutsuz sezonlarda zayıf — dürüst rakam)
  btts: 29,     // Karşılıklı gol
} as const;

export const VALIDATED_META = {
  season: "2022-26",
  matches: 11159,
  method: "Ensemble: Atak/Defans·xG·Dixon-Coles (%70) + Elo (%30)",
  outOfSample: true,
} as const;

export type TrustMarket = keyof typeof VALIDATED_TRUST;
