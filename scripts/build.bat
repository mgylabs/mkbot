cd "%~dp0.."
rmdir /s /q build
mkdir build
set CI_PROJECT_DIR=%cd%
xcopy /I /Y /E package\data build\data
xcopy /I /Y package\info build\info
cd src\bot
set botpackage=..\..\.venv\Lib\site-packages
pyinstaller app.spec
move dist\app ..\..\build
cd ..\console
C:\Windows\Microsoft.NET\Framework\v4.0.30319\msbuild console.sln /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None
move bin\Release\* ..\..\build
cd ..\msu
pyinstaller --icon=..\..\package\mkbot_install.ico "Mulgyeol Software Update.py"
move "dist\Mulgyeol Software Update" ..\..\build\Update
cd %CI_PROJECT_DIR%\build
xcopy /I /Y /E Update\* app
rmdir /s /q Update