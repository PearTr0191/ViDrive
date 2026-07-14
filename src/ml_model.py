"""
ResalePredictor: loads group-average statistics from training_data.json
and ensemble ML models (RF + GB) for resale value prediction.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
import joblib

HERE = Path(__file__).parent.parent
MODELS_DIR = HERE / "data" / "models"
TRAINING_DATA_FILE = MODELS_DIR / "training_data.json"
RF_PATH = MODELS_DIR / "resale_rf.pkl"
GB_PATH = MODELS_DIR / "resale_gb.pkl"


class ResalePredictor:
    """Predicts resale percentage using group-averages and ensemble ML."""

    def __init__(self) -> None:
        self._stats: Optional[pd.DataFrame] = None
        self._rf: Optional[object] = None
        self._gb: Optional[object] = None
        self._feature_cols: Optional[list[str]] = None
        self._load()

    def _load(self) -> None:
        """Load training data, compute group stats, and load models."""
        if not TRAINING_DATA_FILE.exists():
            self._stats = pd.DataFrame()
            return

        with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        df = pd.DataFrame(raw)

        # Group-average statistics by (brand, segment, car_type, years)
        group_cols = ["brand", "segment", "car_type", "years"]
        self._stats = df.groupby(group_cols)["resale_pct"].mean().reset_index()
        self._stats.rename(columns={"resale_pct": "avg_resale_pct"}, inplace=True)

        # Load ML models
        if RF_PATH.exists():
            self._rf = joblib.load(RF_PATH)
        if GB_PATH.exists():
            self._gb = joblib.load(GB_PATH)

        # Build feature columns from training data for encoding
        cats = ["brand", "segment", "car_type"]
        encoded = pd.get_dummies(df[cats], prefix=cats, drop_first=False).astype(float)
        self._feature_cols = ["years", "km_per_year", "log_price"] + list(encoded.columns)

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

    def predict_resale(self, brand: str, segment: str, car_type: str,
                       years: int, annual_km: int, price: float) -> dict:
        """
        Returns dict with:
          - 'ml_prediction': ensemble average of RF + GB (or None)
          - 'group_avg': group-average resale_pct from training data (or None)
          - 'method': 'ml', 'group_avg', or 'none'
        """
        result: dict = {"ml_prediction": None, "group_avg": None, "method": "none"}

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

        # ML ensemble prediction
        if self._rf is not None and self._gb is not None and self._feature_cols is not None:
            X = self._encode(brand, segment, car_type, years, annual_km, price)
            X = X.reindex(columns=self._feature_cols, fill_value=0.0)
            rf_pred = float(self._rf.predict(X)[0])
            gb_pred = float(self._gb.predict(X)[0])
            ensemble = (rf_pred + gb_pred) / 2.0
            result["ml_prediction"] = ensemble
            result["method"] = "ml"

        return result


# Singleton for reuse
_predictor: Optional[ResalePredictor] = None


def get_predictor() -> ResalePredictor:
    global _predictor
    if _predictor is None:
        _predictor = ResalePredictor()
    return _predictor