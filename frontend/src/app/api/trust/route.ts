/**
 * GET /api/trust — TrustBadge'in (client) canlı güven kaynağı.
 *
 * Backend'in kalibrasyon raporundan market güvenlerini + karar defteri
 * kalibrasyon özetini derler. Backend'e ulaşılamazsa elle tutulan snapshot
 * (lib/validated-trust) döner — rozet asla boş kalmaz, sadece "snapshot"
 * kaynağıyla işaretlenir.
 */

import { NextResponse } from "next/server";
import {
  fetchBackendCalibration,
  fetchDecisionsCalibration,
} from "@/lib/backend-calibration";
import { VALIDATED_META, VALIDATED_TRUST } from "@/lib/validated-trust";

export const revalidate = 3600;

export async function GET() {
  const rep = await fetchBackendCalibration();
  if (rep) {
    const t = (k: string) => rep.markets.find((m) => m.key === k)?.trust;
    const dec = await fetchDecisionsCalibration();
    return NextResponse.json({
      source: "backend" as const,
      result: t("result") ?? VALIDATED_TRUST.result,
      over: t("over") ?? VALIDATED_TRUST.over,
      btts: t("btts") ?? VALIDATED_TRUST.btts,
      meta: { season: rep.splitSeason, matches: rep.matches },
      decisions:
        dec && dec.n_evaluated > 0
          ? {
              n: dec.overall.n,
              hitRate: dec.overall.hit_rate,
              wellCalibrated: dec.overall.well_calibrated,
            }
          : null,
    });
  }
  return NextResponse.json({
    source: "snapshot" as const,
    ...VALIDATED_TRUST,
    meta: { season: VALIDATED_META.season, matches: VALIDATED_META.matches },
    decisions: null,
  });
}
