@echo off
setlocal
cd "%~dp0.."

If EXIST "build\MKBot-OSS.exe" (
    cd build
    start MKBot-OSS.exe --debug
)
endlocal
