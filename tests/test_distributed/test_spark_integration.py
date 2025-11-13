"""
Tests for Spark Integration

Tests PySpark session management and distributed data operations.
"""

import pytest
import pandas as pd
import numpy as np

# Check if PySpark is available
try:
    import pyspark

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

# Import with graceful fallback
if PYSPARK_AVAILABLE:
    from mcp_server.distributed.spark_integration import (
        SparkSessionManager,
        DataFrameConverter,
        DistributedDataValidator,
    )

pytest_mark_skipif = pytest.mark.skipif(
    not PYSPARK_AVAILABLE, reason="PySpark not installed"
)


@pytest_mark_skipif
class TestSparkSessionManager:
    """Test suite for SparkSessionManager"""

    def test_session_creation(self):
        """Test creating a Spark session"""
        manager = SparkSessionManager(app_name="test_app", master="local[2]")

        spark = manager.get_or_create_session()

        assert spark is not None
        assert manager._spark is not None

        manager.stop()

    def test_session_reuse(self):
        """Test that session is reused"""
        manager = SparkSessionManager()

        spark1 = manager.get_or_create_session()
        spark2 = manager.get_or_create_session()

        assert spark1 is spark2

        manager.stop()

    def test_context_manager(self):
        """Test using manager as context manager"""
        with SparkSessionManager() as spark:
            assert spark is not None

        # Session should be stopped after context

    def test_get_session_info(self):
        """Test getting session information"""
        manager = SparkSessionManager(app_name="info_test", executor_memory="1g")

        # Before creation
        info = manager.get_session_info()
        assert info["active"] is False

        # After creation
        manager.get_or_create_session()
        info = manager.get_session_info()

        assert info["active"] is True
        assert info["app_name"] == "info_test"
        assert info["executor_memory"] == "1g"

        manager.stop()

    def test_custom_config(self):
        """Test adding custom Spark configuration"""
        custom_config = {
            "spark.sql.shuffle.partitions": "10",
            "spark.default.parallelism": "4",
        }

        manager = SparkSessionManager(config=custom_config)
        spark = manager.get_or_create_session()

        assert spark.conf.get("spark.sql.shuffle.partitions") == "10"

        manager.stop()


@pytest_mark_skipif
class TestDataFrameConverter:
    """Test suite for DataFrameConverter"""

    @pytest.fixture
    def spark_manager(self):
        """Create Spark session manager"""
        manager = SparkSessionManager()
        yield manager
        manager.stop()

    @pytest.fixture
    def converter(self, spark_manager):
        """Create converter instance"""
        return DataFrameConverter(spark_manager)

    @pytest.fixture
    def sample_pandas_df(self):
        """Create sample pandas DataFrame"""
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Player1", "Player2", "Player3", "Player4", "Player5"],
                "score": [25.5, 30.2, 15.8, 22.1, 28.9],
            }
        )

    def test_pandas_to_spark_conversion(self, converter, sample_pandas_df):
        """Test converting pandas to Spark DataFrame"""
        spark_df = converter.pandas_to_spark(sample_pandas_df)

        assert spark_df is not None
        assert spark_df.count() == 5
        assert len(spark_df.columns) == 3

    def test_spark_to_pandas_conversion(self, converter, sample_pandas_df):
        """Test converting Spark to pandas DataFrame"""
        # Convert to Spark and back
        spark_df = converter.pandas_to_spark(sample_pandas_df)
        result_df = converter.spark_to_pandas(spark_df)

        assert len(result_df) == 5
        pd.testing.assert_frame_equal(result_df, sample_pandas_df)

    def test_conversion_with_limit(self, converter):
        """Test converting large Spark DF with limit"""
        # Create large pandas DF
        large_df = pd.DataFrame({"id": range(1000), "value": np.random.randn(1000)})

        spark_df = converter.pandas_to_spark(large_df)
        limited_df = converter.spark_to_pandas(spark_df, limit=100)

        assert len(limited_df) == 100

    def test_repartitioning(self, converter, sample_pandas_df):
        """Test DataFrame repartitioning"""
        spark_df = converter.pandas_to_spark(sample_pandas_df, num_partitions=4)

        assert spark_df.rdd.getNumPartitions() == 4

    def test_optimize_partitioning(self, converter):
        """Test partition optimization"""
        # Create moderately sized DF
        df = pd.DataFrame({"id": range(10000), "value": np.random.randn(10000)})

        spark_df = converter.pandas_to_spark(df)
        optimized_df = converter.optimize_partitioning(spark_df)

        assert optimized_df.rdd.getNumPartitions() > 0


@pytest_mark_skipif
class TestDistributedDataValidator:
    """Test suite for DistributedDataValidator"""

    @pytest.fixture
    def spark_manager(self):
        """Create Spark session manager"""
        manager = SparkSessionManager()
        yield manager
        manager.stop()

    @pytest.fixture
    def validator(self, spark_manager):
        """Create validator instance"""
        return DistributedDataValidator(spark_manager)

    @pytest.fixture
    def sample_spark_df(self, spark_manager):
        """Create sample Spark DataFrame"""
        data = pd.DataFrame(
            {
                "player_id": [1, 2, 3, None, 5],  # Has null
                "name": ["A", "B", "C", "D", "E"],
                "score": [10, 25, 15, 30, 20],  # All valid
                "invalid_score": [5, 150, 10, 200, 15],  # Some out of range
            }
        )

        converter = DataFrameConverter(spark_manager)
        return converter.pandas_to_spark(data)

    def test_validate_nulls(self, validator, sample_spark_df):
        """Test null validation"""
        null_counts = validator.validate_nulls(sample_spark_df)

        assert null_counts["player_id"] == 1
        assert null_counts["name"] == 0
        assert null_counts["score"] == 0

    def test_validate_nulls_specific_columns(self, validator, sample_spark_df):
        """Test null validation for specific columns"""
        null_counts = validator.validate_nulls(
            sample_spark_df, columns=["player_id", "name"]
        )

        assert len(null_counts) == 2
        assert "score" not in null_counts

    def test_validate_ranges(self, validator, sample_spark_df):
        """Test range validation"""
        result = validator.validate_ranges(
            sample_spark_df, column="score", min_value=0, max_value=100
        )

        assert result["column"] == "score"
        assert result["violations"] == 0
        assert result["valid"] is True
        assert result["actual_min"] == 10
        assert result["actual_max"] == 30

    def test_validate_ranges_with_violations(self, validator, sample_spark_df):
        """Test range validation with violations"""
        result = validator.validate_ranges(
            sample_spark_df, column="invalid_score", min_value=0, max_value=100
        )

        assert result["violations"] == 2  # Two values > 100
        assert result["valid"] is False

    def test_validate_uniqueness(self, validator, spark_manager):
        """Test uniqueness validation"""
        # Create DF with duplicates
        data = pd.DataFrame({"id": [1, 2, 2, 3, 3, 3]})  # Has duplicates

        converter = DataFrameConverter(spark_manager)
        df = converter.pandas_to_spark(data)

        result = validator.validate_uniqueness(df, "id")

        assert result["total_rows"] == 6
        assert result["distinct_values"] == 3
        assert result["duplicates"] == 3
        assert result["is_unique"] is False

    def test_validate_uniqueness_unique_column(self, validator, spark_manager):
        """Test uniqueness validation on unique column"""
        data = pd.DataFrame({"id": [1, 2, 3, 4, 5]})  # All unique

        converter = DataFrameConverter(spark_manager)
        df = converter.pandas_to_spark(data)

        result = validator.validate_uniqueness(df, "id")

        assert result["is_unique"] is True
        assert result["uniqueness_ratio"] == 1.0

    def test_run_full_validation(self, validator, sample_spark_df):
        """Test comprehensive validation"""
        validation_rules = {
            "required_columns": ["player_id", "name"],
            "ranges": {"score": {"min": 0, "max": 100}},
            "unique_columns": ["name"],
        }

        result = validator.run_full_validation(sample_spark_df, validation_rules)

        assert result["total_rows"] == 5
        assert result["total_columns"] == 4
        assert "validations" in result
        assert "overall_valid" in result

        # Check null validation
        assert "nulls" in result["validations"]
        assert result["validations"]["nulls"]["player_id"] == 1

        # Check range validation
        assert "ranges" in result["validations"]

        # Check uniqueness
        assert "uniqueness" in result["validations"]

    def test_full_validation_failure(self, validator, sample_spark_df):
        """Test that full validation detects failures"""
        validation_rules = {
            "required_columns": ["player_id"],  # Has nulls
        }

        result = validator.run_full_validation(sample_spark_df, validation_rules)

        # Should fail due to nulls in player_id
        assert result["overall_valid"] is False
