@echo off
setlocal
cd "%~dp0.."

alembic %*

endlocal
