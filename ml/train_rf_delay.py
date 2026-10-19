import os
import clickhouse_connect
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
import joblib
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import time

FEATURES = ["Reporting_Airline", "Origin_Airport", "Destination_Airport", "Hour_Of_Departure"] 
TARGET_LABEL = "Is_Dep_Delay_Greater_Than_15"
PARAMS = {"random_state" : 42, "n_jobs" :-1, "n_estimators" :100, "max_depth" : 15, "min_samples_leaf" : 50}
CATEGORICAL = ["Reporting_Airline", "Origin_Airport", "Destination_Airport"]
# Constants for running a model
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
TRAIN_END = "2024-07-31"
VAL_START, VAL_END   = "2024-08-01", "2025-07-31"
TEST_START, TEST_END = "2025-08-01", "2026-07-31"
YEARS = 1
VERSION = 1
STEP = "curve"
MODEL_NAME = f"rf_delay_y{YEARS}_v{VERSION}"
FRACTIONS = {"12_5": 0.125, "25": 0.25, "50": 0.5, "100": 1.0}


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

def load_data(): 
    client = get_client()

    df = client.query_df("SELECT * FROM features_delay")

    return df

def build_pipeline(model):

    preprocess = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)], remainder="passthrough")

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

def run_train(model_name, step, model, train, validation):
    params = changed_params(model)
    pipeline = build_pipeline(model)

    run_time_start = time.perf_counter()
    pipeline.fit(train[FEATURES], train[TARGET_LABEL])
    train_seconds = time.perf_counter() - run_time_start

    train_metrics = evaluate(pipeline, train)
    val_metrics = evaluate(pipeline, validation)
    print(
        f"{model_name} | rows: {len(train)} | "
        f"train PR-AUC: {train_metrics['pr_auc']:.3f} | "
        f"val PR-AUC: {val_metrics['pr_auc']:.3f} "
        f"(baseline {val_metrics['baseline_pr_auc']:.3f}) | "
        f"{train_seconds:.1f}s"
    )

    joblib.dump(pipeline, ARTIFACTS_DIR / f"{model_name}.joblib")

    record_run(model_name, step, train, validation, FEATURES, params, train_seconds)
    record_metrics(model_name, "train", train_metrics)
    record_metrics(model_name, "validation", val_metrics)

def main():
    df = load_data()

    train = select_period(df, train_start_for(YEARS), TRAIN_END)
    validation = select_period (df, VAL_START, VAL_END)

    for key, fraction in FRACTIONS.items():
        subset = train.sample(frac=fraction, random_state=PARAMS["random_state"]).sort_index()
        model = RandomForestClassifier(**PARAMS)
        run_train(f"rf_delay_y{YEARS}_f{key}_v{VERSION}", STEP, model, subset, validation)


if __name__ == "__main__":
    main()
    




