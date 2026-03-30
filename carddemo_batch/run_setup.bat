@echo off
REM ============================================================================
REM Run SQL setup scripts via spark-sql to create and populate Delta tables.
REM
REM Usage:
REM   run_setup.bat
REM   run_setup.bat --warehouse C:\path\to\warehouse
REM ============================================================================

setlocal enabledelayedexpansion

set "DELTA_PACKAGE=io.delta:delta-spark_2.12:3.1.0"
set "WAREHOUSE_DIR=.\spark-warehouse"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--warehouse"  ( set "WAREHOUSE_DIR=%~2" & shift & shift & goto parse_args )
if /i "%~1"=="--delta-pkg"  ( set "DELTA_PACKAGE=%~2"  & shift & shift & goto parse_args )
if /i "%~1"=="-h"           goto show_help
if /i "%~1"=="--help"       goto show_help
echo Unknown option: %~1
exit /b 1

:show_help
echo Usage: %~nx0 [--warehouse DIR] [--delta-pkg PKG]
exit /b 0

:args_done

set "SCRIPT_DIR=%~dp0"

if defined SPARK_HOME (
    set "SPARK_SQL=%SPARK_HOME%\bin\spark-sql"
) else (
    set "SPARK_SQL=spark-sql"
)

set "COMMON_ARGS=--packages %DELTA_PACKAGE% --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.sql.warehouse.dir=%WAREHOUSE_DIR%"

echo ======================================================================
echo   Creating Delta tables ...
echo ======================================================================
"%SPARK_SQL%" %COMMON_ARGS% -f "%SCRIPT_DIR%setup\01_create_tables.sql"

echo.
echo ======================================================================
echo   Loading sample data ...
echo ======================================================================
"%SPARK_SQL%" %COMMON_ARGS% -f "%SCRIPT_DIR%setup\02_load_sample_data.sql"

echo.
echo ======================================================================
echo   Setup complete.  Tables created in: %WAREHOUSE_DIR%
echo ======================================================================

endlocal
