pyinstaller ".\src\cli_app.py" -n "dogaas-cli" -p ".\src" -F
Copy-Item -Path ".\src\config.json" -Destination ".\dist" -Force
Copy-Item -Path ".\src\i18n" -Destination ".\dist" -Recurse -Force
