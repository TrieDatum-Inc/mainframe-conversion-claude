#!/usr/bin/env bash
# ============================================================================
# Run SQL setup scripts via spark-sql to create and populate Delta tables.
#
# Usage:
#   chmod +x run_setup.sh
#   ./run_setup.sh                        # defaults
#   ./run_setup.sh --warehouse /path/to/warehouse
# ============================================================================

set -euo pipefail

DELTA_PACKAGE="io.delta:delta-spark_2.12:3.1.0"
WAREHOUSE_DIR="./spark-warehouse"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --warehouse)   WAREHOUSE_DIR="$2"; shift 2 ;;
        --delta-pkg)   DELTA_PACKAGE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--warehouse DIR] [--delta-pkg PKG]"
            exit 0 ;;
        *)  echo "Unknown option: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPARK_SQL="${SPARK_HOME:+${SPARK_HOME}/bin/}spark-sql"

COMMON_ARGS=(
    --packages "${DELTA_PACKAGE}"
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension"
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog"
    --conf "spark.sql.warehouse.dir=${WAREHOUSE_DIR}"
)

echo "======================================================================"
echo "  Creating Delta tables ..."
echo "======================================================================"
"${SPARK_SQL}" "${COMMON_ARGS[@]}" -f "${SCRIPT_DIR}/setup/01_create_tables.sql"

echo ""
echo "======================================================================"
echo "  Loading sample data ..."
echo "======================================================================"
"${SPARK_SQL}" "${COMMON_ARGS[@]}" -f "${SCRIPT_DIR}/setup/02_load_sample_data.sql"

echo ""
echo "======================================================================"
echo "  Setup complete.  Tables created in: ${WAREHOUSE_DIR}"
echo "======================================================================"
