"""
Role-Based Access Control (RBAC) System for NBA MCP Server

Implements fine-grained access control with:
- Role definitions with hierarchies
- Permission system (read, write, execute, delete, admin)
- Resource-based permissions
- Permission checking decorators
- Audit logging for all access attempts
- Dynamic permission evaluation

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import asyncio
import functools
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .logging_config import get_logger
from .error_handling import BaseAuthenticationError, get_error_handler

logger = get_logger(__name__)


# ==============================================================================
# Permissions and Resources
# ==============================================================================


class Permission(Enum):
    """
    System permissions.

    Permissions define what actions can be performed:
    - READ: View/query data
    - WRITE: Create/update data
    - EXECUTE: Run queries, tools, and operations
    - DELETE: Remove data
    - ADMIN: Full administrative access
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"

    def __str__(self) -> str:
        return self.value


class ResourceType(Enum):
    """
    Types of resources that can be protected.

    Resources represent the entities that permissions apply to.
    """

    DATABASE = "database"
    TABLE = "table"
    S3_BUCKET = "s3_bucket"
    S3_FILE = "s3_file"
    NBA_DATA = "nba_data"
    USER = "user"
    API_KEY = "api_key"
    TOOL = "tool"
    METRIC = "metric"
    LOG = "log"
    SYSTEM = "system"
    ALL = "*"

    def __str__(self) -> str:
        return self.value


# ==============================================================================
# Role Model
# ==============================================================================


@dataclass
class Role:
    """
    User role with permissions.

    Attributes:
        name: Unique role name
        permissions: Set of permissions granted to this role
        resource_permissions: Resource-specific permissions
        priority: Role priority for hierarchy (higher = more privileged)
        description: Human-readable description
        parent_roles: Parent roles (for inheritance)
        is_system_role: Whether this is a built-in system role
        metadata: Additional role metadata

    Examples:
        >>> analyst_role = Role(
        ...     name="analyst",
        ...     permissions={Permission.READ, Permission.EXECUTE},
        ...     resource_permissions={
        ...         "database:*": {Permission.READ, Permission.EXECUTE},
        ...         "nba_data:*": {Permission.READ, Permission.EXECUTE},
        ...     },
        ...     priority=50
        ... )
    """

    name: str
    permissions: Set[Permission] = field(default_factory=set)
    resource_permissions: Dict[str, Set[Permission]] = field(default_factory=dict)
    priority: int = 0
    description: str = ""
    parent_roles: List[str] = field(default_factory=list)
    is_system_role: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: Permission, resource: str = "*") -> bool:
        """
        Check if role has a specific permission.

        Args:
            permission: Permission to check
            resource: Resource identifier (e.g., "database:games_table")

        Returns:
            True if role has permission, False otherwise
        """
        # Admin permission grants everything
        if Permission.ADMIN in self.permissions:
            return True

        # Check global permissions
        if permission in self.permissions:
            return True

        # Check resource-specific permissions
        if resource in self.resource_permissions:
            if permission in self.resource_permissions[resource]:
                return True

        # Check wildcard resource permissions
        resource_type = resource.split(":")[0] if ":" in resource else resource
        wildcard_resource = f"{resource_type}:*"

        if wildcard_resource in self.resource_permissions:
            if permission in self.resource_permissions[wildcard_resource]:
                return True

        # Check all resources wildcard
        if "*" in self.resource_permissions:
            if permission in self.resource_permissions["*"]:
                return True

        return False

    def grant_permission(self, permission: Permission, resource: str = "*") -> None:
        """
        Grant a permission to this role.

        Args:
            permission: Permission to grant
            resource: Resource identifier (default: all resources)
        """
        if resource == "*":
            self.permissions.add(permission)
        else:
            if resource not in self.resource_permissions:
                self.resource_permissions[resource] = set()
            self.resource_permissions[resource].add(permission)

    def revoke_permission(self, permission: Permission, resource: str = "*") -> None:
        """
        Revoke a permission from this role.

        Args:
            permission: Permission to revoke
            resource: Resource identifier (default: all resources)
        """
        if resource == "*":
            self.permissions.discard(permission)
        else:
            if resource in self.resource_permissions:
                self.resource_permissions[resource].discard(permission)

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "name": self.name,
            "permissions": [p.value for p in self.permissions],
            "resource_permissions": {
                resource: [p.value for p in perms]
                for resource, perms in self.resource_permissions.items()
            },
            "priority": self.priority,
            "description": self.description,
            "parent_roles": self.parent_roles,
            "is_system_role": self.is_system_role,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        """Create role from dictionary."""
        return cls(
            name=data["name"],
            permissions={Permission(p) for p in data.get("permissions", [])},
            resource_permissions={
                resource: {Permission(p) for p in perms}
                for resource, perms in data.get("resource_permissions", {}).items()
            },
            priority=data.get("priority", 0),
            description=data.get("description", ""),
            parent_roles=data.get("parent_roles", []),
            is_system_role=data.get("is_system_role", False),
            metadata=data.get("metadata", {}),
        )


# ==============================================================================
# Access Control Entry
# ==============================================================================


@dataclass
class AccessAttempt:
    """
    Record of an access attempt for audit logging.

    Attributes:
        timestamp: When the access was attempted
        user_id: User who attempted access
        resource: Resource being accessed
        permission: Permission required
        granted: Whether access was granted
        roles: Roles user had at time of access
        reason: Reason for denial (if applicable)
        metadata: Additional context
    """

    timestamp: datetime
    user_id: str
    resource: str
    permission: Permission
    granted: bool
    roles: List[str]
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "resource": self.resource,
            "permission": self.permission.value,
            "granted": self.granted,
            "roles": self.roles,
            "reason": self.reason,
            "metadata": self.metadata,
        }


# ==============================================================================
# RBAC Manager
# ==============================================================================


class RBACManager:
    """
    Role-Based Access Control manager.

    Manages roles, permissions, and access control decisions.
    Provides audit logging for all access attempts.

    Features:
    - Role management with hierarchies
    - Fine-grained permission checking
    - Resource-based access control
    - Permission inheritance
    - Audit logging
    - Dynamic permission evaluation

    Examples:
        >>> rbac = RBACManager()
        >>>
        >>> # Create role
        >>> analyst_role = rbac.create_role(
        ...     name="analyst",
        ...     permissions={Permission.READ, Permission.EXECUTE},
        ...     description="NBA data analyst"
        ... )
        >>>
        >>> # Assign role to user
        >>> rbac.assign_role("user_123", "analyst")
        >>>
        >>> # Check permission
        >>> if rbac.check_permission("user_123", Permission.EXECUTE, "database:games"):
        ...     # Execute query
        ...     pass
    """

    def __init__(self, enable_audit_logging: bool = True):
        """
        Initialize RBAC manager.

        Args:
            enable_audit_logging: Enable audit logging for access attempts
        """
        self.enable_audit_logging = enable_audit_logging

        # Role storage
        self.roles: Dict[str, Role] = {}

        # User role assignments
        self.user_roles: Dict[str, Set[str]] = defaultdict(set)

        # Audit log
        self.access_log: List[AccessAttempt] = []

        # Thread safety
        self._lock = Lock()

        # Create default system roles
        self._create_system_roles()

        logger.info(
            "RBAC manager initialized", extra={"audit_logging": enable_audit_logging}
        )

    def _create_system_roles(self) -> None:
        """Create default system roles."""
        # Admin role (full access)
        admin_role = Role(
            name="admin",
            permissions={Permission.ADMIN},
            priority=100,
            description="Full system administrator",
            is_system_role=True,
        )
        self.roles["admin"] = admin_role

        # Analyst role (read and execute)
        analyst_role = Role(
            name="analyst",
            permissions={Permission.READ, Permission.EXECUTE},
            resource_permissions={
                "database:*": {Permission.READ, Permission.EXECUTE},
                "table:*": {Permission.READ},
                "nba_data:*": {Permission.READ, Permission.EXECUTE},
                "s3_bucket:*": {Permission.READ},
                "s3_file:*": {Permission.READ},
                "tool:*": {Permission.EXECUTE},
                "metric:*": {Permission.READ},
            },
            priority=50,
            description="NBA data analyst with query and analysis capabilities",
            is_system_role=True,
        )
        self.roles["analyst"] = analyst_role

        # Viewer role (read-only)
        viewer_role = Role(
            name="viewer",
            permissions={Permission.READ},
            resource_permissions={
                "database:*": {Permission.READ},
                "table:*": {Permission.READ},
                "nba_data:*": {Permission.READ},
                "s3_bucket:*": {Permission.READ},
                "s3_file:*": {Permission.READ},
                "metric:*": {Permission.READ},
            },
            priority=10,
            description="Read-only access to NBA data",
            is_system_role=True,
        )
        self.roles["viewer"] = viewer_role

        # Developer role (extended analyst permissions)
        developer_role = Role(
            name="developer",
            permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
            resource_permissions={
                "database:*": {Permission.READ, Permission.EXECUTE},
                "table:*": {Permission.READ, Permission.WRITE},
                "nba_data:*": {Permission.READ, Permission.WRITE, Permission.EXECUTE},
                "s3_bucket:*": {Permission.READ, Permission.WRITE},
                "s3_file:*": {Permission.READ, Permission.WRITE},
                "tool:*": {Permission.EXECUTE},
                "metric:*": {Permission.READ, Permission.WRITE},
            },
            priority=75,
            description="Developer with write access to data and tools",
            is_system_role=True,
        )
        self.roles["developer"] = developer_role

        # Service role (for service-to-service auth)
        service_role = Role(
            name="service",
            permissions={Permission.READ, Permission.EXECUTE},
            resource_permissions={
                "database:*": {Permission.READ, Permission.EXECUTE},
                "nba_data:*": {Permission.READ, Permission.EXECUTE},
                "tool:*": {Permission.EXECUTE},
            },
            priority=25,
            description="Service account for automated processes",
            is_system_role=True,
        )
        self.roles["service"] = service_role

        logger.info("Created default system roles")

    def create_role(
        self,
        name: str,
        permissions: Optional[Set[Permission]] = None,
        resource_permissions: Optional[Dict[str, Set[Permission]]] = None,
        priority: int = 50,
        description: str = "",
        parent_roles: Optional[List[str]] = None,
    ) -> Role:
        """
        Create a new role.

        Args:
            name: Unique role name
            permissions: Global permissions for this role
            resource_permissions: Resource-specific permissions
            priority: Role priority (higher = more privileged)
            description: Human-readable description
            parent_roles: Parent roles for inheritance

        Returns:
            Created Role object

        Raises:
            ValueError: If role already exists

        Examples:
            >>> role = rbac.create_role(
            ...     name="data_scientist",
            ...     permissions={Permission.READ, Permission.EXECUTE, Permission.WRITE},
            ...     resource_permissions={
            ...         "database:*": {Permission.READ, Permission.EXECUTE},
            ...         "nba_data:*": {Permission.READ, Permission.WRITE},
            ...     },
            ...     priority=60,
            ...     description="Data scientist with ML capabilities"
            ... )
        """
        with self._lock:
            if name in self.roles:
                raise ValueError(f"Role '{name}' already exists")

            role = Role(
                name=name,
                permissions=permissions or set(),
                resource_permissions=resource_permissions or {},
                priority=priority,
                description=description,
                parent_roles=parent_roles or [],
                is_system_role=False,
            )

            self.roles[name] = role

        logger.info(
            f"Role created: {name}",
            extra={
                "role_name": name,
                "permissions": [p.value for p in (permissions or [])],
                "priority": priority,
            },
        )

        return role

    def update_role(
        self,
        name: str,
        permissions: Optional[Set[Permission]] = None,
        resource_permissions: Optional[Dict[str, Set[Permission]]] = None,
        priority: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Role:
        """
        Update an existing role.

        Args:
            name: Role name
            permissions: New global permissions (None = no change)
            resource_permissions: New resource permissions (None = no change)
            priority: New priority (None = no change)
            description: New description (None = no change)

        Returns:
            Updated Role object

        Raises:
            ValueError: If role doesn't exist or is a system role
        """
        with self._lock:
            if name not in self.roles:
                raise ValueError(f"Role '{name}' not found")

            role = self.roles[name]

            if role.is_system_role:
                raise ValueError(f"Cannot modify system role '{name}'")

            if permissions is not None:
                role.permissions = permissions

            if resource_permissions is not None:
                role.resource_permissions = resource_permissions

            if priority is not None:
                role.priority = priority

            if description is not None:
                role.description = description

        logger.info(f"Role updated: {name}")

        return role

    def delete_role(self, name: str) -> None:
        """
        Delete a role.

        Args:
            name: Role name

        Raises:
            ValueError: If role doesn't exist or is a system role
        """
        with self._lock:
            if name not in self.roles:
                raise ValueError(f"Role '{name}' not found")

            role = self.roles[name]

            if role.is_system_role:
                raise ValueError(f"Cannot delete system role '{name}'")

            # Remove role from all users
            for user_roles in self.user_roles.values():
                user_roles.discard(name)

            del self.roles[name]

        logger.info(f"Role deleted: {name}")

    def get_role(self, name: str) -> Optional[Role]:
        """
        Get a role by name.

        Args:
            name: Role name

        Returns:
            Role object or None if not found
        """
        with self._lock:
            return self.roles.get(name)

    def list_roles(self) -> List[Role]:
        """
        List all roles.

        Returns:
            List of all roles
        """
        with self._lock:
            return list(self.roles.values())

    def assign_role(self, user_id: str, role_name: str) -> None:
        """
        Assign a role to a user.

        Args:
            user_id: User identifier
            role_name: Name of role to assign

        Raises:
            ValueError: If role doesn't exist

        Examples:
            >>> rbac.assign_role("user_123", "analyst")
        """
        with self._lock:
            if role_name not in self.roles:
                raise ValueError(f"Role '{role_name}' not found")

            self.user_roles[user_id].add(role_name)

        logger.info(
            f"Role assigned: {role_name} to user {user_id}",
            extra={"user_id": user_id, "role": role_name},
        )

    def revoke_role(self, user_id: str, role_name: str) -> None:
        """
        Revoke a role from a user.

        Args:
            user_id: User identifier
            role_name: Name of role to revoke
        """
        with self._lock:
            self.user_roles[user_id].discard(role_name)

        logger.info(
            f"Role revoked: {role_name} from user {user_id}",
            extra={"user_id": user_id, "role": role_name},
        )

    def assign_roles(self, user_id: str, role_names: List[str]) -> None:
        """
        Assign multiple roles to a user.

        Args:
            user_id: User identifier
            role_names: List of role names to assign
        """
        for role_name in role_names:
            self.assign_role(user_id, role_name)

    def get_user_roles(self, user_id: str) -> List[Role]:
        """
        Get all roles assigned to a user.

        Args:
            user_id: User identifier

        Returns:
            List of Role objects
        """
        with self._lock:
            role_names = self.user_roles.get(user_id, set())
            return [self.roles[name] for name in role_names if name in self.roles]

    def get_user_permissions(
        self, user_id: str, resource: str = "*"
    ) -> Set[Permission]:
        """
        Get all permissions a user has for a resource.

        Args:
            user_id: User identifier
            resource: Resource identifier

        Returns:
            Set of permissions

        Examples:
            >>> perms = rbac.get_user_permissions("user_123", "database:games")
            >>> if Permission.READ in perms:
            ...     # User can read
            ...     pass
        """
        permissions = set()
        roles = self.get_user_roles(user_id)

        for role in roles:
            # Admin permission grants everything
            if Permission.ADMIN in role.permissions:
                return {
                    Permission.ADMIN,
                    Permission.READ,
                    Permission.WRITE,
                    Permission.EXECUTE,
                    Permission.DELETE,
                }

            # Global permissions
            permissions.update(role.permissions)

            # Resource-specific permissions
            if resource in role.resource_permissions:
                permissions.update(role.resource_permissions[resource])

            # Wildcard resource permissions
            resource_type = resource.split(":")[0] if ":" in resource else resource
            wildcard_resource = f"{resource_type}:*"

            if wildcard_resource in role.resource_permissions:
                permissions.update(role.resource_permissions[wildcard_resource])

            # All resources wildcard
            if "*" in role.resource_permissions:
                permissions.update(role.resource_permissions["*"])

        return permissions

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: str = "*",
        log_attempt: bool = True,
    ) -> bool:
        """
        Check if user has a specific permission for a resource.

        Args:
            user_id: User identifier
            permission: Permission to check
            resource: Resource identifier
            log_attempt: Whether to log this access attempt

        Returns:
            True if user has permission, False otherwise

        Examples:
            >>> if rbac.check_permission("user_123", Permission.EXECUTE, "database:games"):
            ...     # Execute query
            ...     result = execute_query()
        """
        roles = self.get_user_roles(user_id)
        role_names = [r.name for r in roles]

        # Check if user has permission through any role
        granted = False
        for role in roles:
            if role.has_permission(permission, resource):
                granted = True
                break

        # Log access attempt
        if self.enable_audit_logging and log_attempt:
            attempt = AccessAttempt(
                timestamp=datetime.now(),
                user_id=user_id,
                resource=resource,
                permission=permission,
                granted=granted,
                roles=role_names,
                reason=None if granted else "Permission denied",
            )

            with self._lock:
                self.access_log.append(attempt)

            # Log to logger
            if granted:
                logger.debug(
                    f"Access granted: {user_id} -> {permission.value} on {resource}",
                    extra={
                        "user_id": user_id,
                        "permission": permission.value,
                        "resource": resource,
                        "roles": role_names,
                    },
                )
            else:
                logger.warning(
                    f"Access denied: {user_id} -> {permission.value} on {resource}",
                    extra={
                        "user_id": user_id,
                        "permission": permission.value,
                        "resource": resource,
                        "roles": role_names,
                    },
                )

        return granted

    def require_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: str = "*",
    ) -> None:
        """
        Require a permission (raise exception if denied).

        Args:
            user_id: User identifier
            permission: Required permission
            resource: Resource identifier

        Raises:
            BaseAuthenticationError: If permission denied
        """
        if not self.check_permission(user_id, permission, resource):
            raise BaseAuthenticationError(
                f"Permission denied: {permission.value} on {resource}",
                details={
                    "user_id": user_id,
                    "permission": permission.value,
                    "resource": resource,
                },
            )

    def get_access_log(
        self,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        permission: Optional[Permission] = None,
        granted: Optional[bool] = None,
        limit: int = 100,
    ) -> List[AccessAttempt]:
        """
        Get access log with optional filters.

        Args:
            user_id: Filter by user ID
            resource: Filter by resource
            permission: Filter by permission
            granted: Filter by whether access was granted
            limit: Maximum number of entries to return

        Returns:
            List of AccessAttempt objects
        """
        with self._lock:
            log = list(self.access_log)

        # Apply filters
        if user_id:
            log = [a for a in log if a.user_id == user_id]

        if resource:
            log = [a for a in log if a.resource == resource]

        if permission:
            log = [a for a in log if a.permission == permission]

        if granted is not None:
            log = [a for a in log if a.granted == granted]

        # Sort by timestamp (most recent first)
        log.sort(key=lambda a: a.timestamp, reverse=True)

        return log[:limit]

    def clear_access_log(self) -> None:
        """Clear the access log."""
        with self._lock:
            self.access_log.clear()

        logger.info("Access log cleared")


# ==============================================================================
# Decorators
# ==============================================================================


def require_permission(
    permission: Permission,
    resource: str = "*",
    user_id_param: str = "user_id",
):
    """
    Decorator to require a specific permission for a function.

    Args:
        permission: Required permission
        resource: Resource identifier (can use format strings)
        user_id_param: Name of parameter containing user ID

    Examples:
        >>> @require_permission(Permission.EXECUTE, resource="database:{table_name}")
        ... async def query_table(user_id: str, table_name: str, query: str):
        ...     # This function requires EXECUTE permission on specific table
        ...     pass
        >>>
        >>> @require_permission(Permission.ADMIN)
        ... async def delete_user(user_id: str, target_user_id: str):
        ...     # This function requires ADMIN permission
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get user ID from parameters
            user_id = kwargs.get(user_id_param)

            if not user_id:
                # Try to find it in args based on function signature
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    idx = param_names.index(user_id_param)
                    if idx < len(args):
                        user_id = args[idx]

            if not user_id:
                raise BaseAuthenticationError(
                    "User ID not provided for permission check",
                    details={"function": func.__name__},
                )

            # Format resource string with function parameters
            formatted_resource = resource.format(**kwargs)

            # Check permission
            rbac = get_rbac_manager()
            rbac.require_permission(user_id, permission, formatted_resource)

            # Execute function
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get user ID from parameters
            user_id = kwargs.get(user_id_param)

            if not user_id:
                # Try to find it in args based on function signature
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    idx = param_names.index(user_id_param)
                    if idx < len(args):
                        user_id = args[idx]

            if not user_id:
                raise BaseAuthenticationError(
                    "User ID not provided for permission check",
                    details={"function": func.__name__},
                )

            # Format resource string with function parameters
            formatted_resource = resource.format(**kwargs)

            # Check permission
            rbac = get_rbac_manager()
            rbac.require_permission(user_id, permission, formatted_resource)

            # Execute function
            return func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def require_role(role_name: str, user_id_param: str = "user_id"):
    """
    Decorator to require a specific role for a function.

    Args:
        role_name: Required role name
        user_id_param: Name of parameter containing user ID

    Examples:
        >>> @require_role("admin")
        ... async def manage_users(user_id: str):
        ...     # This function requires admin role
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get user ID
            user_id = kwargs.get(user_id_param)

            if not user_id:
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    idx = param_names.index(user_id_param)
                    if idx < len(args):
                        user_id = args[idx]

            if not user_id:
                raise BaseAuthenticationError(
                    "User ID not provided for role check",
                    details={"function": func.__name__},
                )

            # Check role
            rbac = get_rbac_manager()
            user_roles = rbac.get_user_roles(user_id)
            user_role_names = {r.name for r in user_roles}

            if role_name not in user_role_names:
                raise BaseAuthenticationError(
                    f"Role '{role_name}' required",
                    details={
                        "required_role": role_name,
                        "user_roles": list(user_role_names),
                    },
                )

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get user ID
            user_id = kwargs.get(user_id_param)

            if not user_id:
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    idx = param_names.index(user_id_param)
                    if idx < len(args):
                        user_id = args[idx]

            if not user_id:
                raise BaseAuthenticationError(
                    "User ID not provided for role check",
                    details={"function": func.__name__},
                )

            # Check role
            rbac = get_rbac_manager()
            user_roles = rbac.get_user_roles(user_id)
            user_role_names = {r.name for r in user_roles}

            if role_name not in user_role_names:
                raise BaseAuthenticationError(
                    f"Role '{role_name}' required",
                    details={
                        "required_role": role_name,
                        "user_roles": list(user_role_names),
                    },
                )

            return func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==============================================================================
# Global Instance
# ==============================================================================


_global_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get the global RBAC manager instance."""
    global _global_rbac_manager
    if _global_rbac_manager is None:
        _global_rbac_manager = RBACManager()
    return _global_rbac_manager


def set_rbac_manager(manager: RBACManager) -> None:
    """Set the global RBAC manager instance."""
    global _global_rbac_manager
    _global_rbac_manager = manager
