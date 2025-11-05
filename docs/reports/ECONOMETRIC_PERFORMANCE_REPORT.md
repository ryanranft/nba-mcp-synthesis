# Econometric Suite Performance Report

**Generated**: 2025-11-04 18:53:28
**Methods Tested**: 26
**Configurations**: 26

---

## Executive Summary

**Overall Success Rate**: 100.0%

## Performance by Method

| Method | Small (1K) | Medium (10K) | Large (100K) | Status |
|--------|------------|--------------|--------------|--------|
| ARIMA | 1.65s | - | - | ✅ |
| VAR | 0.02s | - | - | ✅ |
| Panel Fixed Effects | 0.77s | - | - | ✅ |
| Panel Random Effects | 0.04s | - | - | ✅ |
| Propensity Score Matching | 3.60s | - | - | ✅ |
| Regression Discontinuity | 0.00s | - | - | ✅ |
| Instrumental Variables | 0.11s | - | - | ✅ |
| Bayesian VAR | 72.46s | - | - | ✅ |
| Particle Filter (Player) | 0.30s | - | - | ✅ |
| ARIMAX | 0.25s | - | - | ✅ |
| STL Decomposition | 0.03s | - | - | ✅ |
| Panel First-Difference | 0.06s | - | - | ✅ |
| Kernel Matching | 0.37s | - | - | ✅ |
| Doubly Robust | 1.18s | - | - | ✅ |
| Cox Proportional Hazards | 0.69s | - | - | ✅ |
| Kaplan-Meier | 0.02s | - | - | ✅ |
| Kalman Filter | 0.07s | - | - | ✅ |
| Markov Switching | 0.04s | - | - | ✅ |
| Dynamic Factor Model | 0.57s | - | - | ✅ |
| MSTL Decomposition | 0.04s | - | - | ✅ |
| Granger Causality | 0.02s | - | - | ✅ |
| VECM | 0.02s | - | - | ✅ |
| Synthetic Control | 0.04s | - | - | ✅ |
| Parametric Survival (Weibull) | 0.51s | - | - | ✅ |
| Frailty Model | 0.61s | - | - | ✅ |
| Competing Risks | 0.03s | - | - | ✅ |

## Memory Usage

| Method | Peak Memory (MB) |
|--------|------------------|
| ARIMA | 42.7 |
| VAR | 0.4 |
| Panel Fixed Effects | 24.6 |
| Panel Random Effects | 0.5 |
| Propensity Score Matching | 78.3 |
| Regression Discontinuity | 1.3 |
| Instrumental Variables | 4.7 |
| Bayesian VAR | 115.0 |
| Particle Filter (Player) | 0.4 |
| ARIMAX | 2.7 |
| STL Decomposition | 0.3 |
| Panel First-Difference | 0.6 |
| Kernel Matching | 0.7 |
| Doubly Robust | 0.9 |
| Cox Proportional Hazards | 5.2 |
| Kaplan-Meier | 0.5 |
| Kalman Filter | 0.9 |
| Markov Switching | 1.7 |
| Dynamic Factor Model | 7.7 |
| MSTL Decomposition | 0.3 |
| Granger Causality | 1.3 |
| VECM | 15.5 |
| Synthetic Control | 0.3 |
| Parametric Survival (Weibull) | 31.4 |
| Frailty Model | 1.1 |
| Competing Risks | 0.5 |

## Recommendations

**Slow Methods** (>10s):
- Bayesian VAR

## Production Readiness

**Real-time Capable** (<1s):
- ✅ VAR
- ✅ Panel Fixed Effects
- ✅ Panel Random Effects
- ✅ Regression Discontinuity
- ✅ Instrumental Variables
- ✅ Particle Filter (Player)
- ✅ ARIMAX
- ✅ STL Decomposition
- ✅ Panel First-Difference
- ✅ Kernel Matching
- ✅ Cox Proportional Hazards
- ✅ Kaplan-Meier
- ✅ Kalman Filter
- ✅ Markov Switching
- ✅ Dynamic Factor Model
- ✅ MSTL Decomposition
- ✅ Granger Causality
- ✅ VECM
- ✅ Synthetic Control
- ✅ Parametric Survival (Weibull)
- ✅ Frailty Model
- ✅ Competing Risks

**Interactive Use** (1-10s):
- ✓ ARIMA
- ✓ Propensity Score Matching
- ✓ Doubly Robust

**Batch Processing** (>10s):
- ⏰ Bayesian VAR

