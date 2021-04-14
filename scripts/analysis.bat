@echo off
setlocal
cd "%~dp0.."

echo pylint ---------------------
pylint src tests
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
