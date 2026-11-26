from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from common import (
    TARGET_LABEL, FEATURES, CATEGORICAL, VAL_START, VAL_END, TRAIN_END,
    changed_params, train_start_for, select_period, load_data,
    fit_model, evaluate, report, persist,
)
import numpy as np

CAT_MASK = [True] * len(CATEGORICAL) + [False] * (len(FEATURES) - len(CATEGORICAL))

PARAMS = {"random_state": 42, "learning_rate": 0.1, "max_iter": 100, "max_leaf_nodes": 31, 
          "min_samples_leaf": 20, "early_stopping": False, "categorical_features" : CAT_MASK}
YEARS = 1
TAG = "curve_default"
STEP = "curve"
FRACTIONS = {"12.5": 0.125, "25": 0.25, "50": 0.5, "100": 1.0}


def main():
    df = load_data(YEARS)

    train = select_period(df, train_start_for(YEARS), TRAIN_END)
    validation = select_period(df, VAL_START, VAL_END)

    preprocess = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan,
                                max_categories=254), CATEGORICAL)],
        remainder="passthrough")

    for key, fraction in FRACTIONS.items():
        subset = train.sample(frac=fraction, random_state=PARAMS["random_state"]).sort_index()
        model_name = f"gb_delay_y{YEARS}_f{key}_{TAG}"
        model = HistGradientBoostingClassifier(**PARAMS)
        params = changed_params(model)

        pipeline, train_seconds = fit_model(model, subset, preprocess)
        train_metrics = evaluate(pipeline, subset)
        val_metrics = evaluate(pipeline, validation)

        report(model_name, len(subset), train_metrics, val_metrics, train_seconds)
        persist(model_name, STEP, pipeline, subset, validation, params, train_seconds, train_metrics, val_metrics)


if __name__ == "__main__":
    main()