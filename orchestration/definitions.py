import dagster as dg

from orchestration import assets

# Everything decorated with @dg.asset in assets.py is registered automatically.
defs = dg.Definitions(
    assets=dg.load_assets_from_modules([assets]),
)
