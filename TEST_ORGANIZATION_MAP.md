# Test Organization Map

**Date**: 2025-10-22
**Purpose**: Organize all 85 test files by category and testing purpose
**Total Tests**: 85 files, ~34,000 lines

---

## Executive Summary

### Organization Structure
Tests are organized into **5 major categories** (A-E):
- **Category A**: MCP Tools Testing (30 files)
- **Category B**: Book Analysis Workflow (10 files)
- **Category C**: Automated Deployment (6 files)
- **Category D**: Infrastructure Testing (21 files)
- **Category E**: Integration Testing (18 files)

### Test Execution Strategy
1. **Run Category D first** (Infrastructure) - Validates foundation
2. **Run Category A** (MCP Tools) - Tests core functionality
3. **Run Category B** (Book Analysis) - Tests workflow
4. **Run Category C** (Deployment) - Tests automation
5. **Run Category E last** (Integration) - Tests end-to-end flows

---

## Category A: MCP Tools Testing (Phases 1-10)

**Purpose**: Test all MCP tool functionality across 10 phases
**Total**: 30 files, ~14,373 lines
**Last Run**: October 18, 2025
**Status**: 97% passing (29/30 tests passing)

### A1: Foundation & Intelligence (Phases 1-2)
**Purpose**: Test formula intelligence and suggestion systems

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase2_formula_intelligence.py` | ~450 | 15+ | Formula type identification, tool suggestions | HIGH |
| `test_phase2_2_formula_extraction.py` | ~420 | 12+ | Extract formulas from text, LaTeX parsing | HIGH |
| `test_phase2_3_formula_builder.py` | ~400 | 10+ | Build formulas from components | MEDIUM |

**Total**: 3 files, ~1,270 lines

**Run Command**:
```bash
# Run all Phase 2 tests
python scripts/test_phase2_formula_intelligence.py
python scripts/test_phase2_2_formula_extraction.py
python scripts/test_phase2_3_formula_builder.py
```

**Expected Time**: ~5-7 minutes
**Expected Cost**: $0 (no API calls)

---

### A2: Advanced Features (Phase 3)
**Purpose**: Test validation, comparison, and harmonization

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase3_1_formula_playground.py` | ~380 | 10+ | Interactive formula testing | MEDIUM |
| `test_phase3_2_visualization_engine.py` | ~390 | 12+ | Formula visualization | MEDIUM |
| `test_phase3_3_formula_validation.py` | ~400 | 15+ | Validation system | HIGH |
| `test_phase3_4_formula_comparison.py` | ~410 | 12+ | Multi-book comparison | MEDIUM |

**Total**: 4 files, ~1,580 lines

**Run Command**:
```bash
# Run all Phase 3 tests
for test in scripts/test_phase3_*.py; do python "$test"; done
```

**Expected Time**: ~8-10 minutes
**Expected Cost**: $0 (no API calls)

---

### A3: Symbolic Regression (Phase 5)
**Purpose**: Test formula discovery from data

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase5_1_symbolic_regression.py` | ~420 | 7 | Formula discovery, validation | HIGH |
| `test_phase5_2_natural_language_formula.py` | ~400 | 10+ | NL to formula conversion | MEDIUM |
| `test_phase5_3_formula_dependency_graph.py` | ~380 | 8+ | Dependency tracking | MEDIUM |

**Total**: 3 files, ~1,200 lines

**Known Issue**: Phase 5.1 has 1 failing validation test (known limitation)

**Run Command**:
```bash
python scripts/test_phase5_1_symbolic_regression.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (no API calls)

---

### A4: Book Analysis (Phase 6)
**Purpose**: Test automated book reading and analysis

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase6_1_automated_book_analysis.py` | 481 | 12+ | Multi-book analysis automation | HIGH |
| `test_phase6_2_cross_reference_system.py` | 640 | 15+ | Cross-book referencing | MEDIUM |

**Total**: 2 files, 1,121 lines

**Run Command**:
```bash
python scripts/test_phase6_1_automated_book_analysis.py
```

**Expected Time**: ~5-7 minutes
**Expected Cost**: $0 (mock data)

---

### A5: ML Core (Phase 7)
**Purpose**: Test machine learning tools and algorithms

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase7_1_intelligent_recommendations.py` | 465 | 10+ | AI-powered recommendations | HIGH |
| `test_phase7_2_automated_formula_discovery.py` | 541 | 12+ | Automated discovery | HIGH |
| `test_phase7_3_smart_context_analysis.py` | 708 | 15+ | Context understanding | MEDIUM |
| `test_phase7_4_predictive_analytics.py` | 813 | 18+ | Predictive models | MEDIUM |
| `test_phase7_5_automated_report_generation.py` | 733 | 14+ | Report automation | LOW |
| `test_phase7_6_intelligent_error_correction.py` | 713 | 12+ | Error detection/correction | MEDIUM |

**Total**: 6 files, 3,973 lines

**Run Command**:
```bash
# Run ML core tests
python scripts/test_sprint7_ml_tools.py  # Comprehensive ML test suite
```

**Expected Time**: ~12-15 minutes
**Expected Cost**: $0 (mock data)

---

### A6: ML Evaluation (Phase 8)
**Purpose**: Test model evaluation and metrics

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase8_1_advanced_formula_intelligence.py` | 843 | 20+ | Advanced intelligence | MEDIUM |
| `test_phase8_2_formula_usage_analytics.py` | 722 | 15+ | Usage tracking/analytics | LOW |
| `test_phase8_3_realtime_calculation_service.py` | 649 | 12+ | Real-time calculations | MEDIUM |

**Total**: 3 files, 2,214 lines

**Run Command**:
```bash
python scripts/test_sprint8_evaluation_tools.py
```

**Expected Time**: ~10-12 minutes
**Expected Cost**: $0 (mock data)

---

### A7: Math/Stats Expansion (Phase 9)
**Purpose**: Test mathematical operations and NBA metrics

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase9_1_advanced_formula_intelligence.py` | 701 | 18+ | Advanced formulas | MEDIUM |
| `test_phase9_2_multimodal_formula_processing.py` | ~450 | 12+ | Multimodal processing | LOW |
| `test_phase9_3_advanced_visualization_engine.py` | 486 | 14+ | Advanced visualizations | LOW |

**Total**: 3 files, ~1,637 lines

**Run Command**:
```bash
python scripts/test_math_stats_features.py
```

**Expected Time**: ~8-10 minutes
**Expected Cost**: $0 (no API calls)

---

### A8: Performance & Production (Phase 10)
**Purpose**: Test deployment and monitoring systems

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_phase10_1_production_deployment_pipeline.py` | 508 | 12+ | Deployment pipeline | HIGH |
| `test_phase10_2_performance_monitoring.py` | ~450 | 10+ | Performance monitoring | HIGH |
| `test_phase10_3_documentation_training.py` | ~420 | 8+ | Documentation generation | LOW |

**Total**: 3 files, ~1,378 lines

**Run Command**:
```bash
python scripts/test_phase10_2_performance_monitoring.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (no API calls)

---

### Category A Summary

| Phase | Files | Lines | Priority Tests | Time | Cost |
|-------|-------|-------|----------------|------|------|
| Phase 2 | 3 | 1,270 | 3 | 5-7 min | $0 |
| Phase 3 | 4 | 1,580 | 1 | 8-10 min | $0 |
| Phase 5 | 3 | 1,200 | 1 | 6-8 min | $0 |
| Phase 6 | 2 | 1,121 | 1 | 5-7 min | $0 |
| Phase 7 | 6 | 3,973 | 2 | 12-15 min | $0 |
| Phase 8 | 3 | 2,214 | 0 | 10-12 min | $0 |
| Phase 9 | 3 | 1,637 | 0 | 8-10 min | $0 |
| Phase 10 | 3 | 1,378 | 2 | 6-8 min | $0 |

**Total**: 30 files, 14,373 lines, 60-77 minutes, $0

---

## Category B: Book Analysis Workflow Testing

**Purpose**: Test complete book analysis workflow (TIER 0-3)
**Total**: 10 files, ~3,542 lines
**Last Run**: October 18, 2025
**Status**: All passing

### B1: Book Reading & Processing
**Purpose**: Test book format handling (EPUB, PDF)

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_book_features.py` | ~420 | 12+ | General book features | HIGH |
| `test_epub_pdf_features.py` | 513 | 15+ | EPUB/PDF reading | HIGH |
| `test_pdf_reading.py` | ~350 | 10+ | PDF text extraction | MEDIUM |

**Total**: 3 files, ~1,283 lines

**Run Command**:
```bash
python scripts/test_epub_pdf_features.py
```

**Expected Time**: ~5-7 minutes
**Expected Cost**: $0 (local files)

---

### B2: Multi-Model Analysis
**Purpose**: Test different AI model configurations

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_four_model_analysis.py` | ~420 | 8+ | 4-model consensus | MEDIUM |
| `test_google_claude_analysis.py` | ~400 | 10+ | Gemini + Claude | HIGH |
| `test_multi_model_analysis.py` | ~410 | 10+ | Multi-model orchestration | MEDIUM |
| `ab_testing_framework.py` | 379 | 12+ | A/B testing framework | HIGH |
| `individual_model_tester.py` | ~350 | 8+ | Individual model tests | LOW |

**Total**: 5 files, ~1,959 lines

**Run Command**:
```bash
python scripts/test_google_claude_analysis.py  # Test dual-model
python scripts/ab_testing_framework.py          # Test A/B framework
```

**Expected Time**: ~8-10 minutes
**Expected Cost**: $0.50-$1 (if using real APIs for testing)

---

### B3: Workflow Orchestration
**Purpose**: Test complete analysis workflows

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `mock_test_3_books.py` | ~300 | 3 | 3-book analysis | HIGH |
| `overnight_test_suite.py` | ~500 | Multiple | Overnight batch processing | MEDIUM |

**Total**: 2 files, ~800 lines

**Run Command**:
```bash
python scripts/mock_test_3_books.py
```

**Expected Time**: ~3-5 minutes
**Expected Cost**: $0 (mock data)

---

### Category B Summary

| Subcategory | Files | Lines | Priority Tests | Time | Cost |
|-------------|-------|-------|----------------|------|------|
| Book Reading | 3 | 1,283 | 2 | 5-7 min | $0 |
| Multi-Model | 5 | 1,959 | 2 | 8-10 min | $0.50-$1 |
| Workflow | 2 | 800 | 1 | 3-5 min | $0 |

**Total**: 10 files, 3,542 lines, 16-22 minutes, $0.50-$1

---

## Category C: Automated Deployment Testing

**Purpose**: Test automated code generation and deployment
**Total**: 6 files, ~2,361 lines
**Last Run**: October 22, 2025 (partial)
**Status**: Deployment system recently fixed

### C1: Test Generation & Execution
**Purpose**: Test the test generator and runner

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_generator_and_runner.py` | 651 | Internal | Test generation system | CRITICAL |
| `test_implementation_runner.py` | ~400 | 8+ | Implementation execution | HIGH |

**Total**: 2 files, ~1,051 lines

**Run Command**:
```bash
# Test the test generator itself
python scripts/test_generator_and_runner.py --dry-run
```

**Expected Time**: ~5-7 minutes
**Expected Cost**: $0.10-$0.20 (Claude API for test generation)

---

### C2: Validation & Safety
**Purpose**: Test deployment safety mechanisms

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_validation_with_sample_data.py` | ~380 | 10+ | Validation system | HIGH |
| `test_circuit_breaker.py` | ~350 | 8+ | Circuit breaker logic | HIGH |
| `test_phase_skip_fix.py` | ~300 | 5+ | Phase skip handling | MEDIUM |
| `test_pass5_only.py` | ~280 | 3+ | Single phase testing | LOW |

**Total**: 4 files, ~1,310 lines

**Run Command**:
```bash
python scripts/test_circuit_breaker.py
python scripts/test_validation_with_sample_data.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (no API calls)

---

### Category C Summary

| Subcategory | Files | Lines | Priority Tests | Time | Cost |
|-------------|-------|-------|----------------|------|------|
| Test Generation | 2 | 1,051 | 2 | 5-7 min | $0.10-$0.20 |
| Validation | 4 | 1,310 | 2 | 6-8 min | $0 |

**Total**: 6 files, 2,361 lines, 11-15 minutes, $0.10-$0.20

---

## Category D: Infrastructure Testing

**Purpose**: Test core infrastructure (databases, APIs, configs)
**Total**: 21 files, ~7,275 lines
**Last Run**: October 18-22, 2025
**Status**: All passing

### D1: Database & Storage
**Purpose**: Test database connections and operations

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_database_integration.py` | ~400 | 12+ | PostgreSQL integration | CRITICAL |
| `test_all_connectors.py` | 439 | 20+ | All MCP connectors | HIGH |

**Total**: 2 files, ~839 lines

**Run Command**:
```bash
python scripts/test_database_integration.py
python tests/test_all_connectors.py
```

**Expected Time**: ~4-6 minutes
**Expected Cost**: $0 (no API calls, uses local/test DB)

---

### D2: MCP Server & Client
**Purpose**: Test MCP server functionality

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_fastmcp_server.py` | ~420 | 15+ | MCP server | CRITICAL |
| `test_mcp_client.py` | ~380 | 12+ | MCP client | CRITICAL |
| `test_mcp_connection.py` | ~350 | 10+ | MCP connections | HIGH |
| `integration/test_mcp_integration.py` | 499 | 18+ | MCP integration | HIGH |

**Total**: 4 files, ~1,649 lines

**Run Command**:
```bash
python scripts/test_mcp_connection.py
python tests/integration/test_mcp_integration.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (no API calls)

---

### D3: Security & Secrets
**Purpose**: Test authentication and secrets management

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_security.py` | 728 | 25+ | Security scanning | HIGH |
| `test_auth.py` | ~380 | 12+ | Authentication | HIGH |
| `test_secrets_manager.py` | ~350 | 10+ | Secrets management | CRITICAL |
| `test_unified_secrets_manager.py` | 289 | 8+ | Unified secrets system | CRITICAL |
| `test_all_credentials.py` | 909 | 34+ | All API credentials | CRITICAL |
| `test_new_projects_secrets.py` | ~400 | 12+ | New secrets system | HIGH |
| `test_security_scanning.py` | ~350 | 10+ | Security scans | MEDIUM |

**Total**: 7 files, ~3,406 lines

**Run Command**:
```bash
# Test secrets loading
python tests/test_unified_secrets_manager.py

# Test all API credentials
python scripts/test_all_credentials.py
```

**Expected Time**: ~8-10 minutes
**Expected Cost**: $0.05-$0.10 (minimal API test calls)

---

### D4: Configuration & Notifications
**Purpose**: Test configuration systems and notifications

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_config.py` | ~350 | 10+ | Configuration system | HIGH |
| `test_docker_scenarios.py` | ~400 | 8+ | Docker integration | LOW |
| `test_notifications.py` | ~380 | 6+ | Notification system | LOW |
| `test_ollama_primary.py` | ~350 | 5+ | Ollama integration | LOW |

**Total**: 4 files, ~1,480 lines

**Run Command**:
```bash
python tests/test_config.py
```

**Expected Time**: ~4-6 minutes
**Expected Cost**: $0 (no API calls)

---

### D5: Math & Formula Tools
**Purpose**: Test mathematical operation tools

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_algebraic_tools.py` | ~400 | 15+ | Algebraic operations | HIGH |
| `test_enhanced_sports_formulas.py` | ~420 | 18+ | Sports formulas | MEDIUM |
| `test_new_nba_metrics.py` | ~380 | 12+ | NBA metrics | MEDIUM |
| `unit/test_algebra_tools.py` | 500 | 20+ | Algebra unit tests | HIGH |

**Total**: 4 files, ~1,700 lines

**Run Command**:
```bash
python scripts/test_algebraic_tools.py
python tests/unit/test_algebra_tools.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (no API calls)

---

### Category D Summary

| Subcategory | Files | Lines | Priority Tests | Time | Cost |
|-------------|-------|-------|----------------|------|------|
| Database | 2 | 839 | 2 | 4-6 min | $0 |
| MCP Server | 4 | 1,649 | 4 | 6-8 min | $0 |
| Security | 7 | 3,406 | 4 | 8-10 min | $0.05-$0.10 |
| Config | 4 | 1,480 | 1 | 4-6 min | $0 |
| Math Tools | 4 | 1,700 | 2 | 6-8 min | $0 |

**Total**: 21 files, 7,275 lines, 28-38 minutes, $0.05-$0.10

---

## Category E: Integration & End-to-End Testing

**Purpose**: Test complete workflows and integrations
**Total**: 18 files, ~6,844 lines
**Last Run**: October 18, 2025
**Status**: All passing

### E1: Workflow Integration
**Purpose**: Test complete analysis workflows end-to-end

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_integration.py` | ~420 | 15+ | General integration | HIGH |
| `test_e2e_workflow.py` | 510 | 12+ | End-to-end workflow | CRITICAL |
| `test_recursive_book_analysis.py` | 510 | 10+ | Recursive analysis | HIGH |
| `test_recommendation_integration.py` | 616 | 18+ | Recommendation flow | CRITICAL |
| `test_workflow_system.py` | ~420 | 12+ | Workflow orchestration | MEDIUM |
| `test_synthesis_direct.py` | ~420 | 8+ | Direct synthesis | MEDIUM |

**Total**: 6 files, ~2,896 lines

**Run Command**:
```bash
# Critical E2E test
python tests/test_e2e_workflow.py

# Recommendation integration
python tests/test_recommendation_integration.py
```

**Expected Time**: ~12-15 minutes
**Expected Cost**: $0.20-$0.50 (some API calls for full workflow)

---

### E2: Feature Integration
**Purpose**: Test integration of specific features

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_ml_integration.py` | ~400 | 12+ | ML feature integration | HIGH |
| `test_enhancements.py` | ~400 | 10+ | System enhancements | MEDIUM |
| `test_new_features.py` | ~380 | 8+ | New features | MEDIUM |
| `test_tier3_integration.py` | ~400 | 10+ | TIER 3 features | MEDIUM |

**Total**: 4 files, ~1,580 lines

**Run Command**:
```bash
python scripts/test_ml_integration.py
```

**Expected Time**: ~6-8 minutes
**Expected Cost**: $0 (mock data)

---

### E3: External Integrations
**Purpose**: Test third-party integrations

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_deepseek_integration.py` | ~400 | 8+ | DeepSeek API | LOW |
| `test_great_expectations_integration.py` | ~420 | 10+ | Great Expectations | LOW |

**Total**: 2 files, ~820 lines

**Run Command**:
```bash
python tests/test_deepseek_integration.py
```

**Expected Time**: ~4-5 minutes
**Expected Cost**: $0.05-$0.10 (DeepSeek API calls)

---

### E4: Sprint Integration Tests
**Purpose**: Test sprint-specific integrations

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_sprint5_integration.py` | ~380 | 10+ | Sprint 5 features | MEDIUM |
| `test_sprint5_real_data.py` | ~390 | 8+ | Real data validation | MEDIUM |
| `test_sprint6_features.py` | ~400 | 10+ | Sprint 6 features | MEDIUM |

**Total**: 3 files, ~1,170 lines

**Run Command**:
```bash
python scripts/test_sprint6_features.py
```

**Expected Time**: ~5-7 minutes
**Expected Cost**: $0 (mock data)

---

### E5: Performance & Load Testing
**Purpose**: Test system under load and stress

| Test File | Lines | Tests | What It Tests | Priority |
|-----------|-------|-------|---------------|----------|
| `test_load.py` | 481 | 8+ | Load testing | MEDIUM |
| `test_resilience.py` | 705 | 15+ | System resilience | HIGH |
| `benchmarks/test_performance.py` | 646 | 12+ | Performance benchmarks | MEDIUM |

**Total**: 3 files, 1,832 lines

**Run Command**:
```bash
python tests/test_resilience.py
python tests/benchmarks/test_performance.py
```

**Expected Time**: ~10-15 minutes
**Expected Cost**: $0 (no API calls)

---

### Category E Summary

| Subcategory | Files | Lines | Priority Tests | Time | Cost |
|-------------|-------|-------|----------------|------|------|
| Workflow Integration | 6 | 2,896 | 4 | 12-15 min | $0.20-$0.50 |
| Feature Integration | 4 | 1,580 | 1 | 6-8 min | $0 |
| External Integration | 2 | 820 | 0 | 4-5 min | $0.05-$0.10 |
| Sprint Integration | 3 | 1,170 | 0 | 5-7 min | $0 |
| Performance | 3 | 1,832 | 1 | 10-15 min | $0 |

**Total**: 18 files, 6,844 lines, 37-50 minutes, $0.25-$0.60

---

## Testing Strategy & Execution Plan

### Recommended Execution Order

**Priority 1: Infrastructure (Category D)**
```bash
# 28-38 minutes, $0.05-$0.10
# Run these first to validate foundation
python tests/test_unified_secrets_manager.py
python scripts/test_database_integration.py
python scripts/test_mcp_connection.py
python scripts/test_algebraic_tools.py
```

**Priority 2: MCP Tools (Category A)**
```bash
# 60-77 minutes, $0
# Run core MCP functionality tests
python scripts/test_phase2_formula_intelligence.py
python scripts/test_sprint7_ml_tools.py
python scripts/test_sprint8_evaluation_tools.py
```

**Priority 3: Book Analysis (Category B)**
```bash
# 16-22 minutes, $0.50-$1
# Test book analysis workflow
python scripts/test_epub_pdf_features.py
python scripts/test_google_claude_analysis.py
```

**Priority 4: Deployment (Category C)**
```bash
# 11-15 minutes, $0.10-$0.20
# Test automated deployment
python scripts/test_circuit_breaker.py
python scripts/test_generator_and_runner.py --dry-run
```

**Priority 5: Integration (Category E)**
```bash
# 37-50 minutes, $0.25-$0.60
# Run end-to-end integration tests
python tests/test_e2e_workflow.py
python tests/test_recommendation_integration.py
python tests/test_resilience.py
```

### Total Execution Plan

| Priority | Category | Time | Cost | Critical Tests |
|----------|----------|------|------|----------------|
| 1 | Infrastructure (D) | 28-38 min | $0.05-$0.10 | 13 |
| 2 | MCP Tools (A) | 60-77 min | $0 | 10 |
| 3 | Book Analysis (B) | 16-22 min | $0.50-$1.00 | 5 |
| 4 | Deployment (C) | 11-15 min | $0.10-$0.20 | 4 |
| 5 | Integration (E) | 37-50 min | $0.25-$0.60 | 6 |

**Total**: 152-202 minutes (2.5-3.5 hours), $0.90-$1.90

---

## Quick Test Commands

### Run All Infrastructure Tests
```bash
# D1: Database
python scripts/test_database_integration.py
python tests/test_all_connectors.py

# D2: MCP Server
python scripts/test_mcp_connection.py
python tests/integration/test_mcp_integration.py

# D3: Security
python tests/test_unified_secrets_manager.py
python scripts/test_all_credentials.py

# D5: Math Tools
python scripts/test_algebraic_tools.py
```

### Run All MCP Phase Tests
```bash
# Sequential execution
for phase in 2 3 5 6 7 8 9 10; do
    echo "Testing Phase $phase..."
    python scripts/test_phase${phase}_*.py 2>/dev/null || \
    python scripts/test_sprint${phase}_*.py 2>/dev/null
done
```

### Run Critical Integration Tests
```bash
# E1: Critical workflows
python tests/test_e2e_workflow.py
python tests/test_recommendation_integration.py
python tests/test_resilience.py
```

### Run Full Test Suite
```bash
# Create comprehensive test runner
python scripts/run_comprehensive_test_suite.py --all
```

---

## Conclusion

### Organization Benefits
1. **Clear categories**: Easy to understand what each test covers
2. **Execution strategy**: Know which tests to run first
3. **Time estimates**: Plan test execution windows
4. **Cost tracking**: Budget for API-dependent tests
5. **Priority levels**: Focus on critical tests first

### Next Steps
1. **Phase 2.3**: Analyze test coverage (identify gaps)
2. **Phase 3**: Design new tests for gaps
3. **Phase 4**: Write missing tests
4. **Phase 5**: Execute comprehensive test suite
5. **Phase 6**: Generate recommendations
6. **Phase 7**: Deploy testing infrastructure

---

*Organization completed: 2025-10-22*
*Total organized: 85 files across 5 categories*
*Execution time: 2.5-3.5 hours | Estimated cost: $0.90-$1.90*
