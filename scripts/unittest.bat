@echo off
cd "%~dp0.."

python -m unittest discover -v -s tests -p test_*.py