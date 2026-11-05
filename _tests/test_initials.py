import re
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db


def test_app_init_files_have_default_app_config():
    """
    Verifica se todos os apps Django dentro do diretório backend possuem:
    1. Um arquivo __init__.py
    2. Uma variável default_app_config nesse arquivo
    3. O valor aponta para uma classe AppConfig dentro do arquivo apps.py
    """
    # Diretório base do projeto
    backend_dir = Path(".")

    # Encontra todos os diretórios que podem ser apps Django
    app_dirs = [
        d
        for d in backend_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    ]

    # Verifica se há diretórios para testar
    assert app_dirs, "Não foram encontrados diretórios que possam ser apps Django"

    for app_dir in app_dirs:
        app_name = app_dir.name

        if f"backend.{app_name}" not in settings.INSTALLED_APPS:
            # Ignora diretórios que não são apps Django
            continue

        # 1. Verifica se existe um __init__.py
        init_file = app_dir / "__init__.py"
        assert (
            init_file.exists()
        ), f"O diretório {app_name} não possui um arquivo __init__.py"

        # Lê o conteúdo do arquivo __init__.py
        with open(init_file, "r") as f:
            init_content = f.read()

        # 2. Verifica se contém a variável default_app_config
        assert (
            "default_app_config" in init_content
        ), f"O arquivo {app_name}/__init__.py não define a variável default_app_config"

        # Extrai o valor da variável default_app_config
        match = re.search(r"default_app_config\s*=\s*['\"]([^'\"]+)['\"]", init_content)
        assert (
            match
        ), f"Formato inválido da variável default_app_config em {app_name}/__init__.py"

        config_path = match.group(1)

        # 3. Verifica se aponta para um módulo apps
        expected_prefix = f"backend.{app_name}.apps."
        assert config_path.startswith(
            expected_prefix
        ), f"Em {app_name}/__init__.py, default_app_config deve começar com '{expected_prefix}'"

        # Extrai o nome da classe
        class_name = config_path[len(expected_prefix) :]

        # Verifica se o arquivo apps.py existe
        apps_file = app_dir / "apps.py"
        assert (
            apps_file.exists()
        ), f"O diretório {app_name} não possui um arquivo apps.py"

        # Verifica se a classe existe no apps.py
        with open(apps_file, "r") as f:
            apps_content = f.read()

        class_pattern = rf"class\s+{class_name}\s*\("
        assert re.search(
            class_pattern, apps_content
        ), f"O arquivo {app_name}/apps.py não contém a definição da classe {class_name}"
