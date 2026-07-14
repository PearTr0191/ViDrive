"""
Train resale prediction models (Random Forest & Gradient Boosting)
from training_data.json. Saves .pkl files to data/models/.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import joblib

HERE = Path(__file__).parent
DATA_FILE = HERE / "training_data.json"
RF_PATH = HERE / "resale_rf.pkl"
GB_PATH = HERE / "resale_gb.pkl"


def load_data() -> pd.DataFrame:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw)
    df["log_price"] = np.log(df["price"] + 1)
    df["km_per_year"] = df["annual_km"]
    return df


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    cats = ["brand", "segment", "car_type"]
    encoded = pd.get_dummies(df[cats], prefix=cats, drop_first=False).astype(float)
    result = pd.concat(
        [df[["years", "km_per_year", "log_price"]].reset_index(drop=True),
         encoded.reset_index(drop=True)],
        axis=1,
    )
    return result


def main():
    df = load_data()
    y = df["resale_pct"].values
    X = encode_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    rf = RandomForestRegressor(
        n_estimators=600,
        max_depth=15,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    gb = GradientBoostingRegressor(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.03,
        min_samples_leaf=4,
        subsample=0.8,
        random_state=42,
    )
    gb.fit(X_train, y_train)

    for name, model in [("RF", rf), ("GB", gb)]:
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        mape = mean_absolute_percentage_error(y_test, preds) * 100
        print(f"{name}  | MAE: {mae:.4f}  | MAPE: {mape:.2f}%")

    joblib.dump(rf, RF_PATH)
    joblib.dump(gb, GB_PATH)
    print(f"Models saved to {RF_PATH.parent}")


if __name__ == "__main__":
    main()