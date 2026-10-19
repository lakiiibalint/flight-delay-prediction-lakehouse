import os
import clickhouse_connect
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import time

FEATURES = ["Reporting_Airline", "Origin_Airport", "Destination_Airport", "Hour_Of_Departure"] 
TARGET_LABEL = "Is_Dep_Delay_Greater_Than_15"
PARAMS = {"random_state" : 42, "n_jobs" :-1, "n_estimators" :500, "max_depth" : 15, "min_samples_leaf" : 50}
CATEGORICAL = ["Reporting_Airline", "Origin_Airport", "Destination_Airport"]
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_NAME = 'rf_delay_v1'

def get_client():
     client = clickhouse_connect.get_client(
            host = "localhost",
            port = 8123,
            username = os.environ["CLICKHOUSE_USER"],
            password = os.environ["CLICKHOUSE_PASSWORD"],
            database = os.environ["CLICKHOUSE_DB"]
        )

     return client

def load_data(): 
    client = get_client()

    df = client.query_df("SELECT * FROM features_delay")

    return df


def split_by_date(df, flight_date_col): 
    dates = sorted(list(df[flight_date_col].unique()))

    cutoff = dates[int((len(dates)) * 0.8)]

    train = df[df[flight_date_col] < cutoff] 
    test = df[df[flight_date_col] >= cutoff]

    return train, test

def build_pipeline():

    preprocess = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)], remainder="passthrough")

    pipeline = Pipeline([
    ("preprocess", preprocess),
    ("model", RandomForestClassifier(**PARAMS)),
])
    return pipeline

def record_run(model_name, step, train, features, params, train_seconds, force=False):
     
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
        "Features": json.dumps(sorted(features)),
        "Params": json.dumps(params, sort_keys=True),
        "Train_Seconds": float(train_seconds),
    }])
    client.insert_df("training_runs", run)

     
def main(): 
    df = load_data()

    train, test = split_by_date(df, "Flight_Date")

    X_train, y_train = train[FEATURES], train[TARGET_LABEL]
    X_test, y_test = test[FEATURES], test[TARGET_LABEL]

    pipeline = build_pipeline()

    run_time_start = time.perf_counter()
    pipeline.fit(X_train, y_train)
    train_seconds = time.perf_counter() - run_time_start

    proba = pipeline.predict_proba(X_test)[:,1]

    pr_auc = average_precision_score(y_test, proba)
    baseline = y_test.mean()
    print(f"PR-AUC: {pr_auc:.3f} | baseline: {baseline:.3f} | lift: {pr_auc / baseline:.2f}x")
    
    joblib.dump(pipeline, ARTIFACTS_DIR /  f"{MODEL_NAME}.joblib")

    record_run(MODEL_NAME, "window", train, FEATURES, PARAMS, train_seconds)


if __name__ == "__main__":
    main()
    





