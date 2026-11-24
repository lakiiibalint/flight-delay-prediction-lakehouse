from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from common import (
    TARGET_LABEL, FEATURES, CATEGORICAL, VAL_START, VAL_END, TRAIN_END,
    changed_params, train_start_for, select_period, load_data,
    fit_model, evaluate, report, persist,
)

PARAMS = {"random_state": 42, "n_jobs": -1, "n_estimators": 100, "max_depth": 25, "min_samples_leaf": 50, "max_features": 0.3}
YEARS = 1
TAG = "mf0.3_depth_25"
STEP = "tuning"
FRACTIONS = {"25": 0.25}


def main():
    df = load_data(YEARS)

    train = select_period(df, train_start_for(YEARS), TRAIN_END)
    validation = select_period(df, VAL_START, VAL_END)

    preprocess = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)],
        remainder="passthrough")

    for key, fraction in FRACTIONS.items():
        subset = train.sample(frac=fraction, random_state=PARAMS["random_state"]).sort_index()
        model_name = f"rf_delay_y{YEARS}_f{key}_{TAG}"
        model = RandomForestClassifier(**PARAMS)
        params = changed_params(model)

        pipeline, train_seconds = fit_model(model, subset, preprocess)
        train_metrics = evaluate(pipeline, subset)
        val_metrics = evaluate(pipeline, validation)

        report(model_name, len(subset), train_metrics, val_metrics, train_seconds)
        persist(model_name, STEP, pipeline, subset, validation, params, train_seconds, train_metrics, val_metrics)


if __name__ == "__main__":
    main()