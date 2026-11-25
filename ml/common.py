import os
import clickhouse_connect
from sklearn.metrics import average_precision_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import time

# Shared by every model script: these define the comparison (same features, same split).
FEATURES = ["Reporting_Airline", "Origin_Airport", 
            "Destination_Airport", "Hour_Of_Departure",
              "Weekday_Of_Departure", "Month_Of_Departure",
                "Departures_In_Hour"] 
TARGET_LABEL = "Is_Dep_Delay_Greater_Than_15"
CATEGORICAL = ["Reporting_Airline", "Origin_Airport", "Destination_Airport"]
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
TRAIN_END = "2024-07-31"
VAL_START, VAL_END   = "2024-08-01", "2025-07-31"
TEST_START, TEST_END = "2025-08-01", "2026-07-31"


def get_client():
     client = clickhouse_connect.get_client(
            host = "localhost",
            port = 8123,
            username = os.environ["CLICKHOUSE_USER"],
            password = os.environ["CLICKHOUSE_PASSWORD"],
            database = os.environ["CLICKHOUSE_DB"]
        )

     return client
    
def changed_params(model):
    defaults = type(model)().get_params()
    return {k: v for k, v in model.get_params().items() if v != defaults[k]}

def train_start_for(years):
    train_end = pd.Timestamp(TRAIN_END)
    next_day = train_end + pd.Timedelta(days=1)
    return next_day - pd.DateOffset(years=years)

def select_period(df, start, end):
    in_period = (df["Flight_Date"] >= start) & (df["Flight_Date"] <= end)
    return df[in_period]

def load_data(years):
    client = get_client()

    columns = ["Flight_Date", TARGET_LABEL] + FEATURES
    start = train_start_for(years).date()
    query = (f"SELECT {', '.join(columns)} FROM features_delay "
             f"WHERE Flight_Date BETWEEN '{start}' AND '{VAL_END}'")

    return client.query_df(query)

def build_pipeline(model, preprocess):

    pipeline = Pipeline([
    ("preprocess", preprocess),
    ("model", model),
])
    return pipeline

def record_run(model_name, step, train, validation, features, params, train_seconds, force=False):
     
    client = get_client()

    client.command("""
            CREATE TABLE IF NOT EXISTS training_runs (
                Model_Name    String,
                Step          String,
                Trained_At    DateTime,
                Train_Start   Date,
                Train_End     Date,
                Val_Start     Nullable(Date),
                Val_End       Nullable(Date),
                Train_Rows    UInt64,
                Val_Rows      Nullable(UInt64),
                Features      String,
                Params        String,
                Train_Seconds Float64
            )
            ENGINE = MergeTree
            ORDER BY Model_Name
    """)
    
    client.command(
        "ALTER TABLE training_runs DELETE WHERE Model_Name = {m:String} SETTINGS mutations_sync = 1",
        parameters={"m": model_name},
    )

    run = pd.DataFrame([{
        "Model_Name": model_name,
        "Step": step,
        "Trained_At": datetime.now(),
        "Train_Start": train["Flight_Date"].min().date(),
        "Train_End": train["Flight_Date"].max().date(),
        "Train_Rows": int(len(train)),
        "Val_Start": validation["Flight_Date"].min().date(),
        "Val_End": validation["Flight_Date"].max().date(),
        "Val_Rows": int(len(validation)),
        "Features": json.dumps(sorted(features)),
        "Params": json.dumps(params, sort_keys=True),
        "Train_Seconds": float(train_seconds),
    }])
    client.insert_df("training_runs", run)


def record_metrics(model_name, split, metrics):
    client = get_client()

    client.command("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            Model_Name   String,
            Split        String,
            Metric       String,
            Value        Float64,
            Evaluated_At DateTime
        )
        ENGINE = MergeTree
        ORDER BY (Model_Name, Split, Metric)
    """)

    client.command(
        "ALTER TABLE model_metrics DELETE WHERE Model_Name = {m:String} AND Split = {s:String} SETTINGS mutations_sync = 1",
        parameters={"m": model_name, "s": split},
    )

    rows = pd.DataFrame({
        "Model_Name": model_name,
        "Split": split,
        "Metric": list(metrics.keys()),
        "Value": list(metrics.values()),
        "Evaluated_At": datetime.now(),
    })
    client.insert_df("model_metrics", rows)

def evaluate(pipeline, data):
    X = data[FEATURES]
    y = data[TARGET_LABEL]
    proba = pipeline.predict_proba(X)[:,1]
    pr_auc = average_precision_score(y, proba)
    baseline = y.mean()
    return {"pr_auc": pr_auc, "baseline_pr_auc": baseline}

def fit_model(model, train, preprocess):
    pipeline = build_pipeline(model, preprocess)

    run_time_start = time.perf_counter()
    pipeline.fit(train[FEATURES], train[TARGET_LABEL])
    train_seconds = time.perf_counter() - run_time_start

    return pipeline, train_seconds

def report(model_name, n_rows, train_metrics, val_metrics, train_seconds):
    print(
        f"{model_name} | rows: {n_rows} | "
        f"train PR-AUC: {train_metrics['pr_auc']:.3f} | "
        f"val PR-AUC: {val_metrics['pr_auc']:.3f} "
        f"(baseline {val_metrics['baseline_pr_auc']:.3f}) | "
        f"{train_seconds:.1f}s"
    )

def persist(model_name, step, pipeline, train, validation, params, train_seconds, train_metrics, val_metrics):
    joblib.dump(pipeline, ARTIFACTS_DIR / f"{model_name}.joblib")

    record_run(model_name, step, train, validation, FEATURES, params, train_seconds)
    record_metrics(model_name, "train", train_metrics)
    record_metrics(model_name, "validation", val_metrics)
