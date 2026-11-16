from definitions import defs
from dagster import Definitions
Definitions.validate_loadable(defs)
print("Dagster definitions validated; no sync or database build was triggered.")
