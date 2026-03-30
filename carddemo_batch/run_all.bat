@echo off
REM ============================================================================
REM CardDemo Batch Pipeline Orchestrator (Windows)
REM ============================================================================
REM Runs all four migrated COBOL batch pipelines in the correct sequential
REM order via spark-submit.  Steps 3 & 4 run sequentially on Windows
REM (no backgrounding) after Steps 1 & 2 complete.
REM
REM Prerequisites:
REM   - Apache Spark installed and SPARK_HOME set (or spark-submit on PATH)
REM   - Delta Lake jar (auto-downloaded via --packages)
REM   - Delta tables already created and loaded (see setup\ scripts)
REM
REM Usage:
REM   run_all.bat
REM   run_all.bat --schema mydb --parm-date 2025-04-01
REM   run_all.bat --start-date 2025-01-01 --end-date 2025-12-31
REM ============================================================================

setlocal enabledelayedexpansion

REM ---------------------------------------------------------------------------
REM Defaults
REM ---------------------------------------------------------------------------
set "SCHEMA=carddemo"
set "PARM_DATE="
set "START_DATE=2025-03-01"
set "END_DATE=2025-03-31"
set "OUTPUT_DIR=.\output"
set "DELTA_PACKAGE=io.delta:delta-spark_2.12:3.1.0"

REM ---------------------------------------------------------------------------
REM Parse CLI arguments
REM ---------------------------------------------------------------------------
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--schema"     ( set "SCHEMA=%~2"      & shift & shift & goto parse_args )
if /i "%~1"=="--parm-date"  ( set "PARM_DATE=%~2"    & shift & shift & goto parse_args )
if /i "%~1"=="--start-date" ( set "START_DATE=%~2"   & shift & shift & goto parse_args )
if /i "%~1"=="--end-date"   ( set "END_DATE=%~2"     & shift & shift & goto parse_args )
if /i "%~1"=="--output"     ( set "OUTPUT_DIR=%~2"   & shift & shift & goto parse_args )
if /i "%~1"=="--delta-pkg"  ( set "DELTA_PACKAGE=%~2" & shift & shift & goto parse_args )
if /i "%~1"=="-h"           goto show_help
if /i "%~1"=="--help"       goto show_help
echo Unknown option: %~1
exit /b 1

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --schema       Catalog schema / database  (default: carddemo)
echo   --parm-date    Interest calc date YYYY-MM-DD (default: today)
echo   --start-date   Report start date           (default: 2025-03-01)
echo   --end-date     Report end date             (default: 2025-03-31)
echo   --output       Output base directory       (default: .\output)
echo   --delta-pkg    Delta Lake Maven coordinate
echo   -h, --help     Show this help message
exit /b 0

:args_done

REM Default parm_date to today if not set
if "%PARM_DATE%"=="" (
    for /f "tokens=1-3 delims=/" %%a in ('date /t') do (
        set "PARM_DATE=%%c-%%a-%%b"
    )
)

REM Resolve script directory
set "SCRIPT_DIR=%~dp0"
set "PIPELINE_DIR=%SCRIPT_DIR%pipelines"

REM Resolve spark-submit
if defined SPARK_HOME (
    set "SPARK_SUBMIT=%SPARK_HOME%\bin\spark-submit"
) else (
    set "SPARK_SUBMIT=spark-submit"
)

set "COMMON_ARGS=--packages %DELTA_PACKAGE% --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog"

REM ---------------------------------------------------------------------------
REM Create output directories
REM ---------------------------------------------------------------------------
if not exist "%OUTPUT_DIR%\statements" mkdir "%OUTPUT_DIR%\statements"
if not exist "%OUTPUT_DIR%\transaction_report" mkdir "%OUTPUT_DIR%\transaction_report"

REM ============================================================================
REM Step 1: CBTRN02C - Post Daily Transactions
REM ============================================================================
echo.
echo ======================================================================
echo   Step 1/4: CBTRN02C - Post Daily Transactions
echo ======================================================================

"%SPARK_SUBMIT%" %COMMON_ARGS% ^
    "%PIPELINE_DIR%\cbtrn02c_post_daily_transactions.py" ^
    --schema %SCHEMA%

if %ERRORLEVEL% GTR 4 (
    echo FATAL: CBTRN02C failed with return code %ERRORLEVEL%. Aborting.
    exit /b %ERRORLEVEL%
)
if %ERRORLEVEL% EQU 4 (
    echo WARNING: CBTRN02C completed with warnings ^(RC=4^).
)

REM ============================================================================
REM Step 2: CBACT04C - Interest Calculator
REM ============================================================================
echo.
echo ======================================================================
echo   Step 2/4: CBACT04C - Interest Calculator
echo ======================================================================

"%SPARK_SUBMIT%" %COMMON_ARGS% ^
    "%PIPELINE_DIR%\cbact04c_interest_calculator.py" ^
    --schema %SCHEMA% ^
    --parm-date %PARM_DATE%

if %ERRORLEVEL% NEQ 0 (
    echo FATAL: CBACT04C failed with return code %ERRORLEVEL%. Aborting.
    exit /b %ERRORLEVEL%
)

REM ============================================================================
REM Step 3: CBSTM03 - Account Statements
REM ============================================================================
echo.
echo ======================================================================
echo   Step 3/4: CBSTM03 - Account Statements
echo ======================================================================

"%SPARK_SUBMIT%" %COMMON_ARGS% ^
    "%PIPELINE_DIR%\cbstm03_account_statements.py" ^
    --schema %SCHEMA% ^
    --output "%OUTPUT_DIR%\statements"

if %ERRORLEVEL% NEQ 0 (
    echo FATAL: CBSTM03 failed with return code %ERRORLEVEL%. Aborting.
    exit /b %ERRORLEVEL%
)

REM ============================================================================
REM Step 4: CBTRN03C - Transaction Detail Report
REM ============================================================================
echo.
echo ======================================================================
echo   Step 4/4: CBTRN03C - Transaction Detail Report
echo ======================================================================

"%SPARK_SUBMIT%" %COMMON_ARGS% ^
    "%PIPELINE_DIR%\cbtrn03c_transaction_report.py" ^
    --schema %SCHEMA% ^
    --start-date %START_DATE% ^
    --end-date %END_DATE% ^
    --output "%OUTPUT_DIR%\transaction_report"

if %ERRORLEVEL% NEQ 0 (
    echo FATAL: CBTRN03C failed with return code %ERRORLEVEL%. Aborting.
    exit /b %ERRORLEVEL%
)

REM ============================================================================
REM Done
REM ============================================================================
echo.
echo ======================================================================
echo   ALL PIPELINES COMPLETE
echo ======================================================================
echo Output directory: %OUTPUT_DIR%
echo   statements\            - Account statement CSVs
echo   transaction_report\    - Transaction detail report CSVs
echo.

endlocal
