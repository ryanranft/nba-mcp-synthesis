"""
End-to-End Workflow Integration Tests

Tests complete workflows spanning multiple agents from start to finish.

Workflows Covered:
- Full ML pipeline (validation → training → deployment → monitoring)
- Econometric analysis pipeline
- Error recovery across agents
- Performance monitoring across pipeline
- Security-integrated workflows
- Multi-model deployment workflows
"""

import pytest
import pandas as pd
import numpy as np
import time
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


@pytest.mark.end_to_end
class TestMLPipelineWorkflow:
    """Test complete ML pipeline from data to deployment"""

    def test_full_ml_pipeline_workflow(
        self, sample_player_data, validation_rules, test_helper
    ):
        """
        Test complete ML pipeline: Validation → Training → Deployment → Monitoring

        Agents involved: 4 (Validation), 5 (Training), 6 (Deployment), 2 (Monitoring)
        """
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        workflow_state = {
            "validation_passed": False,
            "training_completed": False,
            "model_deployed": False,
            "monitoring_active": False,
            "model": None,
            "deployment_config": None,
        }

        # Step 1: Data Validation (Agent 4)
        @profile
        def validate_data(data, rules):
            """Validate data quality"""
            errors = []

            # Check required columns
            for col in rules["required_columns"]:
                if col not in data.columns:
                    errors.append(f"Missing column: {col}")

            # Check for nulls
            null_counts = data[rules["required_columns"]].isnull().sum()
            if null_counts.any():
                errors.append("Null values found in required columns")

            # Check value ranges
            if "points" in data.columns:
                if (data["points"] < 0).any():
                    errors.append("Negative points values found")

            workflow_state["validation_passed"] = len(errors) == 0
            return len(errors) == 0, errors

        # Step 2: Model Training (Agent 5)
        @profile
        def train_model(data):
            """Train ML model"""
            X = data[["minutes"]]
            y = data["points"]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = LinearRegression()
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)

            workflow_state["training_completed"] = True
            workflow_state["model"] = model

            return {
                "model": model,
                "score": score,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            }

        # Step 3: Model Deployment (Agent 6)
        @profile
        def deploy_model(model, version, environment="staging"):
            """Deploy model to environment"""
            deployment = {
                "model": model,
                "version": version,
                "environment": environment,
                "deployed_at": pd.Timestamp.now(),
                "status": "active",
            }

            workflow_state["model_deployed"] = True
            workflow_state["deployment_config"] = deployment

            return deployment

        # Execute workflow
        valid, errors = validate_data(sample_player_data, validation_rules)
        assert valid, f"Validation should pass: {errors}"

        training_result = train_model(sample_player_data)
        assert training_result["score"] is not None

        deployment = deploy_model(
            training_result["model"], version="1.0.0", environment="staging"
        )
        assert deployment["status"] == "active"

        # Step 4: Verify Monitoring (Agent 2)
        stats = profiler.get_summary()
        workflow_state["monitoring_active"] = stats["total_calls"] >= 3

        # Verify complete workflow
        assert workflow_state["validation_passed"], "Validation should pass"
        assert workflow_state["training_completed"], "Training should complete"
        assert workflow_state["model_deployed"], "Model should be deployed"
        assert workflow_state["monitoring_active"], "Monitoring should track all steps"

        # Test deployed model
        test_input = sample_player_data[["minutes"]].head(5)
        predictions = deployment["model"].predict(test_input)
        assert len(predictions) == 5


@pytest.mark.end_to_end
class TestEconometricPipelineWorkflow:
    """Test complete econometric analysis pipeline"""

    def test_econometric_analysis_pipeline(
        self, sample_player_data, time_series_data, test_helper
    ):
        """
        Test econometric pipeline: Data prep → Analysis → Results

        Agents involved: 4 (Validation), 8 (Econometrics), 2 (Monitoring)
        """
        from mcp_server.time_series import TimeSeriesAnalyzer
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        workflow_state = {
            "data_prepared": False,
            "analysis_completed": False,
            "results_generated": False,
        }

        # Step 1: Data Preparation
        @profile
        def prepare_time_series_data(data):
            """Prepare data for time series analysis"""
            # Ensure no nulls
            clean_data = data.dropna()

            # Ensure sufficient length
            if len(clean_data) < 50:
                raise ValueError("Insufficient data for time series analysis")

            workflow_state["data_prepared"] = True
            return clean_data

        # Step 2: Time Series Analysis
        @profile
        def analyze_time_series(ts_data):
            """Run time series analysis"""
            analyzer = TimeSeriesAnalyzer(
                data=pd.DataFrame({"points": ts_data.head(200)}), target_column="points"
            )

            workflow_state["analysis_completed"] = True
            return analyzer

        # Step 3: Generate Results
        @profile
        def generate_results(analyzer):
            """Generate analysis results"""
            results = {
                "data_points": len(analyzer.data),
                "target_column": analyzer.target_column,
                "analysis_type": "time_series",
                "timestamp": pd.Timestamp.now(),
            }

            workflow_state["results_generated"] = True
            return results

        # Execute pipeline
        prepared_data = prepare_time_series_data(time_series_data)
        assert len(prepared_data) >= 50

        analyzer = analyze_time_series(prepared_data)
        assert analyzer.target_column == "points"

        results = generate_results(analyzer)
        assert results["analysis_type"] == "time_series"

        # Verify monitoring
        stats = profiler.get_summary()
        assert stats["total_calls"] >= 3

        # Verify complete workflow
        assert workflow_state["data_prepared"]
        assert workflow_state["analysis_completed"]
        assert workflow_state["results_generated"]


@pytest.mark.end_to_end
class TestErrorRecoveryWorkflow:
    """Test error handling and recovery across agents"""

    def test_error_recovery_with_retry_workflow(self, sample_player_data):
        """
        Test error recovery across multiple agents

        Agents involved: 1 (Error Handling), 2 (Monitoring), 4 (Validation)
        """
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        workflow_state = {
            "attempts": 0,
            "failures": 0,
            "recoveries": 0,
            "final_success": False,
        }

        @profile
        def flaky_data_processing(data, fail_threshold=2):
            """Simulate flaky processing that succeeds after retries"""
            workflow_state["attempts"] += 1

            # Fail first N attempts
            if workflow_state["attempts"] < fail_threshold:
                workflow_state["failures"] += 1
                raise ConnectionError(
                    f"Temporary failure (attempt {workflow_state['attempts']})"
                )

            # Process successfully
            result = data.groupby("player_id")["points"].mean()
            return result

        # Retry logic with monitoring
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                result = flaky_data_processing(sample_player_data)
                workflow_state["final_success"] = True
                break
            except ConnectionError as e:
                last_error = e
                workflow_state["recoveries"] += 1
                if attempt < max_retries - 1:
                    time.sleep(0.01)  # Small delay before retry
                else:
                    raise

        # Verify workflow
        assert workflow_state["attempts"] >= 2, "Should have multiple attempts"
        assert workflow_state["failures"] >= 1, "Should have failures"
        assert workflow_state["recoveries"] >= 1, "Should have retries"
        assert workflow_state["final_success"], "Should ultimately succeed"

        # Verify monitoring tracked all attempts
        stats = profiler.get_summary()
        assert stats["total_calls"] >= workflow_state["attempts"]


@pytest.mark.end_to_end
class TestPerformanceOptimizationWorkflow:
    """Test performance optimization across pipeline"""

    def test_optimized_data_pipeline_workflow(self, large_player_dataset, test_helper):
        """
        Test optimized pipeline: Query opt → Caching → Parallel processing

        Agents involved: 9 (Performance), 2 (Monitoring)
        """
        from mcp_server.optimization.query_optimizer import QueryOptimizer
        from mcp_server.optimization.cache_manager import CacheManager
        from mcp_server.distributed.parallel_executor import ParallelExecutor
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        workflow_state = {
            "queries_optimized": 0,
            "cache_hits": 0,
            "parallel_tasks_completed": 0,
        }

        # Initialize optimization components
        optimizer = QueryOptimizer()
        cache = CacheManager(redis_url=None)
        executor = ParallelExecutor(max_workers=4, use_processes=False)

        # Step 1: Track query execution
        @profile
        def execute_query_with_optimization(query, data):
            """Execute query with tracking"""
            start = time.time()

            # Check cache first
            cache_key = hash(query)
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                workflow_state["cache_hits"] += 1
                return cached_result

            # Execute query
            if "aggregate" in query:
                result = data.groupby("player_id")["points"].mean()
            else:
                result = data["points"].describe()

            # Track execution time
            exec_time = (time.time() - start) * 1000
            optimizer.track_query_execution(query, exec_time)
            workflow_state["queries_optimized"] += 1

            # Cache result
            cache.set(cache_key, result, ttl=3600)

            return result

        # Step 2: Execute queries (some will hit cache)
        queries = [
            ("aggregate points by player", large_player_dataset.head(1000)),
            (
                "aggregate points by player",
                large_player_dataset.head(1000),
            ),  # Cache hit
            ("describe points stats", large_player_dataset.head(1000)),
        ]

        for query, data in queries:
            execute_query_with_optimization(query, data)

        # Step 3: Parallel processing
        @profile
        def process_player_batch(player_data):
            """Process player data in parallel"""
            workflow_state["parallel_tasks_completed"] += 1
            return {
                "player_id": player_data["player_id"].iloc[0],
                "avg_points": player_data["points"].mean(),
            }

        # Split data by player and process in parallel
        player_groups = [
            group for _, group in large_player_dataset.head(5000).groupby("player_id")
        ][:10]

        results = executor.execute_parallel(
            process_player_batch, [(group,) for group in player_groups]
        )

        # Verify workflow
        assert workflow_state["queries_optimized"] >= 2
        assert workflow_state["cache_hits"] >= 1, "Should have at least one cache hit"
        assert workflow_state["parallel_tasks_completed"] >= 10
        assert len(results) == 10

        # Verify monitoring
        stats = profiler.get_summary()
        assert stats["total_calls"] >= 12  # queries + parallel tasks


@pytest.mark.end_to_end
@pytest.mark.security
class TestSecurityIntegratedWorkflow:
    """Test security integrated throughout workflow"""

    def test_secure_data_access_workflow(self, sample_player_data):
        """
        Test security checks throughout data access workflow

        Agents involved: 3 (Security), 1 (Error Handling), 2 (Monitoring)
        """
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        workflow_state = {
            "authenticated": False,
            "authorized": False,
            "data_accessed": False,
            "audit_logged": False,
            "security_events": [],
        }

        @profile
        def authenticate_user(user_id, credentials):
            """Step 1: Authenticate user"""
            if not user_id or not credentials:
                workflow_state["security_events"].append("auth_failed")
                raise PermissionError("Authentication required")

            workflow_state["authenticated"] = True
            workflow_state["security_events"].append("auth_success")
            return True

        @profile
        def authorize_data_access(user_id, resource, permission="read"):
            """Step 2: Authorize access"""
            if not workflow_state["authenticated"]:
                workflow_state["security_events"].append("authz_failed_no_auth")
                raise PermissionError("Must authenticate first")

            # Check permissions
            if user_id == "admin" or permission == "read":
                workflow_state["authorized"] = True
                workflow_state["security_events"].append("authz_success")
                return True

            workflow_state["security_events"].append("authz_failed_insufficient")
            raise PermissionError("Insufficient permissions")

        @profile
        def access_data(user_id, data):
            """Step 3: Access data"""
            if not workflow_state["authorized"]:
                workflow_state["security_events"].append("access_denied")
                raise PermissionError("Not authorized")

            # Log access
            workflow_state["security_events"].append(f"data_accessed_by_{user_id}")
            workflow_state["data_accessed"] = True

            # Return filtered data
            return data.head(100)

        @profile
        def log_audit_trail():
            """Step 4: Log audit trail"""
            audit_entry = {
                "timestamp": pd.Timestamp.now(),
                "events": workflow_state["security_events"],
                "authenticated": workflow_state["authenticated"],
                "authorized": workflow_state["authorized"],
                "data_accessed": workflow_state["data_accessed"],
            }

            workflow_state["audit_logged"] = True
            return audit_entry

        # Execute secure workflow
        authenticate_user("test_user", {"password": "test123"})
        authorize_data_access("test_user", "player_data", permission="read")
        result_data = access_data("test_user", sample_player_data)
        audit = log_audit_trail()

        # Verify workflow
        assert workflow_state["authenticated"]
        assert workflow_state["authorized"]
        assert workflow_state["data_accessed"]
        assert workflow_state["audit_logged"]
        assert len(result_data) == 100

        # Verify security events
        assert "auth_success" in workflow_state["security_events"]
        assert "authz_success" in workflow_state["security_events"]
        assert "data_accessed_by_test_user" in workflow_state["security_events"]

        # Verify monitoring
        stats = profiler.get_summary()
        assert stats["total_calls"] >= 4


@pytest.mark.end_to_end
def test_comprehensive_system_workflow(
    sample_player_data, time_series_data, validation_rules, test_helper
):
    """
    Comprehensive system test with all agents working together

    Workflow: Security → Validation → Training → Deployment → Performance monitoring
    Agents: 1, 2, 3, 4, 5, 6, 9
    """
    from mcp_server.profiling.performance import profile, get_profiler
    from mcp_server.optimization.cache_manager import CacheManager

    profiler = get_profiler()
    profiler.reset()

    workflow_state = {
        "steps_completed": [],
        "errors": [],
        "model": None,
        "deployment": None,
    }

    try:
        # Step 1: Security (Agent 3)
        @profile
        def security_check(user_role):
            if user_role not in ["admin", "analyst"]:
                raise PermissionError("Unauthorized")
            workflow_state["steps_completed"].append("security")
            return True

        security_check("analyst")

        # Step 2: Data Validation (Agent 4)
        @profile
        def validate_data(data, rules):
            for col in rules["required_columns"]:
                if col not in data.columns:
                    raise ValueError(f"Missing column: {col}")
            workflow_state["steps_completed"].append("validation")
            return True

        validate_data(sample_player_data, validation_rules)

        # Step 3: Model Training (Agent 5)
        @profile
        def train_model(data):
            X = data[["minutes"]]
            y = data["points"]
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = LinearRegression()
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)

            workflow_state["model"] = model
            workflow_state["steps_completed"].append("training")
            return {"model": model, "score": score}

        training_result = train_model(sample_player_data)

        # Step 4: Deployment (Agent 6)
        @profile
        def deploy_model(model, version):
            deployment = {
                "model": model,
                "version": version,
                "environment": "production",
                "deployed_at": pd.Timestamp.now(),
            }
            workflow_state["deployment"] = deployment
            workflow_state["steps_completed"].append("deployment")
            return deployment

        deployment = deploy_model(training_result["model"], "1.0.0")

        # Step 5: Caching (Agent 9)
        cache = CacheManager(redis_url=None)
        cache.set("deployed_model_v1", deployment, ttl=3600)
        cached = cache.get("deployed_model_v1")
        assert cached is not None
        workflow_state["steps_completed"].append("caching")

    except Exception as e:
        workflow_state["errors"].append(str(e))
        raise

    # Verify complete workflow
    expected_steps = ["security", "validation", "training", "deployment", "caching"]
    assert (
        workflow_state["steps_completed"] == expected_steps
    ), f"Expected {expected_steps}, got {workflow_state['steps_completed']}"

    assert (
        len(workflow_state["errors"]) == 0
    ), f"Workflow should complete without errors: {workflow_state['errors']}"

    assert workflow_state["model"] is not None
    assert workflow_state["deployment"] is not None

    # Verify monitoring tracked all operations
    stats = profiler.get_summary()
    assert stats["total_calls"] >= 4  # security, validation, training, deployment

    # Test deployed model
    test_input = sample_player_data[["minutes"]].head(5)
    predictions = workflow_state["deployment"]["model"].predict(test_input)
    assert len(predictions) == 5
