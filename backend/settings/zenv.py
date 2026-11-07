from pathlib import Path

from decouple import AutoConfig

# no container do app, o arquivo backend_data está fora da pasta do projeto, dentro de ROOT_HOME.
# Isso permite que as configurações de produção sejam carregadas corretamente sem depender do diretório do projeto dentro do container.
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

if not production:
    print("--------------------------- ENVIRONMENT ---------------------------")
    print("Production environment:", production)
    print("DEBUG:", DEBUG)
    print("BASE_DIR:", BASE_DIR)
    print("PROJECT_DIR:", PROJECT_DIR)
    print("-------------------------------------------------------------------")
