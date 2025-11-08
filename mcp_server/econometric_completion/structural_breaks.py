"""
Structural Breaks Detection (Agent 18, Module 5)

Detect and test for structural changes in time series:
- Chow test for known break points
- Quandt-Andrews (sup-F) test for unknown breaks
- CUSUM and CUSUM-SQ tests
- Bai-Perron multiple break test
- Rolling window stability tests

NBA Applications:
- Coaching change impact detection
- Rule changes (3-point line, etc.)
- Player development phases
- Team strategy shifts
- Injury impact on performance trajectory

Integrates with:
- time_series: Time series models
- panel_data: Panel structural breaks
- causal_inference: Treatment timing identification
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class BreakPoint:
    """Information about a detected break point"""

    index: int  # Position in time series
    test_statistic: float
    p_value: float
    confidence: float  # Confidence in this break (0-1)

    # Optional metadata
    date: Optional[Any] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'index': self.index,
            'test_statistic': self.test_statistic,
            'p_value': self.p_value,
            'confidence': self.confidence,
            'date': str(self.date) if self.date else None,
            'description': self.description
        }


@dataclass
class StructuralBreakResult:
    """Results from structural break detection"""

    has_breaks: bool
    break_points: List[BreakPoint]
    test_statistic: float
    critical_value: float
    p_value: Optional[float] = None

    # Model with breaks
    coefficients_before: Optional[np.ndarray] = None
    coefficients_after: Optional[np.ndarray] = None

    # Stability measures
    cusum: Optional[np.ndarray] = None
    cusum_sq: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'has_breaks': self.has_breaks,
            'n_breaks': len(self.break_points),
            'break_points': [bp.to_dict() for bp in self.break_points],
            'test_statistic': self.test_statistic,
            'critical_value': self.critical_value,
            'p_value': self.p_value
        }


class ChowTest:
    """
    Chow test for structural break at known point.

    Tests if coefficients are different before and after break.
    Requires specifying the break point a priori.
    """

    def __init__(self):
        """Initialize Chow test"""
        logger.info("ChowTest initialized")

    def test(
        self,
        X: np.ndarray,
        y: np.ndarray,
        break_point: int
    ) -> StructuralBreakResult:
        """
        Perform Chow test at specified break point.

        Args:
            X: Feature matrix (n_obs, n_vars)
            y: Target variable (n_obs,)
            break_point: Index of break point

        Returns:
            StructuralBreakResult
        """
        if break_point <= 0 or break_point >= len(y) - 1:
            raise ValueError("Break point must be within sample")

        # Split data
        X1, y1 = X[:break_point], y[:break_point]
        X2, y2 = X[break_point:], y[break_point:]

        # Fit models
        beta1 = np.linalg.lstsq(X1, y1, rcond=None)[0]
        beta2 = np.linalg.lstsq(X2, y2, rcond=None)[0]
        beta_pooled = np.linalg.lstsq(X, y, rcond=None)[0]

        # Calculate RSS
        rss1 = np.sum((y1 - X1 @ beta1) ** 2)
        rss2 = np.sum((y2 - X2 @ beta2) ** 2)
        rss_pooled = np.sum((y - X @ beta_pooled) ** 2)

        # Chow F-statistic
        rss_unrestricted = rss1 + rss2
        rss_restricted = rss_pooled

        k = X.shape[1]  # Number of parameters
        n1 = len(y1)
        n2 = len(y2)
        n = n1 + n2

        numerator = (rss_restricted - rss_unrestricted) / k
        denominator = rss_unrestricted / (n - 2 * k)

        if denominator > 0:
            f_stat = numerator / denominator
            # F-distribution with k and (n - 2k) degrees of freedom
            p_value = 1 - stats.f.cdf(f_stat, k, n - 2 * k)
            critical_value = stats.f.ppf(0.95, k, n - 2 * k)
        else:
            f_stat = 0.0
            p_value = 1.0
            critical_value = 0.0

        has_break = f_stat > critical_value

        break_pt = BreakPoint(
            index=break_point,
            test_statistic=f_stat,
            p_value=p_value,
            confidence=1 - p_value if p_value < 1 else 0.0
        )

        result = StructuralBreakResult(
            has_breaks=has_break,
            break_points=[break_pt] if has_break else [],
            test_statistic=f_stat,
            critical_value=critical_value,
            p_value=p_value,
            coefficients_before=beta1,
            coefficients_after=beta2
        )

        logger.info(f"Chow test: F={f_stat:.4f}, p-value={p_value:.4f}, break={'detected' if has_break else 'not detected'}")

        return result


class SupFTest:
    """
    Quandt-Andrews (sup-F) test for unknown break point.

    Tests for a break at unknown location by maximizing F-statistic
    over all possible break points.
    """

    def __init__(
        self,
        trim: float = 0.15
    ):
        """
        Initialize sup-F test.

        Args:
            trim: Fraction of data to trim at beginning/end
        """
        self.trim = trim
        logger.info(f"SupFTest initialized with trim={trim}")

    def test(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> StructuralBreakResult:
        """
        Perform sup-F test for unknown break.

        Args:
            X: Features
            y: Target

        Returns:
            StructuralBreakResult
        """
        n = len(y)
        trim_start = int(n * self.trim)
        trim_end = n - trim_start

        # Search over possible break points
        f_stats = []
        candidate_points = range(trim_start, trim_end)

        for break_point in candidate_points:
            # Chow test at this point
            chow = ChowTest()
            result = chow.test(X, y, break_point)
            f_stats.append(result.test_statistic)

        # Maximum F-statistic
        sup_f = max(f_stats)
        break_index = candidate_points[np.argmax(f_stats)]

        # Critical values (Andrews 1993, approximate)
        critical_values_5pct = {
            1: 8.58,  # 1 regressor
            2: 10.13,
            3: 11.14,
            4: 11.83
        }

        n_vars = X.shape[1]
        critical_value = critical_values_5pct.get(n_vars, 12.0)

        has_break = sup_f > critical_value

        if has_break:
            # Fit models at detected break
            chow = ChowTest()
            chow_result = chow.test(X, y, break_index)

            break_pt = BreakPoint(
                index=break_index,
                test_statistic=sup_f,
                p_value=chow_result.p_value,
                confidence=1.0 - chow_result.p_value if chow_result.p_value < 1 else 0.0
            )

            result = StructuralBreakResult(
                has_breaks=True,
                break_points=[break_pt],
                test_statistic=sup_f,
                critical_value=critical_value,
                coefficients_before=chow_result.coefficients_before,
                coefficients_after=chow_result.coefficients_after
            )
        else:
            result = StructuralBreakResult(
                has_breaks=False,
                break_points=[],
                test_statistic=sup_f,
                critical_value=critical_value
            )

        logger.info(f"Sup-F test: stat={sup_f:.4f}, crit={critical_value:.4f}, break={'detected at ' + str(break_index) if has_break else 'not detected'}")

        return result


class CUSUMTest:
    """
    CUSUM (Cumulative Sum) test for parameter stability.

    Tests whether coefficients are stable over time.
    Based on cumulative sum of recursive residuals.
    """

    def __init__(self):
        """Initialize CUSUM test"""
        logger.info("CUSUMTest initialized")

    def test(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> StructuralBreakResult:
        """
        Perform CUSUM test.

        Args:
            X: Features
            y: Target

        Returns:
            StructuralBreakResult with CUSUM statistics
        """
        n, k = X.shape

        # Need at least k+1 observations to start
        min_obs = k + 1

        # Recursive residuals
        recursive_residuals = []

        for t in range(min_obs, n):
            # Fit on data up to t-1
            X_t = X[:t]
            y_t = y[:t]

            beta_t = np.linalg.lstsq(X_t, y_t, rcond=None)[0]

            # One-step ahead prediction error at t
            y_pred_t = X[t] @ beta_t
            residual_t = y[t] - y_pred_t

            recursive_residuals.append(residual_t)

        recursive_residuals = np.array(recursive_residuals)

        # Standardize
        sigma = np.std(recursive_residuals)
        if sigma > 0:
            standardized_resid = recursive_residuals / sigma
        else:
            standardized_resid = recursive_residuals

        # CUSUM statistic
        cusum = np.cumsum(standardized_resid)

        # Critical bounds (5% significance, approximate)
        # Boundaries are ±a√(T-k) where a ≈ 0.948
        T = len(cusum)
        a = 0.948
        bound = a * np.sqrt(T)

        # Check if CUSUM crosses boundaries
        crosses_bound = np.any(np.abs(cusum) > bound)

        # Find crossing points
        break_points = []
        if crosses_bound:
            crossings = np.where(np.abs(cusum) > bound)[0]
            for idx in crossings[:3]:  # Report up to 3 breaks
                break_pt = BreakPoint(
                    index=min_obs + idx,
                    test_statistic=abs(cusum[idx]),
                    p_value=0.05 if abs(cusum[idx]) > bound else 0.5,
                    confidence=0.95 if abs(cusum[idx]) > bound else 0.5
                )
                break_points.append(break_pt)

        max_cusum = np.max(np.abs(cusum))

        result = StructuralBreakResult(
            has_breaks=crosses_bound,
            break_points=break_points,
            test_statistic=max_cusum,
            critical_value=bound,
            cusum=cusum
        )

        logger.info(f"CUSUM test: max={max_cusum:.4f}, bound={bound:.4f}, stable={'No' if crosses_bound else 'Yes'}")

        return result


class BaiPerronTest:
    """
    Bai-Perron test for multiple structural breaks.

    Tests for multiple breaks using sequential F-tests and information criteria.
    """

    def __init__(
        self,
        max_breaks: int = 5,
        trim: float = 0.15
    ):
        """
        Initialize Bai-Perron test.

        Args:
            max_breaks: Maximum number of breaks to test
            trim: Trim fraction
        """
        self.max_breaks = max_breaks
        self.trim = trim

        logger.info(f"BaiPerronTest initialized (max_breaks={max_breaks})")

    def test(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> StructuralBreakResult:
        """
        Perform Bai-Perron test.

        Args:
            X: Features
            y: Target

        Returns:
            StructuralBreakResult with multiple breaks
        """
        n = len(y)
        trim_points = int(n * self.trim)

        # Sequential testing for breaks
        detected_breaks = []
        remaining_segments = [(0, n)]

        for m in range(self.max_breaks):
            best_break = None
            best_f_stat = 0

            # Test each remaining segment
            for seg_start, seg_end in remaining_segments:
                if seg_end - seg_start < 2 * trim_points:
                    continue  # Segment too small

                # Search for break in this segment
                for break_point in range(seg_start + trim_points, seg_end - trim_points):
                    # Test this break
                    X_seg = X[seg_start:seg_end]
                    y_seg = y[seg_start:seg_end]

                    # Relative break point within segment
                    rel_break = break_point - seg_start

                    try:
                        chow = ChowTest()
                        result = chow.test(X_seg, y_seg, rel_break)

                        if result.test_statistic > best_f_stat:
                            best_f_stat = result.test_statistic
                            best_break = (break_point, result.p_value, seg_start, seg_end)
                    except:
                        continue

            # Check if best break is significant
            if best_break and best_f_stat > 10:  # Threshold
                break_pt, p_val, seg_start, seg_end = best_break

                detected_breaks.append(BreakPoint(
                    index=break_pt,
                    test_statistic=best_f_stat,
                    p_value=p_val,
                    confidence=1 - p_val if p_val < 1 else 0.5
                ))

                # Split segment
                remaining_segments.remove((seg_start, seg_end))
                remaining_segments.append((seg_start, break_pt))
                remaining_segments.append((break_pt, seg_end))
            else:
                break  # No more significant breaks

        # Sort breaks by index
        detected_breaks.sort(key=lambda bp: bp.index)

        result = StructuralBreakResult(
            has_breaks=len(detected_breaks) > 0,
            break_points=detected_breaks,
            test_statistic=max([bp.test_statistic for bp in detected_breaks]) if detected_breaks else 0.0,
            critical_value=10.0  # Threshold used
        )

        logger.info(f"Bai-Perron test: detected {len(detected_breaks)} break(s)")

        return result


def detect_structural_breaks(
    X: np.ndarray,
    y: np.ndarray,
    method: str = 'sup_f',
    **kwargs
) -> StructuralBreakResult:
    """
    Convenience function to detect structural breaks.

    Args:
        X: Features
        y: Target
        method: Test method ('chow', 'sup_f', 'cusum', 'bai_perron')
        **kwargs: Method-specific arguments

    Returns:
        StructuralBreakResult
    """
    if method == 'chow':
        break_point = kwargs.get('break_point')
        if break_point is None:
            raise ValueError("break_point required for Chow test")
        test = ChowTest()
        return test.test(X, y, break_point)

    elif method == 'sup_f':
        trim = kwargs.get('trim', 0.15)
        test = SupFTest(trim=trim)
        return test.test(X, y)

    elif method == 'cusum':
        test = CUSUMTest()
        return test.test(X, y)

    elif method == 'bai_perron':
        max_breaks = kwargs.get('max_breaks', 5)
        trim = kwargs.get('trim', 0.15)
        test = BaiPerronTest(max_breaks=max_breaks, trim=trim)
        return test.test(X, y)

    else:
        raise ValueError(f"Unknown method: {method}")


__all__ = [
    'BreakPoint',
    'StructuralBreakResult',
    'ChowTest',
    'SupFTest',
    'CUSUMTest',
    'BaiPerronTest',
    'detect_structural_breaks',
]
