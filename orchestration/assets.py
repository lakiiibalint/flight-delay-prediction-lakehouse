import subprocess
from pathlib import Path
from dagster import asset
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets


DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt"
dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR)
dbt_resource = DbtCliResource(project_dir=dbt_project)

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
    
@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models (context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset (deps = ["features_delay"])
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

@asset (deps = ["run_rf_delay_train"])
def run_rf_delay_predict(context):
    result = subprocess.run(
        ["python", "predict_rf_delay.py"],
        cwd = "ml",
        capture_output=True, text=True
                            )
    context.log.info(result.stdout)
    if result.returncode != 0 :
        context.log.error(result.stderr)
        raise Exception ("run_rf_delay_predict.py run failed")