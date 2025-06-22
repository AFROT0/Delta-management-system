@echo off
echo Installing the latest versions of packages...

:: Update pip to the latest version
python -m pip install --upgrade pip

:: Install packages from requirements.txt
pip install -r requirements.txt

:: Check for errors
if errorlevel 1 (
    echo An error occurred! Please check:
    echo 1- Run the script as Administrator.
    echo 2- Ensure Python is installed and added to PATH.
    pause
    exit
)

echo Installation completed successfully!
pause