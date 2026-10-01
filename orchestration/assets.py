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
def dbt_run(context):
    result = subprocess.run(
        ["dbt", "run"],
        cwd = "dbt",
        capture_output= True, text= True
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception ("dbt build failed")

@asset(deps = ["dbt_run"])
def dbt_test(context):
    result = subprocess.run(
        ["dbt","test"],
        cwd = "dbt",
        capture_output=True, text= True
    )
    context.log.info(result.stdout)
    if result.returncode != 0 :
        raise Exception ("dbt tests failed")


