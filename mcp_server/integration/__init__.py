"""
Integration Module (Agent 19)

Comprehensive integration of all NBA analytics components:
- Multi-model ensemble system
- End-to-end pipeline orchestration
- Integration validation and health checks
- Common workflows and templates

Key Modules:
- ensemble: Multi-model ensembles with various combination methods
- pipeline: End-to-end workflow orchestration
- validator: System health and integration testing

Integrates with:
- All modules: Universal integration framework

This is the capstone module that ties everything together.
"""

from mcp_server.integration.ensemble import (
    EnsembleMethod,
    EnsembleConfig,
    EnsemblePrediction,
    ModelEnsemble,
    ContextualEnsemble,
    create_ensemble,
)
from mcp_server.integration.pipeline import (
    StageStatus,
    PipelineStage,
    PipelineResult,
    Pipeline,
    PipelineTemplate,
)
from mcp_server.integration.validator import (
    HealthStatus,
    ModuleHealth,
    SystemHealth,
    IntegrationValidator,
    check_system_health,
    print_health_report,
)

__all__ = [
    # Ensemble
    "EnsembleMethod",
    "EnsembleConfig",
    "EnsemblePrediction",
    "ModelEnsemble",
    "ContextualEnsemble",
    "create_ensemble",
    # Pipeline
    "StageStatus",
    "PipelineStage",
    "PipelineResult",
    "Pipeline",
    "PipelineTemplate",
    # Validator
    "HealthStatus",
    "ModuleHealth",
    "SystemHealth",
    "IntegrationValidator",
    "check_system_health",
    "print_health_report",
]
