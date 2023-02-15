@echo off
setlocal
cd "%~dp0.."

echo pylint ---------------------
pylint src/bot src/update src/lib tests
echo.
echo black ----------------------
black .
echo.
echo flake8 ---------------------
flake8 --count --show-source --statistics
echo.
echo pre-commit -----------------
pre-commit run --all-files

endlocal
