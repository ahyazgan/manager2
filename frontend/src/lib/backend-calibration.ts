/**
 * Backend kalibrasyon köprüsü — model artık backend'de tek kaynak
 * (app/engine/strength + GET /admin/calibration/*). Bu modül SERVER tarafında
 * backend'e ulaşmayı dener; ulaşamazsa null döner ve caller yerel hesaba
 * (lib/calibration) düşer — demo deploy backend'siz de çalışmaya devam eder.
 *
 * Env (server-only, client bundle'a girmez):
 *   BACKEND_API_URL  — örn. http://localhost:8000 (boşsa köprü kapalı)
 *   BACKEND_API_KEY  — X-API-Key değeri (backend auth açıksa)
 */

import type { CalibrationReport, LeagueRatings } from "./calibration";

const BASE = (process.env.BACKEND_API_URL || "").replace(/\/$/, "");
const KEY = process.env.BACKEND_API_KEY || "";
const TIMEOUT_MS = 5000;

async function fetchJson<T>(path: string): Promise<T | null> {
  if (!BASE) return null;
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: KEY ? { "X-API-Key": KEY } : undefined,
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Backend'in out-of-sample kalibrasyon raporu — yoksa null (yerel hesaba düş). */
export async function fetchBackendCalibration(): Promise<CalibrationReport | null> {
  return fetchJson<CalibrationReport>("/admin/calibration/report");
}

/** Backend'in öğrenilmiş takım güçleri — yoksa null. */
export async function fetchBackendPredictorData(): Promise<LeagueRatings[] | null> {
  const d = await fetchJson<{ leagues: LeagueRatings[] }>(
    "/admin/calibration/predictor-data",
  );
  return d?.leagues ?? null;
}

/** Karar defteri kalibrasyonu — GET /admin/decisions/calibration özeti. */
export interface DecisionsCalibration {
  n_evaluated: number;
  overall: {
    n: number;
    hit_rate: number;
    brier_score: number;
    mean_predicted: number;
    observed_rate: number;
    well_calibrated: boolean;
  };
  by_decision_type: Record<string, { n: number; hit_rate: number; brier_score: number; well_calibrated: boolean }>;
}

export async function fetchDecisionsCalibration(): Promise<DecisionsCalibration | null> {
  return fetchJson<DecisionsCalibration>("/admin/decisions/calibration");
}
