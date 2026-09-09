import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


def train_freight_forecaster():
  print("=" * 60)
  print("SIH26006: Training Multi-Horizon Freight Rate Forecaster")
  print("=" * 60)

  features_path = os.path.join("data", "processed", "model_features.csv")
  if not os.path.exists(features_path):
    raise FileNotFoundError(f"Missing dataset at {features_path}")

  df = pd.read_csv(features_path)
  df["date"] = pd.to_datetime(df["date"])
  df = df.sort_values("date").reset_index(drop=True)

  # Fill initial lag window NaNs using forward/backward fill
  feature_cols = [
      "bunker_vlsfo",
      "usd_inr",
      "day_of_week",
      "month",
      "bdi_lag_1",
      "bdi_lag_7",
      "bdi_rolling_mean_7",
      "bdi_rolling_std_7",
      "bdi_rolling_mean_30",
      "bunker_vlsfo_lag_1",
      "bunker_change_pct_7d",
      "usd_inr_lag_1",
      "usd_inr_change_pct_7d",
  ]

  # Filter available columns present in dataset
  valid_features = [c for c in feature_cols if c in df.columns]

  # Forward fill missing lag series
  df[valid_features] = df[valid_features].ffill().bfill().fillna(0)

  # Filter to a primary benchmark corridor: KALIMANTAN to DHAMRA (PANAMAX)
  # (Can be generalized across all origin-destination routes)
  benchmark_df = df[
      (df["vessel_type"] == "PANAMAX")
      & (df["destination"] == "DHAMRA")
      & (df["freight_rate_usd_mt"].notnull())
  ].copy()

  if len(benchmark_df) < 50:
    print(
        "[!] Corridor subset small, aggregating median rate across all routes."
    )
    benchmark_df = (
        df.groupby("date")
        .agg({
            "freight_rate_usd_mt": "median",
            **{col: "first" for col in valid_features},
        })
        .reset_index()
    )

  X = benchmark_df[valid_features]
  y = benchmark_df["freight_rate_usd_mt"]

  # Time-series split (Train: first 80%, Test: recent 20% to prevent lookahead leakage)
  split_idx = int(len(benchmark_df) * 0.8)
  X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
  y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
  test_dates = benchmark_df["date"].iloc[split_idx:]

  print(f"[*] Training samples: {len(X_train)} | Testing samples: {len(X_test)}")

  # 1. Train Median Predictor (P50)
  model_p50 = GradientBoostingRegressor(
      loss="squared_error", n_estimators=120, max_depth=4, random_state=42
  )
  model_p50.fit(X_train, y_train)
  pred_p50 = model_p50.predict(X_test)

  # 2. Train Quantile Risk Lower Bound (P10)
  model_p10 = GradientBoostingRegressor(
      loss="quantile",
      alpha=0.10,
      n_estimators=120,
      max_depth=4,
      random_state=42,
  )
  model_p10.fit(X_train, y_train)
  pred_p10 = model_p10.predict(X_test)

  # 3. Train Quantile Risk Upper Bound (P90)
  model_p90 = GradientBoostingRegressor(
      loss="quantile",
      alpha=0.90,
      n_estimators=120,
      max_depth=4,
      random_state=42,
  )
  model_p90.fit(X_train, y_train)
  pred_p90 = model_p90.predict(X_test)

  # Metrics
  mae = mean_absolute_error(y_test, pred_p50)
  rmse = np.sqrt(mean_squared_error(y_test, pred_p50))
  print(f"\n[+] Validation Performance:")
  print(f"    - Mean Absolute Error (MAE): ${mae:.2f}/MT")
  print(f"    - Root Mean Squared Error (RMSE): ${rmse:.2f}/MT")

  # Generate Output Visualization for Presentation Deck
  os.makedirs(os.path.join("data", "metadata"), exist_ok=True)
  plot_path = os.path.join("data", "metadata", "freight_forecast_eval.png")

  plt.figure(figsize=(12, 6))
  plt.plot(
      test_dates,
      y_test.values,
      label="Actual Fixture Rate ($/MT)",
      color="black",
      lw=1.8,
  )
  plt.plot(
      test_dates,
      pred_p50,
      label="AI Forecast (P50 Expected)",
      color="#1f77b4",
      lw=2,
      linestyle="--",
  )
  plt.fill_between(
      test_dates,
      pred_p10,
      pred_p90,
      color="#1f77b4",
      alpha=0.25,
      label="Uncertainty Bound (P10 - P90)",
  )
  plt.title(
      "Bulk Freight Spot Rate Trajectory — AI Multi-Horizon Forecast",
      fontsize=13,
      fontweight="bold",
  )
  plt.xlabel("Timeline", fontsize=11)
  plt.ylabel("Commercial Freight Rate (USD/MT)", fontsize=11)
  plt.grid(True, linestyle=":", alpha=0.6)
  plt.legend(loc="upper left")
  plt.tight_layout()
  plt.savefig(plot_path, dpi=300)
  plt.close()

  print(f"[+] Forecast chart exported to: {plot_path}")
  print("=" * 60)


if __name__ == "__main__":
  train_freight_forecaster()