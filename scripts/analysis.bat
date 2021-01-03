@echo off
setlocal
cd "%~dp0.."

echo pylint ---------------------
pylint src tests -d R,C,W,F0010 --init-hook="import sys, os; sys.path.extend(['./src/bot', './src/msu'])" -s n -f colorized
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
