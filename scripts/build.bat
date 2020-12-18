cd "%~dp0.."

python -m pip install --upgrade pip

@ If EXIST "build" (
    rmdir /s /q build
)

@ If EXIST "build" (
    echo.
    echo Build Failed
    exit /b 1
)

pip install -r requirements.txt || goto :error

mkdir build
set CI_PROJECT_DIR=%cd%

xcopy /q /I /Y /E package\data build\data
xcopy /q /I /Y /E package\info build\info
xcopy /q /I /Y resources\app build\resources\app

cd src\bot
pyinstaller app.spec --log-level WARN || goto :error
move dist\app ..\..\build

@ If /i "%1" == "--test-bot" (
    cd %CI_PROJECT_DIR%
    xcopy /q /I /Y src\data build\data
    cd build\app
    start cmd /k "app.exe --debug & pause & exit"
    echo.
    echo Start MK Bot in Test Mode
    exit /b 0
)

cd ..\console
@ If DEFINED GITHUB_ACTIONS (
    nuget restore console.sln
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe" console.sln /clp:Summary /v:m /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None || goto :error
) Else (
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" console.sln /clp:Summary /v:m /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None || goto :error
)
move bin\Release\* ..\..\build

cd ..\msu
pyinstaller msu.spec --log-level WARN || goto :error
move "dist\msu" ..\..\build\Update

cd %CI_PROJECT_DIR%\build
xcopy /q /I /Y /E Update\* app
del *.pdb
rmdir /q /s Update

exit /b 0

:error
    @echo.
    @echo Build Failed
    @exit /b %errorlevel%
