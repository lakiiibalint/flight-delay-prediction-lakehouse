WITH metrics AS (
    SELECT
        Model_Name,
        maxIf(Value, Split = 'validation' AND Metric = 'pr_auc')          AS val_pr_auc,
        maxIf(Value, Split = 'train'      AND Metric = 'pr_auc')          AS train_pr_auc,
        maxIf(Value, Split = 'validation' AND Metric = 'baseline_pr_auc') AS val_baseline_pr_auc,
        maxIf(Value, Split = 'train' AND Metric = 'baseline_pr_auc')      AS train_baseline_pr_auc
     FROM {{ source('ml', 'model_metrics') }}
    GROUP BY Model_Name
)


SELECT
    tr.Model_Name       AS Model_Name,
    tr.Step             AS Step,
    tr.Train_Start      AS Train_Start,
    tr.Train_End        AS Train_End,
    tr.Train_Rows       AS Train_Rows,
    tr.Train_Seconds    AS Train_Seconds,
    tr.Features         AS Features,
    tr.Params         AS Params,
    m.val_pr_auc       AS val_pr_auc,  
    m.train_pr_auc     AS train_pr_auc,
    m.val_baseline_pr_auc  AS val_baseline_pr_auc,
    m.val_pr_auc / m.val_baseline_pr_auc AS val_lift,   
    m.train_pr_auc / m.train_baseline_pr_auc AS train_lift   
FROM {{ source('ml', 'training_runs') }} tr
INNER JOIN metrics AS m ON tr.Model_Name = m.Model_Name