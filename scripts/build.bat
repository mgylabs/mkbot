setlocal
cd "%~dp0.."

@ If EXIST "build" (
    rmdir /s /q build
)

@ If EXIST "build" (
    echo.
    echo Build Failed
    exit /b 1
)

mkdir build
set CI_PROJECT_DIR=%cd%

@ If /i "%1" == "--canary" (
    set CANARY_BUILD=true
    rmdir /s /q resources
    mkdir resources
    xcopy /q /I /Y /E .resources\canary\* resources
) Else IF /i "%1" == "--stable" (
    set CANARY_BUILD=false
    rmdir /s /q resources
    mkdir resources
    xcopy /q /I /Y /E .resources\stable\* resources
)

xcopy /q /I /Y /E package\data build\data
xcopy /q /I /Y /E package\info build\info
xcopy /q /I /Y resources\app build\resources\app

cd src\bot
@ If /i "%1" == "--clean" (
    rmdir /s /q build
    rmdir /s /q dist
    pyinstaller main.spec -y --clean || goto :error
) Else (
    pyinstaller main.spec -y || goto :error
)

move dist\bin ..\..\build

@ If /i "%1" == "--test-bot" (
    cd %CI_PROJECT_DIR%
    xcopy /q /I /Y src\data build\data
    cd build\bin
    start cmd /k "MKBotCore.exe --debug --test-bot & cd ..\.. & pause & exit"
    echo.
    echo Start MK Bot in Test Mode
    exit /b 0
)

cd %CI_PROJECT_DIR%\src\console
@ If DEFINED GITHUB_ACTIONS (
    nuget restore console.sln
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe" console.sln /clp:Summary /v:m /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None /p:Oss=false /p:Canary=%CANARY_BUILD% || goto :error
) Else (
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" console.sln /clp:Summary /v:m /p:Configuration=Release /p:AllowedReferenceRelatedFileExtensions=none /p:DebugType=None /p:Oss=true || goto :error
)
move bin\Release\* ..\..\build

cd %CI_PROJECT_DIR%\build
del *.pdb

cd %CI_PROJECT_DIR%
pybabel compile -d locales -D mkbot

@echo.
@echo Build Succeeded
@exit /b 0

:error
    @echo.
    @echo Build Failed
    @exit /b %errorlevel%

endlocal
