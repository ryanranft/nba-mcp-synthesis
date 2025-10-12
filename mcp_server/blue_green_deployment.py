"""
Blue-Green Deployment Module
Zero-downtime deployments by switching between two environments.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environment"""
    BLUE = "blue"
    GREEN = "green"


class EnvironmentStatus(Enum):
    """Environment status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    FAILED = "failed"


@dataclass
class EnvironmentConfig:
    """Configuration for a deployment environment"""
    name: Environment
    model_id: str
    version: str
    status: EnvironmentStatus
    deployed_at: datetime
    health_checks_passed: int = 0
    health_checks_failed: int = 0


class BlueGreenDeploymentManager:
    """Manages blue-green deployments"""
    
    def __init__(self):
        """Initialize blue-green deployment manager"""
        self.environments: Dict[Environment, EnvironmentConfig] = {
            Environment.BLUE: EnvironmentConfig(
                name=Environment.BLUE,
                model_id="initial",
                version="1.0.0",
                status=EnvironmentStatus.ACTIVE,
                deployed_at=datetime.utcnow()
            ),
            Environment.GREEN: EnvironmentConfig(
                name=Environment.GREEN,
                model_id="initial",
                version="1.0.0",
                status=EnvironmentStatus.INACTIVE,
                deployed_at=datetime.utcnow()
            )
        }
        self.active_environment = Environment.BLUE
        self.deployment_history = []
    
    def get_active_environment(self) -> Environment:
        """Get currently active environment"""
        return self.active_environment
    
    def get_inactive_environment(self) -> Environment:
        """Get currently inactive environment"""
        return Environment.GREEN if self.active_environment == Environment.BLUE else Environment.BLUE
    
    def deploy_to_inactive(
        self,
        model_id: str,
        version: str
    ):
        """
        Deploy new version to inactive environment.
        
        Args:
            model_id: Model identifier
            version: Model version
        """
        inactive_env = self.get_inactive_environment()
        
        logger.info(
            f"Deploying {model_id} v{version} to {inactive_env.value} environment"
        )
        
        # Update inactive environment
        self.environments[inactive_env] = EnvironmentConfig(
            name=inactive_env,
            model_id=model_id,
            version=version,
            status=EnvironmentStatus.TESTING,
            deployed_at=datetime.utcnow()
        )
        
        logger.info(f"Deployment to {inactive_env.value} complete. Ready for testing.")
    
    def run_health_check(
        self,
        environment: Environment,
        check_fn: callable
    ) -> bool:
        """
        Run health check on environment.
        
        Args:
            environment: Environment to check
            check_fn: Health check function
            
        Returns:
            True if health check passed
        """
        env_config = self.environments[environment]
        
        try:
            logger.info(f"Running health check on {environment.value}")
            passed = check_fn()
            
            if passed:
                env_config.health_checks_passed += 1
                logger.info(f"✅ Health check passed for {environment.value}")
                return True
            else:
                env_config.health_checks_failed += 1
                logger.warning(f"❌ Health check failed for {environment.value}")
                return False
                
        except Exception as e:
            env_config.health_checks_failed += 1
            logger.error(f"❌ Health check error for {environment.value}: {e}")
            return False
    
    def switch_traffic(self):
        """Switch traffic to inactive environment (blue/green swap)"""
        old_active = self.active_environment
        new_active = self.get_inactive_environment()
        
        # Verify new environment is ready
        new_env = self.environments[new_active]
        if new_env.status != EnvironmentStatus.TESTING:
            raise ValueError(
                f"Cannot switch to {new_active.value}: status is {new_env.status.value}"
            )
        
        if new_env.health_checks_passed < 3:
            raise ValueError(
                f"Cannot switch to {new_active.value}: insufficient health checks "
                f"({new_env.health_checks_passed} < 3)"
            )
        
        # Perform switch
        logger.info(
            f"Switching traffic from {old_active.value} to {new_active.value}"
        )
        
        self.environments[new_active].status = EnvironmentStatus.ACTIVE
        self.environments[old_active].status = EnvironmentStatus.INACTIVE
        self.active_environment = new_active
        
        # Record in history
        self.deployment_history.append({
            "timestamp": datetime.utcnow(),
            "from": old_active.value,
            "to": new_active.value,
            "model_id": new_env.model_id,
            "version": new_env.version
        })
        
        logger.info(
            f"✅ Traffic switched to {new_active.value} "
            f"({new_env.model_id} v{new_env.version})"
        )
    
    def rollback(self):
        """Rollback to previous environment"""
        if not self.deployment_history:
            raise ValueError("No deployment history to rollback")
        
        logger.warning("Initiating rollback...")
        
        # Switch back
        old_active = self.active_environment
        new_active = self.get_inactive_environment()
        
        self.environments[new_active].status = EnvironmentStatus.ACTIVE
        self.environments[old_active].status = EnvironmentStatus.FAILED
        self.active_environment = new_active
        
        logger.warning(f"✅ Rolled back to {new_active.value}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status"""
        blue_env = self.environments[Environment.BLUE]
        green_env = self.environments[Environment.GREEN]
        
        return {
            "active_environment": self.active_environment.value,
            "blue": {
                "model_id": blue_env.model_id,
                "version": blue_env.version,
                "status": blue_env.status.value,
                "deployed_at": blue_env.deployed_at.isoformat(),
                "health_checks_passed": blue_env.health_checks_passed,
                "health_checks_failed": blue_env.health_checks_failed
            },
            "green": {
                "model_id": green_env.model_id,
                "version": green_env.version,
                "status": green_env.status.value,
                "deployed_at": green_env.deployed_at.isoformat(),
                "health_checks_passed": green_env.health_checks_passed,
                "health_checks_failed": green_env.health_checks_failed
            },
            "deployments": len(self.deployment_history),
            "last_deployment": (
                self.deployment_history[-1] if self.deployment_history else None
            )
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("BLUE-GREEN DEPLOYMENT DEMO")
    print("=" * 80)
    
    manager = BlueGreenDeploymentManager()
    
    # Show initial status
    print("\n" + "=" * 80)
    print("INITIAL STATUS")
    print("=" * 80)
    
    status = manager.get_status()
    print(f"\nActive Environment: {status['active_environment'].upper()}")
    print(f"\nBlue:")
    print(f"  Model: {status['blue']['model_id']} v{status['blue']['version']}")
    print(f"  Status: {status['blue']['status']}")
    print(f"\nGreen:")
    print(f"  Model: {status['green']['model_id']} v{status['green']['version']}")
    print(f"  Status: {status['green']['status']}")
    
    # Deploy new version
    print("\n" + "=" * 80)
    print("DEPLOYING NEW VERSION")
    print("=" * 80)
    
    manager.deploy_to_inactive(
        model_id="nba_predictor_v2",
        version="2.0.0"
    )
    
    print(f"✅ Deployed to {manager.get_inactive_environment().value}")
    
    # Run health checks
    print("\n" + "=" * 80)
    print("RUNNING HEALTH CHECKS")
    print("=" * 80)
    
    def mock_health_check():
        # Simulate health check
        import random
        return random.random() > 0.1  # 90% success rate
    
    inactive_env = manager.get_inactive_environment()
    for i in range(5):
        passed = manager.run_health_check(inactive_env, mock_health_check)
        result = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  Health Check {i+1}: {result}")
    
    # Show status before switch
    print("\n" + "=" * 80)
    print("STATUS BEFORE SWITCH")
    print("=" * 80)
    
    status = manager.get_status()
    inactive = manager.get_inactive_environment().value
    print(f"\n{inactive.upper()} Environment:")
    print(f"  Model: {status[inactive]['model_id']} v{status[inactive]['version']}")
    print(f"  Status: {status[inactive]['status']}")
    print(f"  Health Checks: ✅ {status[inactive]['health_checks_passed']} | "
          f"❌ {status[inactive]['health_checks_failed']}")
    
    # Switch traffic
    print("\n" + "=" * 80)
    print("SWITCHING TRAFFIC")
    print("=" * 80)
    
    try:
        manager.switch_traffic()
        print("✅ Traffic switch successful!")
    except ValueError as e:
        print(f"❌ Traffic switch failed: {e}")
    
    # Show final status
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    
    status = manager.get_status()
    print(f"\nActive Environment: {status['active_environment'].upper()}")
    print(f"\nBlue:")
    print(f"  Model: {status['blue']['model_id']} v{status['blue']['version']}")
    print(f"  Status: {status['blue']['status']}")
    print(f"\nGreen:")
    print(f"  Model: {status['green']['model_id']} v{status['green']['version']}")
    print(f"  Status: {status['green']['status']}")
    
    print(f"\nTotal Deployments: {status['deployments']}")
    
    # Demonstrate rollback capability
    print("\n" + "=" * 80)
    print("ROLLBACK CAPABILITY")
    print("=" * 80)
    print("✅ Rollback available (use manager.rollback())")
    
    print("\n" + "=" * 80)
    print("Blue-Green Deployment Demo Complete!")
    print("=" * 80)

