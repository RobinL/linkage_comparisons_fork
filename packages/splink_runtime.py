from splink.duckdb.duckdb_linker import DuckDBLinker
import splink.duckdb.duckdb_comparison_library as cl
import logging
import time
import pandas as pd
from  pathlib import Path
import os

logs = ["splink.estimate_u", "splink.expectation_maximisation", "splink.settings", "splink.em_training_session", "comparison_level"]
for log in logs:
    logging.getLogger(log).setLevel(logging.ERROR)


root_folder = Path(__file__).parents[1]
df_folder = root_folder / "sample_df"
results_folder = root_folder / "results"

columns = ["id", "first_name", "middle_name", "last_name", "res_street_address", "birth_year", "zip_code"]

settings = {
    "link_type": "link_only",
    "unique_id_column_name": "id",
    "comparisons": [
        cl.levenshtein_at_thresholds(col_name="first_name", distance_threshold_or_thresholds=1, include_exact_match_level=False),
        cl.levenshtein_at_thresholds(col_name="last_name", distance_threshold_or_thresholds=1, include_exact_match_level=False),
        cl.levenshtein_at_thresholds(col_name="middle_name", distance_threshold_or_thresholds=1, include_exact_match_level=False),
        cl.levenshtein_at_thresholds(col_name="res_street_address", distance_threshold_or_thresholds=1, include_exact_match_level=False),
        cl.levenshtein_at_thresholds(col_name="birth_year", distance_threshold_or_thresholds=1, include_exact_match_level=False)
    ],
    #Blocking used here
    "blocking_rules_to_generate_predictions": [
       "l.zip_code = r.zip_code"
    ]
}

x = [2000,4000,6000,8000,10000,12000,14000,16000,18000,20000,22000,24000,26000,28000,30000,32000,34000,36000,38000,40000]
for size in x:

    dfA = pd.read_csv(os.path.join(df_folder, str(size) + "_dfA.csv"), names = columns)
    dfB = pd.read_csv(os.path.join(df_folder, str(size) + "_dfB.csv"), names = columns)

    time_start = time.time()

    linker = DuckDBLinker([dfA, dfB], settings)
    linker.estimate_u_using_random_sampling(target_rows=1e6)
    training = ["l.first_name = r.first_name",
                "l.middle_name = r.middle_name",
                "l.last_name = r.last_name",
                "l.res_street_address = r.res_street_address",
                "l.birth_year = r.birth_year"
                ]

    for i in training:
        linker.estimate_parameters_using_expectation_maximisation(i)
    predict = linker.predict(0.95) #Has None as a dafault value, thus 0.95 was needed for any analysis

    time_end = time.time()

    df_predict = predict.as_pandas_dataframe()
    pairs = linker.count_num_comparisons_from_blocking_rule("l.zip_code = r.zip_code")

    false_positive = len(df_predict.loc[df_predict["id_l"] != df_predict["id_r"]])
    true_positive = len(df_predict.loc[df_predict["id_l"] == df_predict["id_r"]])
    false_negative = round(size / 2) - true_positive

    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)

    with open(os.path.join(results_folder, "test.txt"), "a") as f:
        f.writelines(
            "Sample Size: " + str(size) +
            "|Links Predicted: " + str(len(df_predict)) +
            "|Time Taken: " + str(round((time_end - time_start),2)) +
            "|Precision: " + str(precision) +
            "|Recall: " + str(recall) +
            "|Linkage Pairs: " + str(pairs) +
            "\n"
        )

    time.sleep(600)