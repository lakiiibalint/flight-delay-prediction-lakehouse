from pathlib import Path
import joblib
from train_rf_delay import load_data, split_by_date, FEATURES, TARGET_LABEL
from datetime import datetime
import clickhouse_connect
import os

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH    = ARTIFACTS_DIR / "rf_delay_v1.joblib"


def build_results (test, proba):

    results = test[["Flight_Number", "Flight_Date", "Reporting_Airline", "Origin_Airport", "Destination_Airport"]].copy()
    results["Delay_Probability"] = proba
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

def main():
    pipeline = joblib.load(MODEL_PATH)

    df = load_data()
    _, test = split_by_date(df,"Flight_Date")

    X_test = test[FEATURES]
    proba = pipeline.predict_proba(X_test)[:,1]

    results = build_results(test, proba)

    write_predictions_into_table(results)

    print(f"{len(X_test)} row written into delay_predictions table")

if __name__ == "__main__":
    main()