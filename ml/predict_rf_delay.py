from pathlib import Path
import joblib
from train_rf_delay import load_data, split_by_date, FEATURES, TARGET_LABEL
from datetime import datetime
import clickhouse_connect
import os
from sklearn.metrics import average_precision_score
import pandas as pd

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH    = ARTIFACTS_DIR / "rf_delay_v1.joblib"
MODEL_NAME = "rf_v1"


def build_results (test, probability_predict):

    results = test[["Flight_Number", "Flight_Date", "Reporting_Airline", "Origin_Airport", "Destination_Airport"]].copy()
    results["Delay_Probability"] = probability_predict
    results["Is_Dep_Delay_Greater_Than_15"] = test[TARGET_LABEL]
    results["Model_Name"] = "rf_v1"
    results["Scored_At"] = datetime.now()

    return results


def write_predictions_into_table(results): 

    client = clickhouse_connect.get_client(
            host = "localhost",
            port = 8123,
            username = os.environ["CLICKHOUSE_USER"],
            password = os.environ["CLICKHOUSE_PASSWORD"],
            database = os.environ["CLICKHOUSE_DB"]
        )

    client.command("""
    CREATE TABLE IF NOT EXISTS delay_predictions (
        Flight_Number                String,
        Flight_Date                  Date,
        Reporting_Airline            String,
        Origin_Airport               String,
        Destination_Airport          String,
        Delay_Probability            Float64,
        Is_Dep_Delay_Greater_Than_15 UInt8,
        Model_Name                   String,
        Scored_At                    DateTime
    )
    ENGINE = MergeTree
    ORDER BY (Flight_Date, Reporting_Airline, Flight_Number)
""")

    client.command("TRUNCATE TABLE delay_predictions")
    client.insert_df("delay_predictions", results)

def write_metrics_into_table(model_name, baseline_probability, pr_auc):
    client = clickhouse_connect.get_client(
                host = "localhost",
                port = 8123,
                username = os.environ["CLICKHOUSE_USER"],
                password = os.environ["CLICKHOUSE_PASSWORD"],
                database = os.environ["CLICKHOUSE_DB"]
            )

    client.command("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            Model_Name                   String,
            Metric                       String,
            Value                        Float64,
            Evaluated_At                 DateTime,
        )
        ENGINE = MergeTree
        ORDER BY (Model_Name, Metric)
    """)
    client.command(
    "ALTER TABLE model_metrics DELETE WHERE Model_Name = {model:String} SETTINGS mutations_sync = 1",
    parameters={"model": model_name},
)

    metrics = pd.DataFrame({
        "Model_Name":   model_name,                          #
        "Metric":       ["pr_auc", "baseline_pr_auc"],
        "Value":        [pr_auc, baseline_probability],
        "Evaluated_At": datetime.now(),
    })

    client.insert_df("model_metrics", metrics)

def main():
    pipeline = joblib.load(MODEL_PATH)

    df = load_data()
    _, test = split_by_date(df,"Flight_Date")

    X_test = test[FEATURES]
    y_test = test[TARGET_LABEL]

    probability_predict = pipeline.predict_proba(X_test)[:,1]

    results = build_results(test, probability_predict)

    write_predictions_into_table(results)

    print(f"{len(X_test)} row written into delay_predictions table")

    baseline = y_test.mean()
    pr_auc = average_precision_score(y_test, probability_predict)

    write_metrics_into_table(MODEL_NAME, baseline, pr_auc)

    print(f"Written rows into model_metrics")

if __name__ == "__main__":
    main()