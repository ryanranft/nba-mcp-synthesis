"""
Null/Missing Data Handling Module
Comprehensive strategies for handling null and missing data in ML pipelines.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
import numpy as np
import pandas as pd
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImputationStrategy(Enum):
    """Data imputation strategies"""
    DROP = "drop"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "ffill"
    BACKWARD_FILL = "bfill"
    CONSTANT = "constant"
    INTERPOLATE = "interpolate"
    KNN = "knn"


class NullDataHandler:
    """Handles null and missing data with multiple strategies"""
    
    def __init__(self):
        self.imputation_stats: Dict[str, Any] = {}
    
    def analyze_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing data patterns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict with missing data analysis
        """
        total_cells = df.size
        total_missing = df.isnull().sum().sum()
        missing_ratio = total_missing / total_cells if total_cells > 0 else 0
        
        column_missing = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                column_missing[col] = {
                    "count": int(missing_count),
                    "percentage": (missing_count / len(df)) * 100
                }
        
        analysis = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": total_cells,
            "total_missing": int(total_missing),
            "missing_percentage": missing_ratio * 100,
            "columns_with_missing": column_missing,
            "completely_null_columns": [col for col in df.columns if df[col].isnull().all()]
        }
        
        logger.info(
            f"Missing data analysis: {analysis['total_missing']} cells "
            f"({analysis['missing_percentage']:.2f}%) missing"
        )
        
        return analysis
    
    def impute_column(
        self,
        df: pd.DataFrame,
        column: str,
        strategy: ImputationStrategy,
        fill_value: Optional[Any] = None,
        k_neighbors: int = 5
    ) -> pd.DataFrame:
        """
        Impute missing values in a specific column.
        
        Args:
            df: DataFrame
            column: Column name
            strategy: Imputation strategy
            fill_value: Value for CONSTANT strategy
            k_neighbors: Number of neighbors for KNN strategy
            
        Returns:
            DataFrame with imputed values
        """
        if column not in df.columns:
            logger.error(f"Column '{column}' not found")
            return df
        
        missing_count = df[column].isnull().sum()
        if missing_count == 0:
            logger.info(f"Column '{column}' has no missing values")
            return df
        
        df_copy = df.copy()
        
        if strategy == ImputationStrategy.DROP:
            df_copy = df_copy.dropna(subset=[column])
            logger.info(f"Dropped {missing_count} rows with missing values in '{column}'")
        
        elif strategy == ImputationStrategy.MEAN:
            mean_value = df[column].mean()
            df_copy[column].fillna(mean_value, inplace=True)
            self.imputation_stats[column] = {"strategy": "mean", "value": mean_value}
            logger.info(f"Imputed '{column}' with mean: {mean_value:.2f}")
        
        elif strategy == ImputationStrategy.MEDIAN:
            median_value = df[column].median()
            df_copy[column].fillna(median_value, inplace=True)
            self.imputation_stats[column] = {"strategy": "median", "value": median_value}
            logger.info(f"Imputed '{column}' with median: {median_value:.2f}")
        
        elif strategy == ImputationStrategy.MODE:
            mode_value = df[column].mode()[0] if not df[column].mode().empty else None
            if mode_value is not None:
                df_copy[column].fillna(mode_value, inplace=True)
                self.imputation_stats[column] = {"strategy": "mode", "value": mode_value}
                logger.info(f"Imputed '{column}' with mode: {mode_value}")
        
        elif strategy == ImputationStrategy.FORWARD_FILL:
            df_copy[column].fillna(method='ffill', inplace=True)
            logger.info(f"Forward filled '{column}'")
        
        elif strategy == ImputationStrategy.BACKWARD_FILL:
            df_copy[column].fillna(method='bfill', inplace=True)
            logger.info(f"Backward filled '{column}'")
        
        elif strategy == ImputationStrategy.CONSTANT:
            if fill_value is None:
                logger.error("CONSTANT strategy requires fill_value")
                return df
            df_copy[column].fillna(fill_value, inplace=True)
            self.imputation_stats[column] = {"strategy": "constant", "value": fill_value}
            logger.info(f"Imputed '{column}' with constant: {fill_value}")
        
        elif strategy == ImputationStrategy.INTERPOLATE:
            df_copy[column] = df_copy[column].interpolate()
            logger.info(f"Interpolated '{column}'")
        
        elif strategy == ImputationStrategy.KNN:
            logger.warning("KNN imputation requires scikit-learn, using mean as fallback")
            mean_value = df[column].mean()
            df_copy[column].fillna(mean_value, inplace=True)
        
        return df_copy
    
    def auto_impute(self, df: pd.DataFrame, numeric_strategy: ImputationStrategy = ImputationStrategy.MEDIAN, categorical_strategy: ImputationStrategy = ImputationStrategy.MODE) -> pd.DataFrame:
        """
        Automatically impute all columns based on data type.
        
        Args:
            df: DataFrame
            numeric_strategy: Strategy for numeric columns
            categorical_strategy: Strategy for categorical columns
            
        Returns:
            DataFrame with imputed values
        """
        df_copy = df.copy()
        
        for col in df.columns:
            if df[col].isnull().sum() == 0:
                continue
            
            if pd.api.types.is_numeric_dtype(df[col]):
                df_copy = self.impute_column(df_copy, col, numeric_strategy)
            else:
                df_copy = self.impute_column(df_copy, col, categorical_strategy)
        
        logger.info("Auto-imputation complete")
        return df_copy
    
    def validate_no_nulls(self, df: pd.DataFrame, strict: bool = True) -> bool:
        """
        Validate that DataFrame has no null values.
        
        Args:
            df: DataFrame to validate
            strict: If True, raise error on nulls. If False, log warning.
            
        Returns:
            True if no nulls found
        """
        null_count = df.isnull().sum().sum()
        
        if null_count > 0:
            columns_with_nulls = df.columns[df.isnull().any()].tolist()
            message = f"Found {null_count} null values in columns: {columns_with_nulls}"
            
            if strict:
                logger.error(message)
                raise ValueError(message)
            else:
                logger.warning(message)
                return False
        
        logger.info("✓ No null values found")
        return True


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("NULL/MISSING DATA HANDLING DEMO")
    print("=" * 80)
    
    # Create sample data with missing values
    df = pd.DataFrame({
        "player_id": [1, 2, 3, 4, 5],
        "points": [25.0, None, 18.0, 22.0, None],
        "rebounds": [8.0, 6.0, None, 7.0, 9.0],
        "assists": [5.0, 7.0, 4.0, None, 6.0],
        "team": ["Lakers", None, "Warriors", "Celtics", "Heat"],
        "position": ["PG", "SG", None, "SF", "PF"]
    })
    
    print("\nOriginal DataFrame:")
    print(df)
    
    handler = NullDataHandler()
    
    # Analyze missing data
    print("\n" + "=" * 80)
    print("MISSING DATA ANALYSIS")
    print("=" * 80)
    
    analysis = handler.analyze_missing_data(df)
    print(f"\nTotal Missing: {analysis['total_missing']} ({analysis['missing_percentage']:.2f}%)")
    print("\nColumns with Missing Data:")
    for col, info in analysis['columns_with_missing'].items():
        print(f"  - {col}: {info['count']} ({info['percentage']:.1f}%)")
    
    # Impute specific columns
    print("\n" + "=" * 80)
    print("COLUMN-SPECIFIC IMPUTATION")
    print("=" * 80)
    
    df_imputed = handler.impute_column(df.copy(), "points", ImputationStrategy.MEAN)
    df_imputed = handler.impute_column(df_imputed, "rebounds", ImputationStrategy.MEDIAN)
    df_imputed = handler.impute_column(df_imputed, "assists", ImputationStrategy.FORWARD_FILL)
    df_imputed = handler.impute_column(df_imputed, "team", ImputationStrategy.MODE)
    df_imputed = handler.impute_column(df_imputed, "position", ImputationStrategy.CONSTANT, fill_value="Unknown")
    
    print("\nImputed DataFrame:")
    print(df_imputed)
    
    # Auto-impute
    print("\n" + "=" * 80)
    print("AUTO-IMPUTATION")
    print("=" * 80)
    
    df_auto = handler.auto_impute(df.copy())
    print("\nAuto-Imputed DataFrame:")
    print(df_auto)
    
    # Validate
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)
    
    try:
        handler.validate_no_nulls(df_auto, strict=True)
    except ValueError as e:
        print(f"Validation failed: {e}")
    
    print("\n" + "=" * 80)
    print("Null Handling Demo Complete!")
    print("=" * 80)

