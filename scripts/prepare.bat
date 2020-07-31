cd "%~dp0.."
xcopy /I /Y /E package\data src\data
xcopy /I /Y /E package\info src\info
xcopy /I /Y /E extensions src\bot\extensions
xcopy /I /Y /E package\data src\console\bin\Debug\data
xcopy /I /Y /E package\info src\console\bin\Debug\info