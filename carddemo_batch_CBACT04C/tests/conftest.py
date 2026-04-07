"""
Shared pytest fixtures for CBACT04C tests.

Uses a local SparkSession with Delta Lake enabled.
All Delta table operations use in-memory paths under a temporary directory.
"""

import os
import tempfile

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """
    Session-scoped SparkSession with Delta Lake configured.

    Uses local mode with a temporary warehouse directory so tests run
    without a Databricks cluster.
    """
    warehouse_dir = tempfile.mkdtemp(prefix="cbact04c_test_warehouse_")

    spark = (
        SparkSession.builder.master("local[2]")
        .appName("cbact04c_tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", warehouse_dir)
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        # Disable unnecessary Spark UI in tests
        .config("spark.ui.enabled", "false")
        # Deterministic aggregation for test assertions
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()


@pytest.fixture(scope="session")
def tmp_catalog(spark, tmp_path_factory):
    """
    Create temporary Delta tables that mirror the carddemo catalog schemas.
    Returns a dict of table paths keyed by logical name.
    """
    base = str(tmp_path_factory.mktemp("delta_tables"))
    return base
