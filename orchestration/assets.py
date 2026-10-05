import subprocess
from dagster import asset

@asset
def run_collector(context):
    result = subprocess.run(
        ['python', 'collector.py'],
        capture_output=True, text= True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception("python collector run failed")

@asset(deps = ["run_collector"])
def dbt_build(context):
    result = subprocess.run(
        ["dbt", "build"],
        cwd = "dbt",
        capture_output= True, text= True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception ("dbt build failed")

@asset (deps = ["dbt_build"])
def run_rf_delay_train(context):
    result = subprocess.run(
        ["python", "train_rf_delay.py"],
        cwd = "ml",
        capture_output= True, text = True
    )
    context.log.info(result.stdout)
    if result.returncode != 0 :
        context.log.error(result.stderr)
        raise Exception ("train_rf_delay.py run failed")
