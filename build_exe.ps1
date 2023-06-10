poetry run python -m py
pyinstaller ".\dogaas_cli.spec"
Copy-Item -Path ".\src\config.json" -Destination ".\dist"
Copy-Item -Path ".\src\i18n" -Destination ".\dist" -Recurse
