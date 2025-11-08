"""
PySpark Integration for Distributed Processing

Provides Spark session management and distributed data operations.
"""

import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import DataFrame as SparkDataFrame
    import pyspark.sql.functions as F
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, TimestampType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    # Define dummy types for type hints when PySpark not available
    if TYPE_CHECKING:
        from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
        from pyspark.sql.types import StructType
    else:
        SparkSession = Any
        SparkDataFrame = Any
        StructType = Any
    logger.warning("PySpark not available - distributed processing disabled")


class SparkSessionManager:
    """
    Manages Spark sessions with configurable resources.

    Features:
    - Session creation and lifecycle management
    - Resource configuration
    - Graceful shutdown
    """

    def __init__(
        self,
        app_name: str = "NBA_MCP_Analytics",
        master: str = "local[*]",  # local mode by default
        executor_memory: str = "2g",
        driver_memory: str = "2g",
        executor_cores: int = 2,
        config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Spark session manager.

        Args:
            app_name: Name for Spark application
            master: Spark master URL (e.g., "local[*]", "spark://host:port")
            executor_memory: Memory per executor
            driver_memory: Memory for driver
            executor_cores: Cores per executor
            config: Additional Spark configuration
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is not installed. Install with: pip install pyspark")

        self.app_name = app_name
        self.master = master
        self.executor_memory = executor_memory
        self.driver_memory = driver_memory
        self.executor_cores = executor_cores
        self.additional_config = config or {}

        self._spark: Optional[SparkSession] = None

        logger.info(f"SparkSessionManager initialized (app={app_name}, master={master})")

    def get_or_create_session(self) -> SparkSession:
        """
        Get existing Spark session or create new one.

        Returns:
            Active SparkSession
        """
        if self._spark is not None:
            return self._spark

        logger.info("Creating new Spark session")

        builder = (
            SparkSession.builder
            .appName(self.app_name)
            .master(self.master)
            .config("spark.executor.memory", self.executor_memory)
            .config("spark.driver.memory", self.driver_memory)
            .config("spark.executor.cores", str(self.executor_cores))
        )

        # Add additional configurations
        for key, value in self.additional_config.items():
            builder = builder.config(key, value)

        self._spark = builder.getOrCreate()

        logger.info(
            f"Spark session created: {self._spark.version}, "
            f"master={self.master}, "
            f"executors={self.executor_memory}"
        )

        return self._spark

    @property
    def spark(self) -> SparkSession:
        """Get Spark session (creates if needed)"""
        return self.get_or_create_session()

    def stop(self):
        """Stop Spark session"""
        if self._spark is not None:
            logger.info("Stopping Spark session")
            self._spark.stop()
            self._spark = None

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about current Spark session"""
        if self._spark is None:
            return {"active": False}

        return {
            "active": True,
            "app_name": self.app_name,
            "master": self.master,
            "spark_version": self._spark.version,
            "executor_memory": self.executor_memory,
            "driver_memory": self.driver_memory,
            "executor_cores": self.executor_cores
        }

    def __enter__(self):
        """Context manager entry"""
        return self.get_or_create_session()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()


class DataFrameConverter:
    """
    Converts between pandas and Spark DataFrames.

    Handles data type mapping and optimization.
    """

    def __init__(self, spark_manager: SparkSessionManager):
        """
        Initialize converter.

        Args:
            spark_manager: SparkSessionManager instance
        """
        self.spark_manager = spark_manager

    def pandas_to_spark(
        self,
        df: pd.DataFrame,
        schema: Optional[StructType] = None,
        num_partitions: Optional[int] = None
    ) -> SparkDataFrame:
        """
        Convert pandas DataFrame to Spark DataFrame.

        Args:
            df: Pandas DataFrame
            schema: Optional Spark schema
            num_partitions: Number of partitions for distribution

        Returns:
            Spark DataFrame
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark not available")

        logger.debug(f"Converting pandas DataFrame ({len(df)} rows) to Spark")

        spark_df = self.spark_manager.spark.createDataFrame(df, schema=schema)

        if num_partitions:
            spark_df = spark_df.repartition(num_partitions)
            logger.debug(f"Repartitioned to {num_partitions} partitions")

        return spark_df

    def spark_to_pandas(
        self,
        df: SparkDataFrame,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Convert Spark DataFrame to pandas DataFrame.

        Args:
            df: Spark DataFrame
            limit: Max rows to convert (for large datasets)

        Returns:
            Pandas DataFrame
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark not available")

        logger.debug("Converting Spark DataFrame to pandas")

        if limit:
            df = df.limit(limit)

        pandas_df = df.toPandas()

        logger.debug(f"Converted to pandas DataFrame ({len(pandas_df)} rows)")

        return pandas_df

    def optimize_partitioning(
        self,
        df: SparkDataFrame,
        target_partition_size_mb: int = 128
    ) -> SparkDataFrame:
        """
        Optimize DataFrame partitioning based on size.

        Args:
            df: Spark DataFrame
            target_partition_size_mb: Target size per partition in MB

        Returns:
            Repartitioned Spark DataFrame
        """
        # Estimate DataFrame size
        num_rows = df.count()
        num_cols = len(df.columns)

        # Rough estimate: 8 bytes per value
        estimated_size_mb = (num_rows * num_cols * 8) / (1024 * 1024)

        # Calculate optimal partitions
        optimal_partitions = max(1, int(estimated_size_mb / target_partition_size_mb))

        logger.info(
            f"Optimizing partitions: {estimated_size_mb:.1f} MB → {optimal_partitions} partitions"
        )

        return df.repartition(optimal_partitions)


class DistributedDataValidator:
    """
    Distributes data validation across Spark cluster.

    Scales Agent 4's validation to large datasets.
    """

    def __init__(self, spark_manager: SparkSessionManager):
        """
        Initialize distributed validator.

        Args:
            spark_manager: SparkSessionManager instance
        """
        self.spark_manager = spark_manager

    def validate_nulls(
        self,
        df: SparkDataFrame,
        columns: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Check for null values across all partitions.

        Args:
            df: Spark DataFrame
            columns: Columns to check (all if None)

        Returns:
            Dict mapping column name to null count
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark not available")

        if columns is None:
            columns = df.columns

        logger.debug(f"Validating nulls across {len(columns)} columns")

        null_counts = {}
        for col in columns:
            count = df.filter(F.col(col).isNull()).count()
            null_counts[col] = count

        return null_counts

    def validate_ranges(
        self,
        df: SparkDataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate column values are within acceptable range.

        Args:
            df: Spark DataFrame
            column: Column to validate
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value

        Returns:
            Dict with validation results
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark not available")

        logger.debug(f"Validating range for column: {column}")

        # Get actual min/max
        stats = df.select(
            F.min(column).alias("actual_min"),
            F.max(column).alias("actual_max"),
            F.count(column).alias("count")
        ).collect()[0]

        actual_min = stats["actual_min"]
        actual_max = stats["actual_max"]
        count = stats["count"]

        # Check violations
        violations = 0
        if min_value is not None:
            violations += df.filter(F.col(column) < min_value).count()
        if max_value is not None:
            violations += df.filter(F.col(column) > max_value).count()

        return {
            "column": column,
            "actual_min": actual_min,
            "actual_max": actual_max,
            "expected_min": min_value,
            "expected_max": max_value,
            "total_rows": count,
            "violations": violations,
            "valid": violations == 0
        }

    def validate_uniqueness(
        self,
        df: SparkDataFrame,
        column: str
    ) -> Dict[str, Any]:
        """
        Check for duplicate values in a column.

        Args:
            df: Spark DataFrame
            column: Column to check

        Returns:
            Dict with uniqueness validation results
        """
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark not available")

        logger.debug(f"Validating uniqueness for column: {column}")

        total_count = df.count()
        distinct_count = df.select(column).distinct().count()
        duplicates = total_count - distinct_count

        return {
            "column": column,
            "total_rows": total_count,
            "distinct_values": distinct_count,
            "duplicates": duplicates,
            "is_unique": duplicates == 0,
            "uniqueness_ratio": distinct_count / total_count if total_count > 0 else 0.0
        }

    def run_full_validation(
        self,
        df: SparkDataFrame,
        validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run comprehensive validation suite.

        Args:
            df: Spark DataFrame
            validation_rules: Dict specifying validation rules per column

        Returns:
            Comprehensive validation report
        """
        logger.info("Running full distributed validation")

        results = {
            "total_rows": df.count(),
            "total_columns": len(df.columns),
            "validations": {},
            "overall_valid": True
        }

        # Null checks
        if "required_columns" in validation_rules:
            null_counts = self.validate_nulls(df, validation_rules["required_columns"])
            results["validations"]["nulls"] = null_counts
            if any(count > 0 for count in null_counts.values()):
                results["overall_valid"] = False

        # Range checks
        if "ranges" in validation_rules:
            range_results = []
            for col, ranges in validation_rules["ranges"].items():
                result = self.validate_ranges(
                    df, col,
                    min_value=ranges.get("min"),
                    max_value=ranges.get("max")
                )
                range_results.append(result)
                if not result["valid"]:
                    results["overall_valid"] = False

            results["validations"]["ranges"] = range_results

        # Uniqueness checks
        if "unique_columns" in validation_rules:
            uniqueness_results = []
            for col in validation_rules["unique_columns"]:
                result = self.validate_uniqueness(df, col)
                uniqueness_results.append(result)
                if not result["is_unique"]:
                    results["overall_valid"] = False

            results["validations"]["uniqueness"] = uniqueness_results

        logger.info(f"Validation complete: {'PASSED' if results['overall_valid'] else 'FAILED'}")

        return results
