"""
Data Cleaning Module
Automated data cleaning and preprocessing for NBA MCP system.

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive cleaning utilities: outlier detection, missing value handling, normalization.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Literal, Tuple
from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import IsolationForest

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext
    from mcp_server.monitoring import get_health_monitor

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutlierMethod(Enum):
    """Outlier detection methods"""

    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"


class ImputationStrategy(Enum):
    """Missing value imputation strategies"""

    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "ffill"
    BACKWARD_FILL = "bfill"
    INTERPOLATE = "interpolate"
    DROP = "drop"


class ScalingMethod(Enum):
    """Data scaling methods"""

    MINMAX = "minmax"
    STANDARD = "standard"
    ROBUST = "robust"


@dataclass
class CleaningReport:
    """Report of cleaning operations"""

    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    outliers_removed: int = 0
    missing_values_imputed: int = 0
    duplicates_removed: int = 0
    types_converted: int = 0
    scaled_columns: List[str] = dc_field(default_factory=list)
    operations: List[str] = dc_field(default_factory=list)

    @property
    def rows_removed(self) -> int:
        """Calculate rows removed"""
        return self.rows_before - self.rows_after

    @property
    def columns_removed(self) -> int:
        """Calculate columns removed"""
        return self.columns_before - self.columns_after

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rows_before": self.rows_before,
            "rows_after": self.rows_after,
            "columns_before": self.columns_before,
            "columns_after": self.columns_after,
            "rows_removed": self.rows_removed,
            "columns_removed": self.columns_removed,
            "outliers_removed": self.outliers_removed,
            "missing_values_imputed": self.missing_values_imputed,
            "duplicates_removed": self.duplicates_removed,
            "types_converted": self.types_converted,
            "scaled_columns": self.scaled_columns,
            "operations": self.operations,
        }


class DataCleaner:
    """
    Automated data cleaning and preprocessing.

    Provides comprehensive cleaning utilities:
    - Outlier detection and removal
    - Missing value imputation
    - Data normalization and scaling
    - Duplicate detection and removal
    - Data type conversion
    """

    def __init__(self):
        """Initialize data cleaner"""
        self.cleaning_history: List[CleaningReport] = []
        logger.info("DataCleaner initialized")

    @handle_errors(reraise=True, notify=False)
    def detect_outliers_iqr(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None, threshold: float = 1.5
    ) -> pd.Series:
        """
        Detect outliers using IQR (Interquartile Range) method.

        Args:
            df: DataFrame to check
            columns: Columns to check (None = all numeric columns)
            threshold: IQR multiplier (default: 1.5)

        Returns:
            Boolean series indicating outlier rows
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outlier_mask = pd.Series([False] * len(df), index=df.index)

        for col in columns:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in DataFrame")
                continue

            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_mask = outlier_mask | col_outliers

        return outlier_mask

    @handle_errors(reraise=True, notify=False)
    def detect_outliers_zscore(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None, threshold: float = 3.0
    ) -> pd.Series:
        """
        Detect outliers using Z-score method.

        Args:
            df: DataFrame to check
            columns: Columns to check (None = all numeric columns)
            threshold: Z-score threshold (default: 3.0)

        Returns:
            Boolean series indicating outlier rows
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outlier_mask = pd.Series([False] * len(df), index=df.index)

        for col in columns:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in DataFrame")
                continue

            # Calculate z-scores
            z_scores = np.abs(stats.zscore(df[col], nan_policy='omit'))
            col_outliers = z_scores > threshold
            outlier_mask = outlier_mask | col_outliers

        return outlier_mask

    @handle_errors(reraise=True, notify=False)
    def detect_outliers_isolation_forest(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        contamination: float = 0.1,
    ) -> pd.Series:
        """
        Detect outliers using Isolation Forest (ML-based).

        Args:
            df: DataFrame to check
            columns: Columns to check (None = all numeric columns)
            contamination: Expected proportion of outliers (default: 0.1)

        Returns:
            Boolean series indicating outlier rows
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # Prepare data
        X = df[columns].fillna(df[columns].median())

        # Fit Isolation Forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        predictions = iso_forest.fit_predict(X)

        # -1 indicates outlier, 1 indicates inlier
        outlier_mask = pd.Series(predictions == -1, index=df.index)

        return outlier_mask

    @handle_errors(reraise=True, notify=False)
    def remove_outliers(
        self,
        df: pd.DataFrame,
        method: OutlierMethod = OutlierMethod.IQR,
        columns: Optional[List[str]] = None,
        **kwargs,
    ) -> Tuple[pd.DataFrame, int]:
        """
        Remove outliers from DataFrame.

        Args:
            df: DataFrame to clean
            method: Outlier detection method
            columns: Columns to check (None = all numeric)
            **kwargs: Additional arguments for detection method

        Returns:
            Tuple of (cleaned DataFrame, number of outliers removed)
        """
        if method == OutlierMethod.IQR:
            outlier_mask = self.detect_outliers_iqr(df, columns, **kwargs)
        elif method == OutlierMethod.ZSCORE:
            outlier_mask = self.detect_outliers_zscore(df, columns, **kwargs)
        elif method == OutlierMethod.ISOLATION_FOREST:
            outlier_mask = self.detect_outliers_isolation_forest(df, columns, **kwargs)
        else:
            raise ValueError(f"Unknown outlier method: {method}")

        outliers_count = outlier_mask.sum()
        cleaned_df = df[~outlier_mask].copy()

        logger.info(f"Removed {outliers_count} outliers using {method.value} method")
        return cleaned_df, outliers_count

    @handle_errors(reraise=True, notify=False)
    def impute_missing_values(
        self,
        df: pd.DataFrame,
        strategy: ImputationStrategy = ImputationStrategy.MEAN,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, int]:
        """
        Impute missing values in DataFrame.

        Args:
            df: DataFrame to clean
            strategy: Imputation strategy
            columns: Columns to impute (None = all columns with missing values)

        Returns:
            Tuple of (imputed DataFrame, number of values imputed)
        """
        df_cleaned = df.copy()
        initial_missing = df_cleaned.isnull().sum().sum()

        if columns is None:
            columns = df_cleaned.columns[df_cleaned.isnull().any()].tolist()

        for col in columns:
            if col not in df_cleaned.columns:
                logger.warning(f"Column '{col}' not found in DataFrame")
                continue

            if not df_cleaned[col].isnull().any():
                continue

            if strategy == ImputationStrategy.MEAN:
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    df_cleaned[col].fillna(df_cleaned[col].mean(), inplace=True)
            elif strategy == ImputationStrategy.MEDIAN:
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    df_cleaned[col].fillna(df_cleaned[col].median(), inplace=True)
            elif strategy == ImputationStrategy.MODE:
                mode_value = df_cleaned[col].mode()
                if len(mode_value) > 0:
                    df_cleaned[col].fillna(mode_value[0], inplace=True)
            elif strategy == ImputationStrategy.FORWARD_FILL:
                df_cleaned[col].fillna(method='ffill', inplace=True)
            elif strategy == ImputationStrategy.BACKWARD_FILL:
                df_cleaned[col].fillna(method='bfill', inplace=True)
            elif strategy == ImputationStrategy.INTERPOLATE:
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    df_cleaned[col].interpolate(inplace=True)
            elif strategy == ImputationStrategy.DROP:
                # Will be handled separately
                pass

        if strategy == ImputationStrategy.DROP:
            df_cleaned.dropna(subset=columns, inplace=True)

        final_missing = df_cleaned.isnull().sum().sum()
        imputed_count = initial_missing - final_missing

        logger.info(f"Imputed {imputed_count} missing values using {strategy.value} strategy")
        return df_cleaned, imputed_count

    @handle_errors(reraise=True, notify=False)
    def remove_duplicates(
        self,
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: Literal["first", "last", False] = "first",
    ) -> Tuple[pd.DataFrame, int]:
        """
        Remove duplicate rows from DataFrame.

        Args:
            df: DataFrame to clean
            subset: Columns to consider for duplicates (None = all columns)
            keep: Which duplicates to keep ('first', 'last', or False to remove all)

        Returns:
            Tuple of (cleaned DataFrame, number of duplicates removed)
        """
        initial_rows = len(df)
        df_cleaned = df.drop_duplicates(subset=subset, keep=keep).copy()
        duplicates_count = initial_rows - len(df_cleaned)

        logger.info(f"Removed {duplicates_count} duplicate rows")
        return df_cleaned, duplicates_count

    @handle_errors(reraise=True, notify=False)
    def scale_features(
        self,
        df: pd.DataFrame,
        method: ScalingMethod = ScalingMethod.STANDARD,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Scale/normalize numeric features.

        Args:
            df: DataFrame to scale
            method: Scaling method
            columns: Columns to scale (None = all numeric columns)

        Returns:
            Scaled DataFrame
        """
        df_scaled = df.copy()

        if columns is None:
            columns = df_scaled.select_dtypes(include=[np.number]).columns.tolist()

        if not columns:
            logger.warning("No numeric columns found for scaling")
            return df_scaled

        if method == ScalingMethod.MINMAX:
            scaler = MinMaxScaler()
        elif method == ScalingMethod.STANDARD:
            scaler = StandardScaler()
        elif method == ScalingMethod.ROBUST:
            scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {method}")

        df_scaled[columns] = scaler.fit_transform(df_scaled[columns])

        logger.info(f"Scaled {len(columns)} columns using {method.value} method")
        return df_scaled

    @handle_errors(reraise=True, notify=False)
    def convert_types(
        self, df: pd.DataFrame, type_map: Dict[str, str]
    ) -> Tuple[pd.DataFrame, int]:
        """
        Convert column data types.

        Args:
            df: DataFrame to convert
            type_map: Dictionary mapping column names to target types

        Returns:
            Tuple of (converted DataFrame, number of conversions)
        """
        df_converted = df.copy()
        conversions = 0

        for col, target_type in type_map.items():
            if col not in df_converted.columns:
                logger.warning(f"Column '{col}' not found in DataFrame")
                continue

            try:
                if target_type == "int":
                    df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').astype('Int64')
                elif target_type == "float":
                    df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
                elif target_type == "str":
                    df_converted[col] = df_converted[col].astype(str)
                elif target_type == "datetime":
                    df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
                elif target_type == "bool":
                    df_converted[col] = df_converted[col].astype(bool)
                else:
                    logger.warning(f"Unknown type '{target_type}' for column '{col}'")
                    continue

                conversions += 1
                logger.info(f"Converted column '{col}' to {target_type}")
            except Exception as e:
                logger.error(f"Failed to convert column '{col}' to {target_type}: {e}")

        return df_converted, conversions

    @handle_errors(reraise=True, notify=False)
    def clean(
        self,
        df: pd.DataFrame,
        remove_outliers: bool = True,
        outlier_method: OutlierMethod = OutlierMethod.IQR,
        impute_missing: bool = True,
        imputation_strategy: ImputationStrategy = ImputationStrategy.MEDIAN,
        remove_dupes: bool = True,
        scale_features: bool = False,
        scaling_method: ScalingMethod = ScalingMethod.STANDARD,
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Perform comprehensive data cleaning.

        Args:
            df: DataFrame to clean
            remove_outliers: Whether to remove outliers
            outlier_method: Outlier detection method
            impute_missing: Whether to impute missing values
            imputation_strategy: Imputation strategy
            remove_dupes: Whether to remove duplicates
            scale_features: Whether to scale features
            scaling_method: Scaling method

        Returns:
            Tuple of (cleaned DataFrame, cleaning report)
        """
        report = CleaningReport(
            rows_before=len(df),
            columns_before=len(df.columns),
            rows_after=len(df),
            columns_after=len(df.columns),
        )

        df_cleaned = df.copy()

        # Remove duplicates
        if remove_dupes:
            df_cleaned, dupes_removed = self.remove_duplicates(df_cleaned)
            report.duplicates_removed = dupes_removed
            report.rows_after = len(df_cleaned)
            report.operations.append(f"Removed {dupes_removed} duplicates")

        # Impute missing values
        if impute_missing:
            df_cleaned, imputed = self.impute_missing_values(df_cleaned, imputation_strategy)
            report.missing_values_imputed = imputed
            report.operations.append(f"Imputed {imputed} missing values ({imputation_strategy.value})")

        # Remove outliers
        if remove_outliers:
            df_cleaned, outliers = self.remove_outliers(df_cleaned, outlier_method)
            report.outliers_removed = outliers
            report.rows_after = len(df_cleaned)
            report.operations.append(f"Removed {outliers} outliers ({outlier_method.value})")

        # Scale features
        if scale_features:
            numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()
            df_cleaned = self.scale_features(df_cleaned, scaling_method)
            report.scaled_columns = numeric_cols
            report.operations.append(f"Scaled {len(numeric_cols)} columns ({scaling_method.value})")

        report.columns_after = len(df_cleaned.columns)

        # Track metrics if Week 1 available
        if WEEK1_AVAILABLE:
            self._track_metrics(report)

        # Save to history
        self.cleaning_history.append(report)

        return df_cleaned, report

    def _track_metrics(self, report: CleaningReport) -> None:
        """Track cleaning metrics with Week 1 monitoring"""
        try:
            monitor = get_health_monitor()

            monitor.track_metric("data_cleaning.rows_removed", report.rows_removed)
            monitor.track_metric("data_cleaning.outliers_removed", report.outliers_removed)
            monitor.track_metric(
                "data_cleaning.missing_values_imputed", report.missing_values_imputed
            )
            monitor.track_metric("data_cleaning.duplicates_removed", report.duplicates_removed)

        except Exception as e:
            logger.error(f"Failed to track metrics: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cleaning statistics"""
        if not self.cleaning_history:
            return {
                "total_cleanings": 0,
                "total_rows_removed": 0,
                "total_outliers_removed": 0,
                "total_missing_imputed": 0,
                "total_duplicates_removed": 0,
            }

        return {
            "total_cleanings": len(self.cleaning_history),
            "total_rows_removed": sum(r.rows_removed for r in self.cleaning_history),
            "total_outliers_removed": sum(r.outliers_removed for r in self.cleaning_history),
            "total_missing_imputed": sum(
                r.missing_values_imputed for r in self.cleaning_history
            ),
            "total_duplicates_removed": sum(
                r.duplicates_removed for r in self.cleaning_history
            ),
        }
