@echo off
setlocal
cd "%~dp0.."

set ch_title=
set ch_type=
set ch_pr=

:title
set /p ch_title="Title> "

if "%ch_title%" == "" (
    echo Title is required.
    goto :title
)

echo.
set /p ch_pr="Pull Request Number> "

echo.
:select
echo Please specify the category of your change:
echo 1. Feature
echo 2. Change
echo 3. Bug Fix
echo 4. Other
echo.

set /p num="Number> "
if "%num%" == "1" (
    set ch_type= features
) else if "%num%" == "2" (
    set ch_type= changes
) else if "%num%" == "3" (
    set ch_type= bug fixes
) else if "%num%" == "4" (
    set ch_type= others
) else (
    goto :select
)


if "%ch_pr%" == "" (
    set ch_filename="changelogs\unreleased\%ch_title: =-%.yml"
) else (
    set ch_filename="changelogs\unreleased\%ch_pr%-%ch_title: =-%.yml"
    set "ch_pr= %ch_pr%"
)

set "ch_title= %ch_title%"

>"%ch_filename%" (
    echo ---
    echo title:%ch_title%
    echo pull_request:%ch_pr%
    echo type:%ch_type%
)

echo.
echo A changelog was created at %ch_filename%
endlocal
