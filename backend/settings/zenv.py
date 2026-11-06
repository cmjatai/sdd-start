from pathlib import Path

from decouple import AutoConfig

# backend_data está fora da pasta do projeto, dentro de ROOT_HOME.
production = Path(__file__).parents[3] / "backend_data" / ".env"
production = production.exists()

config = AutoConfig(
    search_path=(Path(__file__).parents[3] / "backend_data" if production else None)
)

DEBUG = config("DEBUG", default=False, cast=bool)

BASE_DIR = Path(__file__).parents[1]
PROJECT_DIR = Path(__file__).parents[2]

FOLDER_DEBUG_CONTAINER = Path(
    config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str)
)

print("--------------------------- ENVIRONMENT ---------------------------")
print("Production environment:", production)
print("DEBUG:", DEBUG)
print("BASE_DIR:", BASE_DIR)
print("PROJECT_DIR:", PROJECT_DIR)
print("-------------------------------------------------------------------")
