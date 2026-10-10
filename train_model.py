import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, cross_validate
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import joblib
import os
import logging
from datetime import datetime


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "dataset/student_data.csv"

MODEL_DIR = "model"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "model.pkl"
)

META_PATH = os.path.join(
    MODEL_DIR,
    "metadata.pkl"
)

METRICS_PATH = os.path.join(
    MODEL_DIR,
    "model_metrics.csv"
)

REPORT_PATH = os.path.join(
    MODEL_DIR,
    "training_report.txt"
)


FEATURES = [
    "studytime",
    "failures",
    "absences",
    "health",
    "G1",
    "G2"
]

TARGET = "G3"

MODEL_VERSION = "v2.0"


os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ============================================================
# LOAD DATASET
# ============================================================

try:

    data = pd.read_csv(DATA_PATH)

    logging.info(
        f"Dataset loaded successfully: {DATA_PATH}"
    )

except Exception as e:

    logging.error(
        f"Failed to load dataset: {e}"
    )

    raise


# ============================================================
# DATA VALIDATION
# ============================================================

required_columns = FEATURES + [TARGET]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]

if missing_columns:

    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


logging.info(
    f"Dataset rows: {len(data)}"
)

logging.info(
    f"Dataset columns: {len(data.columns)}"
)


# ============================================================
# REMOVE MISSING VALUES
# ============================================================

before_rows = len(data)

data = data.dropna(
    subset=required_columns
).copy()

after_rows = len(data)

removed_rows = before_rows - after_rows


if removed_rows > 0:

    logging.warning(
        f"Removed {removed_rows} rows containing missing values."
    )


# ============================================================
# FEATURES / TARGET
# ============================================================

X = data[FEATURES]

y = data[TARGET]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


logging.info(
    f"Training samples: {len(X_train)}"
)

logging.info(
    f"Testing samples: {len(X_test)}"
)


# ============================================================
# MODEL DEFINITIONS
# ============================================================

pipelines = {

    "LinearRegression": Pipeline([
        (
            "scaler",
            StandardScaler()
        ),

        (
            "model",
            LinearRegression()
        )
    ]),

    "RandomForest": Pipeline([
        (
            "scaler",
            StandardScaler()
        ),

        (
            "model",
            RandomForestRegressor(
                n_estimators=300,
                random_state=42,
                n_jobs=-1
            )
        )
    ])
}


# ============================================================
# MODEL EVALUATION
# ============================================================

results = []

trained_models = {}

best_model = None
best_model_name = None

best_r2 = float("-inf")


for name, pipeline in pipelines.items():

    logging.info(
        f"Training model: {name}"
    )

    # --------------------------------------------------------
    # CROSS VALIDATION
    # --------------------------------------------------------

    cv_results = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=5,
        scoring=[
            "r2",
            "neg_mean_absolute_error",
            "neg_mean_squared_error"
        ],
        return_train_score=False
    )

    cv_r2 = cv_results[
        "test_r2"
    ]

    cv_mae = -cv_results[
        "test_neg_mean_absolute_error"
    ]

    cv_mse = -cv_results[
        "test_neg_mean_squared_error"
    ]

    cv_rmse = np.sqrt(cv_mse)


    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    pipeline.fit(
        X_train,
        y_train
    )

    trained_models[name] = pipeline


    # --------------------------------------------------------
    # TEST PREDICTIONS
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )


    # --------------------------------------------------------
    # TEST METRICS
    # --------------------------------------------------------

    test_r2 = r2_score(
        y_test,
        predictions
    )

    test_mae = mean_absolute_error(
        y_test,
        predictions
    )

    test_mse = mean_squared_error(
        y_test,
        predictions
    )

    test_rmse = np.sqrt(
        test_mse
    )


    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    model_result = {

        "model": name,

        "cv_r2_mean": float(
            cv_r2.mean()
        ),

        "cv_r2_std": float(
            cv_r2.std()
        ),

        "cv_mae_mean": float(
            cv_mae.mean()
        ),

        "cv_rmse_mean": float(
            cv_rmse.mean()
        ),

        "test_r2": float(
            test_r2
        ),

        "test_mae": float(
            test_mae
        ),

        "test_mse": float(
            test_mse
        ),

        "test_rmse": float(
            test_rmse
        )
    }


    results.append(
        model_result
    )


    # --------------------------------------------------------
    # LOG RESULTS
    # --------------------------------------------------------

    logging.info(
        f"{name} | "
        f"CV R²={cv_r2.mean():.4f} | "
        f"Test R²={test_r2:.4f} | "
        f"MAE={test_mae:.4f} | "
        f"RMSE={test_rmse:.4f}"
    )


    # --------------------------------------------------------
    # BEST MODEL
    # --------------------------------------------------------

    if test_r2 > best_r2:

        best_r2 = test_r2

        best_model = pipeline

        best_model_name = name


# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(
    results
)


# Sort by test R²

results_df = results_df.sort_values(
    by="test_r2",
    ascending=False
).reset_index(
    drop=True
)


# ============================================================
# SAVE METRICS CSV
# ============================================================

results_df.to_csv(
    METRICS_PATH,
    index=False
)


logging.info(
    f"Model comparison saved to: {METRICS_PATH}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

feature_importance = {}


if best_model_name == "RandomForest":

    rf_model = best_model.named_steps[
        "model"
    ]

    importance_values = (
        rf_model.feature_importances_
    )

    feature_importance = dict(
        sorted(
            zip(
                FEATURES,
                importance_values
            ),
            key=lambda x: x[1],
            reverse=True
        )
    )


# ============================================================
# SAVE BEST MODEL
# ============================================================

joblib.dump(
    best_model,
    MODEL_PATH
)


# ============================================================
# BEST MODEL METRICS
# ============================================================

best_result = results_df.iloc[0].to_dict()


# ============================================================
# SAVE METADATA
# ============================================================

metadata = {

    "model_version": MODEL_VERSION,

    "trained_at":
        datetime.now().isoformat(),

    "model_name":
        best_model_name,

    "features":
        FEATURES,

    "target":
        TARGET,

    "dataset_rows":
        len(data),

    "training_rows":
        len(X_train),

    "testing_rows":
        len(X_test),

    "removed_missing_rows":
        removed_rows,

    "metrics":
        results,

    "best_model_metrics":
        best_result,

    "feature_importance":
        feature_importance
}


joblib.dump(
    metadata,
    META_PATH
)


# ============================================================
# TRAINING REPORT
# ============================================================

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8"
) as report:

    report.write(
        "STUDENT PERFORMANCE ML - TRAINING REPORT\n"
    )

    report.write(
        "=" * 55 + "\n\n"
    )

    report.write(
        f"Model Version: {MODEL_VERSION}\n"
    )

    report.write(
        f"Training Time: "
        f"{metadata['trained_at']}\n"
    )

    report.write(
        f"Dataset Rows: {len(data)}\n"
    )

    report.write(
        f"Training Rows: {len(X_train)}\n"
    )

    report.write(
        f"Testing Rows: {len(X_test)}\n"
    )

    report.write(
        f"Best Model: {best_model_name}\n\n"
    )


    report.write(
        "MODEL COMPARISON\n"
    )

    report.write(
        "-" * 55 + "\n"
    )

    for result in results:

        report.write(
            f"\nModel: {result['model']}\n"
        )

        report.write(
            f"CV R²: "
            f"{result['cv_r2_mean']:.4f}\n"
        )

        report.write(
            f"Test R²: "
            f"{result['test_r2']:.4f}\n"
        )

        report.write(
            f"MAE: "
            f"{result['test_mae']:.4f}\n"
        )

        report.write(
            f"MSE: "
            f"{result['test_mse']:.4f}\n"
        )

        report.write(
            f"RMSE: "
            f"{result['test_rmse']:.4f}\n"
        )


    if feature_importance:

        report.write(
            "\n\nFEATURE IMPORTANCE\n"
        )

        report.write(
            "-" * 55 + "\n"
        )

        for feature, importance in feature_importance.items():

            report.write(
                f"{feature}: "
                f"{importance:.4f}\n"
            )


# ============================================================
# FINAL OUTPUT
# ============================================================

logging.info(
    "=" * 60
)

logging.info(
    f"BEST MODEL: {best_model_name}"
)

logging.info(
    f"MODEL VERSION: {MODEL_VERSION}"
)

logging.info(
    f"TEST R²: "
    f"{best_result['test_r2']:.4f}"
)

logging.info(
    f"TEST MAE: "
    f"{best_result['test_mae']:.4f}"
)

logging.info(
    f"TEST RMSE: "
    f"{best_result['test_rmse']:.4f}"
)

logging.info(
    f"MODEL SAVED: {MODEL_PATH}"
)

logging.info(
    f"METADATA SAVED: {META_PATH}"
)

logging.info(
    f"METRICS SAVED: {METRICS_PATH}"
)

logging.info(
    f"REPORT SAVED: {REPORT_PATH}"
)

logging.info(
    "=" * 60
)