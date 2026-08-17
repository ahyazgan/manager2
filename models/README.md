# models/ — xG model artifact'leri

Bu klasör eğitilmiş ML modellerini barındırır. `.pkl` dosyaları git'e
**girmez** (.gitignore); deploy sırasında `python -m app.engine.xg.train`
ile yeniden üretilir veya CI artifact'tan indirilir.

## xG (engine.xg)

Logistic regression — sklearn 1.4+. Feature set:
- `distance`, `angle` (görünür kale, radyan)
- `is_header`, `is_open_play`, `is_set_piece`, `is_fast_break`
- `x`, `y` (saha 0-100 normalize)

Penalty şutları model'e dahil edilmez (xG = 0.76 sabit, literatür).

## Training

```bash
# Synthetic data (test/dev — gerçek StatsBomb yok ise)
python -m app.engine.xg.train --output models/xg_v1.pkl --source synthetic --n 5000

# StatsBomb Open (ücretsiz, non-commercial) — default: La Liga 20/21 + WC 2022
# STATSBOMB_CACHE_DIR ile indirilenler diske yazılır, tekrar offline çalışır.
STATSBOMB_CACHE_DIR=.statsbomb_cache \
python -m app.engine.xg.train --output models/xg_v1.pkl --source statsbomb_open

# Farklı lig/sezon + hızlı deneme:
python -m app.engine.xg.train --output models/xg_v1.pkl --source statsbomb_open \
    --competitions 11:90,43:106 --max-matches 10
```

Çıktı:
- `models/xg_v1.pkl` — joblib bundle (model + feature_names)
- `models/xg_v1_metadata.json` — train tarihi + metrikler

## Beklenen metrikler

| Metrik | Beklenen aralık (literatür) | Synthetic'te tipik | StatsBomb Open (La Liga 20/21 + WC 2022, ~2.3k şut) |
|---|---|---|---|
| ROC-AUC | 0.75 - 0.82 | ~0.78 | 0.773 |
| Brier score | 0.07 - 0.10 | ~0.08 | 0.087 |
| Log loss | 0.30 - 0.45 | ~0.35 | 0.298 |

> Not: `class_weight="balanced"` KULLANILMAZ — AUC'yi korur ama olasılıkları
> şişirir (gerçek veride Brier 0.19'a çıkmıştı). xG çıktısı gerçek olasılıktır;
> kalibrasyon sıralamadan önce gelir.

## Veri lisansı

StatsBomb Open data **non-commercial license** altında. Production deploy
için ticari kullanım hakkı doğrulanmalı (kulüp kendi Opta lisansı üzerinden
okur). Bu repo'da yalnızca eğitim/test amaçlı.

## Deploy

CI'da otomatik retrain yok (StatsBomb veri indirimi yavaş + lisans). Manuel:
1. Geliştirme makinesinde train et
2. `models/xg_v1.pkl + xg_v1_metadata.json` artifact'ı production'a kopyala
3. `/admin/xg-model-status` ile doğrula
4. `compute_shot_xg(shot, mode='auto')` → otomatik trained mode'a geçer
