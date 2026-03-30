#!/usr/bin/env bash
# ============================================================================
# CardDemo Batch Pipeline Orchestrator
# ============================================================================
# Runs all four migrated COBOL batch pipelines in the correct sequential
# order via spark-submit.  Steps 3 & 4 are read-only reports and execute
# in parallel after Steps 1 & 2 complete.
#
# Prerequisites:
#   - Apache Spark installed and SPARK_HOME set (or spark-submit on PATH)
#   - Delta Lake jar (auto-downloaded via --packages)
#   - Delta tables already created and loaded (see setup/ scripts)
#
# Usage:
#   chmod +x run_all.sh
#   ./run_all.sh                                     # all defaults
#   ./run_all.sh --schema mydb --parm-date 2025-04-01
#   ./run_all.sh --start-date 2025-01-01 --end-date 2025-12-31
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults (override via CLI flags)
# ---------------------------------------------------------------------------
SCHEMA="carddemo"
PARM_DATE="$(date +%Y-%m-%d)"
START_DATE="2025-03-01"
END_DATE="2025-03-31"
OUTPUT_DIR="./output"
DELTA_PACKAGE="io.delta:delta-spark_2.12:3.1.0"

# ---------------------------------------------------------------------------
# Parse CLI arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --schema)      SCHEMA="$2";      shift 2 ;;
        --parm-date)   PARM_DATE="$2";   shift 2 ;;
        --start-date)  START_DATE="$2";  shift 2 ;;
        --end-date)    END_DATE="$2";    shift 2 ;;
        --output)      OUTPUT_DIR="$2";  shift 2 ;;
        --delta-pkg)   DELTA_PACKAGE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --schema       Catalog schema / database  (default: carddemo)"
            echo "  --parm-date    Interest calc date YYYY-MM-DD (default: today)"
            echo "  --start-date   Report start date           (default: 2025-03-01)"
            echo "  --end-date     Report end date             (default: 2025-03-31)"
            echo "  --output       Output base directory       (default: ./output)"
            echo "  --delta-pkg    Delta Lake Maven coordinate (default: ${DELTA_PACKAGE})"
            echo "  -h, --help     Show this help message"
            exit 0 ;;
        *)  echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Resolve the directory where this script lives (portable)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="${SCRIPT_DIR}/pipelines"

# ---------------------------------------------------------------------------
# Common spark-submit flags
# ---------------------------------------------------------------------------
SPARK_SUBMIT="${SPARK_HOME:+${SPARK_HOME}/bin/}spark-submit"

COMMON_ARGS=(
    --packages "${DELTA_PACKAGE}"
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension"
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog"
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
banner() {
    echo ""
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
}

check_rc() {
    local rc=$1
    local step_name=$2
    if [ "${rc}" -ne 0 ] && [ "${rc}" -ne 4 ]; then
        echo "FATAL: ${step_name} failed with return code ${rc}. Aborting."
        exit "${rc}"
    fi
    if [ "${rc}" -eq 4 ]; then
        echo "WARNING: ${step_name} completed with warnings (RC=4)."
    fi
}

# ---------------------------------------------------------------------------
# Create output directories
# ---------------------------------------------------------------------------
mkdir -p "${OUTPUT_DIR}/statements" "${OUTPUT_DIR}/transaction_report"

# ============================================================================
# Step 1: CBTRN02C - Post Daily Transactions
# ============================================================================
banner "Step 1/4: CBTRN02C - Post Daily Transactions"

"${SPARK_SUBMIT}" "${COMMON_ARGS[@]}" \
    "${PIPELINE_DIR}/cbtrn02c_post_daily_transactions.py" \
    --schema "${SCHEMA}"
check_rc $? "CBTRN02C"

# ============================================================================
# Step 2: CBACT04C - Interest Calculator
# ============================================================================
banner "Step 2/4: CBACT04C - Interest Calculator"

"${SPARK_SUBMIT}" "${COMMON_ARGS[@]}" \
    "${PIPELINE_DIR}/cbact04c_interest_calculator.py" \
    --schema "${SCHEMA}" \
    --parm-date "${PARM_DATE}"
check_rc $? "CBACT04C"

# ============================================================================
# Steps 3 & 4: Reports (can run in parallel - read-only)
# ============================================================================
banner "Steps 3+4: Reports (parallel execution)"

# Step 3: CBSTM03 - Account Statements (background)
"${SPARK_SUBMIT}" "${COMMON_ARGS[@]}" \
    "${PIPELINE_DIR}/cbstm03_account_statements.py" \
    --schema "${SCHEMA}" \
    --output "${OUTPUT_DIR}/statements" &
PID_STMT=$!

# Step 4: CBTRN03C - Transaction Detail Report (background)
"${SPARK_SUBMIT}" "${COMMON_ARGS[@]}" \
    "${PIPELINE_DIR}/cbtrn03c_transaction_report.py" \
    --schema "${SCHEMA}" \
    --start-date "${START_DATE}" \
    --end-date "${END_DATE}" \
    --output "${OUTPUT_DIR}/transaction_report" &
PID_RPT=$!

# Wait for both report jobs
STMT_RC=0; wait ${PID_STMT} || STMT_RC=$?
RPT_RC=0;  wait ${PID_RPT}  || RPT_RC=$?

check_rc ${STMT_RC} "CBSTM03 (Account Statements)"
check_rc ${RPT_RC}  "CBTRN03C (Transaction Report)"

# ============================================================================
# Done
# ============================================================================
banner "ALL PIPELINES COMPLETE"
echo "Output directory: ${OUTPUT_DIR}"
echo "  statements/            - Account statement CSVs"
echo "  transaction_report/    - Transaction detail report CSVs"
echo ""
