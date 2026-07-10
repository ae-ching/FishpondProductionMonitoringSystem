from pathlib import Path

import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    root_mean_squared_error,
)

# =====================================
# LOAD DATASET
# =====================================
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

DATASET_CANDIDATES = [
    DATASET_DIR / "fishpond_harvest_dataset.csv",
    DATASET_DIR / "fishpond_harvest_dataset (1).csv",
]
DATASET_PATH = next((path for path in DATASET_CANDIDATES if path.exists()), None)

if DATASET_PATH is None:
    available_csvs = sorted([p.name for p in DATASET_DIR.glob("*.csv")])
    raise FileNotFoundError(
        f"No training dataset found in {DATASET_DIR}. Available CSV files: {available_csvs}"
    )

print(f"Using training dataset: {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)

EXPECTED_FEATURES = [
    "Fish_Type",
    "Pond_Size",
    "Harvest_Month",
    "Previous_Harvest_Quantity",
    "Average_Harvest_Last_3_Records",
    "Total_Historical_Harvest_Records",
]
TARGET_COLUMN = "Harvest_Quantity"

missing_columns = [col for col in EXPECTED_FEATURES + [TARGET_COLUMN] if col not in df.columns]
if missing_columns:
    raise ValueError(f"Dataset is missing required columns: {missing_columns}")

if df[EXPECTED_FEATURES + [TARGET_COLUMN]].isna().any().any():
    raise ValueError("Dataset contains missing values; clean the data before training.")

print("=" * 60)
print("ORIGINAL DATASET")
print("=" * 60)
print(df.head())
print(f"\nDataset shape: {df.shape}")
print(f"Feature columns: {EXPECTED_FEATURES}")
print(f"Target column: {TARGET_COLUMN}")

# =====================================
# CREATE LABEL ENCODERS
# =====================================
# The new dataset uses Fish_Type as the categorical feature to encode.
fish_encoder = LabelEncoder()
df["Fish_Type"] = fish_encoder.fit_transform(df["Fish_Type"].astype(str))

print("\n" + "=" * 60)
print("ENCODED DATASET")
print("=" * 60)
print(df.head())

# =====================================
# SEPARATE FEATURES AND TARGET
# =====================================
X = df[EXPECTED_FEATURES].copy()
y = df[TARGET_COLUMN].copy()

print("\n" + "=" * 60)
print("FEATURES (X)")
print("=" * 60)
print(X.head())

print("\n" + "=" * 60)
print("TARGET (y)")
print("=" * 60)
print(y.head())

# =====================================
# SPLIT TRAINING AND TEST DATA
# =====================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# =====================================
# VERIFY DATA SPLIT
# =====================================
print("\n" + "=" * 60)
print("TRAINING AND TEST DATA")
print("=" * 60)

print(f"Training Features : {X_train.shape}")
print(f"Testing Features  : {X_test.shape}")
print(f"Training Target   : {y_train.shape}")
print(f"Testing Target    : {y_test.shape}")

# =====================================
# VERIFY FEATURE COLUMNS
# =====================================
print("\n" + "=" * 60)
print("FEATURE COLUMNS")
print("=" * 60)

print(X_train.columns)

# =====================================
# PREVIEW TRAINING DATA
# =====================================
print("\n" + "=" * 60)
print("FIRST 5 TRAINING SAMPLES")
print("=" * 60)

print(X_train.head())

print("\n" + "=" * 60)
print("FIRST 5 TRAINING TARGETS")
print("=" * 60)

print(y_train.head())

# =====================================
# PREVIEW TESTING DATA
# =====================================
print("\n" + "=" * 60)
print("FIRST 5 TESTING SAMPLES")
print("=" * 60)

print(X_test.head())

print("\n" + "=" * 60)
print("FIRST 5 TESTING TARGETS")
print("=" * 60)

print(y_test.head())

# =====================================
# PHASE 7 COMPLETE
# =====================================
print("\n" + "=" * 60)
print("PHASE 7 COMPLETE")
print("=" * 60)
print("✔ Dataset loaded")
print("✔ Categorical variables encoded")
print("✔ Features and target separated")
print("✔ Dataset split into training and testing sets")
print("✔ Ready for Phase 8: Train Random Forest Model")

# =====================================
# CREATE RANDOM FOREST MODEL
# =====================================
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

print("\n" + "=" * 60)
print("RANDOM FOREST MODEL")
print("=" * 60)
print(model)

# =====================================
# TRAIN RANDOM FOREST MODEL
# =====================================
model.fit(X_train, y_train)

print("\n" + "=" * 60)
print("MODEL TRAINING COMPLETE")
print("=" * 60)
print("✔ Random Forest successfully trained using the training dataset.")

# =====================================
# MAKE PREDICTIONS
# =====================================
predictions = model.predict(X_test)

print("\n" + "=" * 60)
print("FIRST 10 PREDICTIONS")
print("=" * 60)

for actual, predicted in zip(y_test.head(10), predictions[:10]):
    print(f"Actual: {actual:,.0f} kg | Predicted: {predicted:,.2f} kg")

# =====================================
# EVALUATE MODEL
# =====================================
r2 = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)
rmse = root_mean_squared_error(y_test, predictions)

print("\n" + "=" * 60)
print("MODEL EVALUATION")
print("=" * 60)

print(f"R² Score : {r2:.4f}")
print(f"MAE      : {mae:.2f} kg")
print(f"RMSE     : {rmse:.2f} kg")

print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)

print(f"The model explains approximately {r2 * 100:.2f}% of the variation in harvest quantity.")
print(f"On average, the prediction differs from the actual harvest by {mae:.2f} kg.")
print(f"The RMSE of {rmse:.2f} kg indicates the model's prediction error while giving greater weight to larger errors.")

# =====================================
# SAVE RANDOM FOREST MODEL
# =====================================
joblib.dump(model, MODELS_DIR / "random_forest_model.pkl")

print("\n" + "=" * 60)
print("MODEL SAVED")
print("=" * 60)
print("✔ Random Forest model saved.")

# =====================================
# SAVE LABEL ENCODERS
# =====================================
# NOTE: pond_encoder.pkl is no longer saved because Pond_ID feature has been removed

joblib.dump(fish_encoder, MODELS_DIR / "fish_encoder.pkl")

print("✔ Fish encoder saved.")

# =====================================
# SAVE FEATURE COLUMNS
# =====================================
feature_columns = list(X.columns)

joblib.dump(feature_columns, MODELS_DIR / "feature_columns.pkl")

print("✔ Feature columns saved.")

# =====================================
# PHASE 10 COMPLETE
# =====================================
print("\n" + "=" * 60)
print("PHASE 10 COMPLETE")
print("=" * 60)

print("✔ Random Forest model saved")
print("✔ Fish encoder saved")
print("✔ Feature columns saved")
print("✔ Machine Learning pipeline completed")
print("✔ Ready for Django Integration")