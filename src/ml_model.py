"""
ResalePredictor: loads group-average statistics from training_data.json
and ensemble ML models (RF + GB) for resale value prediction.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Protocol
import joblib
from sklearn.isotonic import isotonic_regression
from src.config import (
    PARAMETRIC_MIN_SAMPLES,
    CALIBRATED_RESALE_ANCHORS,
    VINFAST_BUYBACK_GUARANTEE,
    VINFAST_FLOOR_DECAY,
    HEAVY_TAIL_ASYMPTOTE,
    HEAVY_TAIL_ASYMPTOTE_DEFAULT,
    SHRINKAGE_ALPHA,
)


class _HasPredict(Protocol):
    """Protocol for sklearn-like estimators with a predict method."""
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...

HERE = Path(__file__).parent.parent
MODELS_DIR = HERE / "data" / "models"
TRAINING_DATA_FILE = MODELS_DIR / "training_data.json"
RF_PATH = MODELS_DIR / "resale_rf.pkl"
GB_PATH = MODELS_DIR / "resale_gb.pkl"


class ResalePredictor:
    """Predicts resale percentage using group-averages and ensemble ML."""

    def __init__(self) -> None:
        self._stats: Optional[pd.DataFrame] = None
        self._real_stats: Optional[pd.DataFrame] = None
        self._rf: Optional[_HasPredict] = None
        self._gb: Optional[_HasPredict] = None
        self._feature_cols: Optional[list[str]] = None
        self._max_training_year: int = 0
        self._load()

    def _load(self) -> None:
        """Load training data, compute group stats, and load models."""
        if not TRAINING_DATA_FILE.exists():
            self._stats = pd.DataFrame()
            self._real_stats = pd.DataFrame()
            return

        with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        df = pd.DataFrame(raw)

        # Group-average statistics by (brand, segment, car_type, years)
        group_cols = ["brand", "segment", "car_type", "years"]
        self._stats = df.groupby(group_cols)["resale_pct"].mean().reset_index()
        self._stats.rename(columns={"resale_pct": "avg_resale_pct"}, inplace=True)

        # Real-only stats for the shrinkage target — training_data.json mixes
        # 2,157 synthetic (parametric-derived) rows with 764 real (bonbanh/oto)
        # rows. The synthetic rows bias several segments low (e.g. B-SUV/ICE y4
        # ~0.63 vs real ~0.80). Using real-only group means as the shrinkage
        # target pulls ML predictions toward true market retention, not the
        # contaminated average.
        real_mask = df["source"].notna() & (df["source"] != "ORIG")
        df_real = df[real_mask]
        if len(df_real) > 0:
            self._real_stats = df_real.groupby(group_cols)["resale_pct"].mean().reset_index()
            self._real_stats.rename(columns={"resale_pct": "avg_resale_pct"}, inplace=True)
        else:
            self._real_stats = pd.DataFrame()

        # Load ML models independently — a single incompatible pickle (e.g. trained
        # on a different scikit-learn version) must NOT abort the whole predictor,
        # otherwise every car silently falls back to the parametric path.
        if RF_PATH.exists():
            try:
                self._rf = joblib.load(RF_PATH)
                # Single-sample inference never benefits from loky workers.
                # Force n_jobs=1 so predict doesn't spawn worker processes —
                # those workers don't inherit the caller's warning filters and
                # emit the sklearn "delayed should be used with Parallel" config
                # warning on every TCO request (seen as 394MB log spam in the
                # exhaustive stress run). Also avoids loky spawn overhead.
                if hasattr(self._rf, "n_jobs"):
                    self._rf.n_jobs = 1
            except Exception as e:  # pragma: no cover - defensive
                print(f"[ml_model] RF model load failed: {e}")
                self._rf = None
        if GB_PATH.exists():
            try:
                self._gb = joblib.load(GB_PATH)
                # Mirror the RF guard: pin n_jobs=1 so any parallel-capable
                # estimator never spawns loky workers (which would emit the
                # benign sklearn "delayed should be used with Parallel" warning
                # and add spawn overhead on every TCO request).
                if hasattr(self._gb, "n_jobs"):
                    self._gb.n_jobs = 1
            except Exception as e:  # pragma: no cover - defensive
                print(f"[ml_model] GB model load failed: {e}")
                self._gb = None

        # Build feature columns from training data for encoding
        cats = ["brand", "segment", "car_type"]
        encoded = pd.get_dummies(df[cats], prefix=cats, drop_first=False).astype(float)
        self._feature_cols = ["years", "km_per_year", "log_price"] + list(encoded.columns)

        # Max training year — capped at 10 because years 11+ have zero or
        # vanishingly sparse training samples (≤3). Tree-based models cannot
        # extrapolate; predictions flatten or become unreliable beyond this.
        # The hard cap is min(10, actual_max) so we never exceed the ceiling
        # even if future training data extends further.
        self._max_training_year = min(10, int(df["years"].max()))

        # Per-car (group) training horizon: the last year for which the group
        # (brand, segment, car_type) has at least PARAMETRIC_MIN_SAMPLES
        # observed records. This replaces the global hard cap so a group with
        # sparse late-year data does not get ML predictions it cannot support,
        # and a dense group keeps every year it has earned.
        self._group_year_counts: dict[tuple, dict[int, int]] = {}
        grouped = df.groupby(["brand", "segment", "car_type", "years"]).size()
        for (g_brand, g_segment, g_type, g_year), count in grouped.items():
            key = (g_brand, g_segment, g_type)
            self._group_year_counts.setdefault(key, {})[int(g_year)] = int(count)
        self._group_max_year: dict[tuple, int] = {}
        for key, year_counts in self._group_year_counts.items():
            qualified = [y for y, c in year_counts.items() if c >= PARAMETRIC_MIN_SAMPLES]
            self._group_max_year[key] = max(qualified) if qualified else 0

        # Reliable max year: the last year with sufficient training samples.
        # Tree ensembles produce unreliable predictions in years with very
        # sparse data (< MIN_TRAINING_SAMPLES per year) because the model
        # cannot learn a meaningful signal from few examples.
        MIN_TRAINING_SAMPLES = 50
        year_counts = df.groupby("years").size()
        reliable_years = year_counts[year_counts >= MIN_TRAINING_SAMPLES].index
        self._reliable_max_year = int(reliable_years.max()) if len(reliable_years) > 0 else 0

    def _encode(self, brand: str, segment: str, car_type: str,
                years: int, annual_km: int, price: float) -> pd.DataFrame:
        """Build a single-row feature DataFrame matching training schema."""
        row: dict[str, float] = {
            "years": float(years),
            "km_per_year": float(annual_km),
            "log_price": float(np.log(price + 1)),
        }
        if self._feature_cols is not None:
            for col in self._feature_cols[3:]:
                row[col] = 0.0
        for prefix, val in [("brand_", brand), ("segment_", segment), ("car_type_", car_type)]:
            col = f"{prefix}{val}"
            if col in row:
                row[col] = 1.0
        return pd.DataFrame([row])

    def _group_curve_baseline(self, brand: str, segment: str, car_type: str,
                              years: int, annual_km: float) -> float | None:
        """Compute a real-data-based parametric retention value for the target year,
        using the PAVA-monotonized group curve from ``get_group_curve()`` as anchors.

        - Years within the curve: linear interpolation between anchors.
        - Years beyond the curve: exponential extrapolation from the last two
          anchors, then floored by the heavy-tail asymptote (inert for
          over-predicting groups, raises under-predicted long-tail cars).
        - Returns None if the group has no observed training data at all.

        This serves as the shrinkage target for the ML ensemble — it reflects
        real bonbanh/oto retention rather than parametric-synthetic contamination.
        """
        curve = self._get_real_group_curve(brand, segment, car_type)
        if not curve:
            return None

        ys_sorted = sorted(curve.keys())
        if years <= ys_sorted[0]:
            retention = float(curve[ys_sorted[0]])
        elif years >= ys_sorted[-1]:
            # Exponential extrapolation past the last anchor
            if len(ys_sorted) >= 2:
                y_a, y_b = ys_sorted[-2], ys_sorted[-1]
                r_a, r_b = curve[y_a], curve[y_b]
                if r_a > 0 and r_b < r_a:
                    # Back out decay rate from the last two anchors
                    span = y_b - y_a
                    decay_rate = 1.0 - (r_b / r_a) ** (1.0 / span)
                    retention = r_b * ((1 - decay_rate) ** (years - y_b))
                else:
                    retention = float(curve[ys_sorted[-1]])
            else:
                retention = float(curve[ys_sorted[-1]])
            # Heavy-tail floor
            floor_frac = HEAVY_TAIL_ASYMPTOTE.get(segment, HEAVY_TAIL_ASYMPTOTE_DEFAULT)
            retention = max(retention, float(curve[ys_sorted[-1]]) * floor_frac)
        else:
            # Linear interpolation between surrounding anchors
            for i in range(1, len(ys_sorted)):
                if years <= ys_sorted[i]:
                    y0, y1 = ys_sorted[i - 1], ys_sorted[i]
                    r0, r1 = float(curve[y0]), float(curve[y1])
                    frac = (years - y0) / (y1 - y0)
                    retention = r0 + (r1 - r0) * frac
                    break
            else:
                retention = float(curve[ys_sorted[-1]])

        return retention

    def _get_real_group_curve(self, brand: str, segment: str, car_type: str) -> dict[int, float]:
        """Like get_group_curve() but uses _real_stats (real-only rows from
        bonbanh/oto) instead of the contaminated _stats (synthetic + real).

        This is the shrinkage target for predict_resale() — it reflects true
        Vietnamese market retention rather than the parametric-synthetic mix.
        """
        stats = self._real_stats
        if stats is None or len(stats) == 0:
            return self.get_group_curve(brand, segment, car_type)
        mask = (
            (stats["brand"] == brand)
            & (stats["segment"] == segment)
            & (stats["car_type"] == car_type)
        )
        sub = stats[mask]
        if len(sub) == 0:
            # No real data for this specific group — fall back to the full
            # (contaminated) group curve so there is always a shrinkage target.
            return self.get_group_curve(brand, segment, car_type)
        curve: dict[int, float] = {}
        for _, row in sub.iterrows():
            curve[int(row["years"])] = float(row["avg_resale_pct"])
        if len(curve) > 1:
            ys = sorted(curve.keys())
            vals = np.array([curve[y] for y in ys], dtype=float)
            try:
                pooled = isotonic_regression(
                    vals, increasing=False, y_min=0.0, y_max=1.0
                )
                curve = {y: float(v) for y, v in zip(ys, pooled)}
            except Exception:  # pragma: no cover - defensive
                pass
        return curve

    def predict_resale(self, brand: str, segment: str, car_type: str,
                       years: int, annual_km: int, price: float) -> dict:
        """
        Returns dict with:
          - 'ml_prediction': ensemble average of RF + GB (or None), calibrated
            to be non-increasing across the car's observed year range via PAVA
          - 'ml_prediction_raw': the un-calibrated ensemble average for the
            requested year (or None)
          - 'group_avg': group-average resale_pct from training data (or None)
          - 'method': 'ml', 'group_avg', or 'none'
        """
        result: dict = {
            "ml_prediction": None,
            "ml_prediction_raw": None,
            "group_avg": None,
            "method": "none",
        }

        # Group average lookup
        if self._stats is not None and len(self._stats) > 0:
            mask = (
                (self._stats["brand"] == brand)
                & (self._stats["segment"] == segment)
                & (self._stats["car_type"] == car_type)
                & (self._stats["years"] == years)
            )
            match = self._stats[mask]
            if len(match) > 0:
                result["group_avg"] = float(match.iloc[0]["avg_resale_pct"])
                result["method"] = "group_avg"

        # ML ensemble prediction — use whichever models loaded successfully
        # (RF only, GB only, or both). Never let one missing model block prediction.
        models = [m for m in (self._rf, self._gb) if m is not None]
        if models and self._feature_cols is not None:
            group_max = self._group_max_year.get((brand, segment, car_type), 0)

            # Predict the whole observed year range (1..group_max) and enforce
            # non-increasing retention across it with Pool Adjacent Violators
            # (PAVA / isotonic regression, decreasing). RF predictions are
            # already ~monotonic per group, so this is a light correction that
            # removes sparse-year noise (Y4 > Y3) at the source — the runtime
            # monotonicity clamp in calculations.py is therefore unnecessary.
            #
            # Batch all year predictions into single model.predict() calls to avoid
            # the sklearn "delayed should be used with Parallel" warning that fires
            # on every loop iteration. Batching also improves performance ~10x.
            if group_max >= 1:
                raw_seq: list[float] = []
                req_preds: list[float] = []
                req_Xv = None
                
                # Build feature arrays for all years (1..group_max) and stack into
                # single (group_max, features) array for batch prediction.
                year_arrays = []
                for y in range(1, group_max + 1):
                    X = self._encode(brand, segment, car_type, y, annual_km, price)
                    X = X.reindex(columns=self._feature_cols, fill_value=0.0)
                    year_arrays.append(X.to_numpy(dtype=float)[0, :])
                X_batch = np.vstack(year_arrays)  # (group_max, features)
                
                # Predict for all years in single call per model, extract per-year averages
                all_model_preds = [m.predict(X_batch) for m in models]  # Each: (group_max,)
                for y_idx in range(group_max):
                    preds = [float(all_model_preds[m_idx][y_idx]) for m_idx in range(len(models))]
                    raw_seq.append(float(np.mean(preds)))
                    if (y_idx + 1) == years:  # y_idx is 0-based, years is 1-based
                        req_preds = preds
                        req_Xv = X_batch[y_idx:y_idx+1, :]
                try:
                    calibrated = isotonic_regression(
                        np.array(raw_seq, dtype=float),
                        increasing=False,
                        y_min=0.0,
                        y_max=1.0,
                    )
                except Exception:  # pragma: no cover - defensive
                    calibrated = np.array(raw_seq, dtype=float)

                if 1 <= years <= group_max:
                    ensemble = float(calibrated[years - 1])
                    raw_val = float(raw_seq[years - 1])
                    preds = req_preds
                    Xv = req_Xv
                else:
                    # Requested year is beyond the observed range — predict it
                    # directly (the calculate_resale gate keeps in-range years
                    # on the calibrated curve).
                    X = self._encode(brand, segment, car_type, years, annual_km, price)
                    X = X.reindex(columns=self._feature_cols, fill_value=0.0)
                    Xv = X.to_numpy(dtype=float)
                    preds = [float(m.predict(Xv)[0]) for m in models]
                    ensemble = float(np.mean(preds))
                    raw_val = ensemble
            else:
                X = self._encode(brand, segment, car_type, years, annual_km, price)
                X = X.reindex(columns=self._feature_cols, fill_value=0.0)
                Xv = X.to_numpy(dtype=float)
                preds = [float(m.predict(Xv)[0]) for m in models]
                ensemble = float(np.mean(preds))
                raw_val = ensemble

            spread = max(preds) - min(preds)

            # Shrink ML ensemble toward real-data parametric baseline (counteracts
            # synthetic training-data contamination where synthetic retention is
            # biased low, e.g. B-SUV/ICE y4: synthetic ~0.63 vs real ~0.80).
            # The baseline is the PAVA-monotonized group-curve interpolated/
            # extrapolated to the target year. SHRINKAGE_ALPHA controls the blend.
            param_baseline = self._group_curve_baseline(
                brand, segment, car_type, years, annual_km)
            if param_baseline is not None:
                ensemble = (SHRINKAGE_ALPHA * ensemble
                            + (1 - SHRINKAGE_ALPHA) * param_baseline)

            result["ml_prediction"] = ensemble
            result["ml_prediction_raw"] = raw_val
            result["ml_spread"] = spread
            result["method"] = "ml"

            try:
                if self._rf is not None and Xv is not None:
                    # Xv is already validated by the ensemble predict above; skip the
                    # per-tree re-validation (~600x) so predict_resale stays cheap on
                    # constrained CPUs (this is the dominant cost on the old sklearn
                    # path that Render was running).
                    tree_preds = [float(t.predict(Xv, check_input=False)[0]) for t in self._rf.estimators_]
                    result["ml_std"] = float(np.std(tree_preds))
                else:
                    result["ml_std"] = None
            except Exception:  # pragma: no cover - defensive
                result["ml_std"] = None

        return result

    def get_car_max_training_year(self, brand: str, segment: str, car_type: str) -> int:
        """Last year the car group has enough observed samples to trust ML.

        Returns 0 when the group has no training data at all (so callers fall
        through to the parametric path for every year)."""
        return self._group_max_year.get((brand, segment, car_type), 0)

    def get_group_curve(self, brand: str, segment: str, car_type: str) -> dict[int, float]:
        """Group-average retention curve as {year: avg_resale_pct}, derived from
        the existing per-(brand,segment,car_type,years) group stats. Used to seed
        the two-phase parametric extrapolation with observed anchors."""
        if self._stats is None or len(self._stats) == 0:
            return {}
        mask = (
            (self._stats["brand"] == brand)
            & (self._stats["segment"] == segment)
            & (self._stats["car_type"] == car_type)
        )
        sub = self._stats[mask]
        if len(sub) == 0:
            return {}
        # Keep anchors whose (group, year) cell has enough observed samples in
        # the DENSE region (years <= reliable_max_year, where the global sample
        # count is >= 50). A single stray sparse listing must not dominate the
        # curve there. But for the SPARSE deep tail (years > reliable_max_year)
        # we relax the threshold to n >= 1: beyond the dense region there is no
        # other basis to estimate retention, and a real market observation
        # (however sparse) beats a flat exponential extrapolation that we know
        # over-predicts fast-depreciating groups (e.g. diesel D-SUV Fortuner:
        # predicted 0.526 vs real 0.313 at age 14). The heavy-tail floor still
        # guards against over-shooting, and _blend_resale_curve's PAVA step
        # enforces monotonicity, so a single noisy tail anchor is bounded.
        counts = self._group_year_counts.get((brand, segment, car_type), {})
        rmy = self._reliable_max_year
        curve: dict[int, float] = {}
        for _, row in sub.iterrows():
            y = int(row["years"])
            needed = PARAMETRIC_MIN_SAMPLES if y <= rmy else 1
            if counts.get(y, 0) >= needed:
                curve[y] = float(row["avg_resale_pct"])
        # PAVA: enforce monotonically non-increasing retention (older => lower value).
        # Sparse tail anchors (n=1) can be inflated, producing upward jumps in
        # _interp_group_curve (e.g. k3 y7→y9→y11: 0.418→0.451→0.483). Isotonic
        # regression with increasing=False pools violating neighbours so the
        # parametric fallback never predicts a car is worth MORE as it ages.
        if len(curve) > 1:
            ys = sorted(curve.keys())
            vals = np.array([curve[y] for y in ys], dtype=float)
            try:
                pooled = isotonic_regression(
                    vals, increasing=False, y_min=0.0, y_max=1.0
                )
                curve = {y: float(v) for y, v in zip(ys, pooled)}
            except Exception:  # pragma: no cover - defensive
                pass
        return curve

    @property
    def max_training_year(self) -> int:
        """Maximum year the ML model was trained on. Beyond this, predictions
        are unreliable because tree-based models cannot extrapolate."""
        return self._max_training_year

    @property
    def reliable_max_year(self) -> int:
        """Last year with sufficient training samples (>= 50) for reliable
        ML predictions. Falls back to parametric for years beyond this,
        even if training data technically extends further out."""
        return self._reliable_max_year


# Singleton for reuse
_predictor: Optional[ResalePredictor] = None


def get_predictor() -> ResalePredictor:
    global _predictor
    if _predictor is None:
        _predictor = ResalePredictor()
    return _predictor