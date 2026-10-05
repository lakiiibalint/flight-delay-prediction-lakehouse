import os
import clickhouse_connect
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path

FEATURES = ["Reporting_Airline", "Origin_Airport", "Destination_Airport", "Hour_Of_Departure"] 
TARGET_LABEL = "Is_Dep_Delay_Greater_Than_15"
CATEGORICAL = ["Reporting_Airline", "Origin_Airport", "Destination_Airport"]
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

def load_data(): 
    client = clickhouse_connect.get_client(
        host = "localhost",
        port = 8123,
        username = os.environ["CLICKHOUSE_USER"],
        password = os.environ["CLICKHOUSE_PASSWORD"],
        database = os.environ["CLICKHOUSE_DB"]
    )

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
    ("model", RandomForestClassifier(random_state=42, n_jobs=-1, n_estimators=500, max_depth=15, min_samples_leaf=50 )),
])
    return pipeline


def main(): 
    df = load_data()

    train, test = split_by_date(df, "Flight_Date")

    X_train, y_train = train[FEATURES], train[TARGET_LABEL]
    X_test, y_test = test[FEATURES], test[TARGET_LABEL]

    pipeline = build_pipeline()

    pipeline.fit(X_train, y_train)

    proba = pipeline.predict_proba(X_test)[:,1]

    pr_auc = average_precision_score(y_test, proba)
    baseline = y_test.mean()
    print(f"PR-AUC: {pr_auc:.3f} | baseline: {baseline:.3f} | lift: {pr_auc / baseline:.2f}x")
    
    joblib.dump(pipeline, ARTIFACTS_DIR / "rf_delay_v1.joblib")


if __name__ == "__main__":
    main()
    





