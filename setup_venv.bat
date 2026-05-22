@echo off
setlocal

python -m venv .venv
if errorlevel 1 (
    echo Failed to create virtual environment. Ensure Python is installed and on PATH.
    exit /b 1
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Virtual environment created in .venv
if exist .env (
    echo Found existing .env file.
) else (
    echo Copy .env.example to .env and fill your secrets.
    echo    copy .env.example .env
)
echo Activate it with:
if exist .venv\Scripts\activate (
    echo    .venv\Scripts\activate
)
echo Run the app with:
echo    .venv\Scripts\python main_improved.py
exit /b 0
