# backend/training

Training pipeline for the DeepShield image detector (BUILD_PLAN2 Phase 11).

| Phase | Module |
|---|---|
| 11.1 Dataset procurement | [`datasets/`](./datasets/) — see [../../docs/datasets.md](../../docs/datasets.md) |
| 11.2 Training | `dataset.py`, `train_convnext.py` (pending) |
| 11.2 Calibration | `calibrate.py` (pending) |
| 11.2 Evaluation | `eval.py` (pending) |

Run `bash datasets/procure_all.sh` to build `./data/manifest.csv`.
