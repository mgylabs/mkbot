@echo off
setlocal
cd "%~dp0.."

python -m unittest discover -v -s tests -p test_*.py
endlocal
