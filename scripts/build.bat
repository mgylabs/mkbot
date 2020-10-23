cd "%~dp0.."

rmdir /s /q build
@ If EXIST "build" (
    echo.
    echo Build Failed
    exit /b 1
)

pip install -r requirements.txt || goto :error

mkdir build
set CI_PROJECT_DIR=%cd%

xcopy /I /Y /E package\data build\data
xcopy /I /Y /E package\info build\info
xcopy /I /Y resources build\resources

cd src\bot
set botpackage=..\..\.venv\Lib\site-packages
pyinstaller app.spec || goto :error
move dist\app ..\..\build

cd ..\console
"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" console.sln /clp:Summary /v:m /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None || goto :error
echo %errorlevel%
move bin\Release\* ..\..\build

cd ..\msu
pyinstaller --icon=..\..\package\mkbot_install.ico "Mulgyeol Software Update.py" || goto :error
move "dist\Mulgyeol Software Update" ..\..\build\Update

cd %CI_PROJECT_DIR%\build
xcopy /I /Y /E Update\* app
del *.pdb
rmdir /s /q Update

@ If /i "%1" == "--test-bot" (
    cd %CI_PROJECT_DIR%
    xcopy /I /Y src\data build\data
    cd build\app
    start cmd /k "app.exe & pause & exit"
    echo.
    echo Start MK Bot in Test Mode
    exit /b 0
)

:error
    @echo.
    @echo Build Failed
    @exit /b %errorlevel%
