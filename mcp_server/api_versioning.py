"""
API Versioning System

Manage multiple API versions concurrently:
- URL-based versioning
- Header-based versioning
- Backward compatibility
- Deprecation warnings
- Version negotiation
- Migration guides

Features:
- Multiple version support
- Automatic routing
- Version-specific schemas
- Deprecation notices
- Breaking change management
- Documentation per version

Use Cases:
- Rolling API updates
- Gradual migration
- Backward compatibility
- Client-specific versions
- Beta features
"""

import logging
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """API version status"""
    DEVELOPMENT = "development"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


@dataclass
class APIVersion:
    """API version definition"""
    version: str  # e.g., "1.0", "2.1", "3.0-beta"
    status: VersionStatus
    release_date: datetime
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    changelog: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    migration_guide_url: Optional[str] = None

    def is_active(self) -> bool:
        """Check if version is active"""
        if self.status == VersionStatus.SUNSET:
            return False
        if self.sunset_date and datetime.now() >= self.sunset_date:
            return False
        return True

    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        if self.status == VersionStatus.DEPRECATED:
            return True
        if self.deprecation_date and datetime.now() >= self.deprecation_date:
            return True
        return False

    def days_until_sunset(self) -> Optional[int]:
        """Get days until sunset"""
        if not self.sunset_date:
            return None
        delta = self.sunset_date - datetime.now()
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version,
            'status': self.status.value,
            'release_date': self.release_date.isoformat(),
            'deprecation_date': self.deprecation_date.isoformat() if self.deprecation_date else None,
            'sunset_date': self.sunset_date.isoformat() if self.sunset_date else None,
            'days_until_sunset': self.days_until_sunset(),
            'is_active': self.is_active(),
            'is_deprecated': self.is_deprecated(),
            'changelog': self.changelog,
            'breaking_changes': self.breaking_changes,
            'migration_guide_url': self.migration_guide_url
        }


class VersionRouter:
    """Route requests to appropriate API version"""

    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.handlers: Dict[str, Dict[str, Callable]] = {}  # {version: {endpoint: handler}}
        self.default_version: Optional[str] = None

    def register_version(self, version: APIVersion) -> None:
        """Register an API version"""
        self.versions[version.version] = version
        self.handlers[version.version] = {}

        # Set as default if it's the first stable version
        if version.status == VersionStatus.STABLE and not self.default_version:
            self.default_version = version.version

        logger.info(f"Registered API version: {version.version} ({version.status.value})")

    def register_endpoint(
        self,
        version: str,
        endpoint: str,
        handler: Callable
    ) -> None:
        """Register endpoint handler for specific version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")

        self.handlers[version][endpoint] = handler
        logger.debug(f"Registered endpoint {endpoint} for version {version}")

    def get_version(self, version_string: str) -> Optional[APIVersion]:
        """Get API version by string"""
        return self.versions.get(version_string)

    def get_latest_stable_version(self) -> Optional[str]:
        """Get latest stable version"""
        stable_versions = [
            v for v in self.versions.values()
            if v.status == VersionStatus.STABLE and v.is_active()
        ]

        if not stable_versions:
            return None

        # Sort by release date, get latest
        latest = max(stable_versions, key=lambda v: v.release_date)
        return latest.version

    def route(
        self,
        endpoint: str,
        version: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Route request to appropriate version handler"""
        # Determine version
        if not version:
            version = self.default_version or self.get_latest_stable_version()

        if not version:
            raise ValueError("No API version specified and no default available")

        # Check version exists and is active
        api_version = self.get_version(version)
        if not api_version:
            raise ValueError(f"Unknown API version: {version}")

        if not api_version.is_active():
            raise ValueError(f"API version {version} is no longer active")

        # Get handler
        version_handlers = self.handlers.get(version, {})
        handler = version_handlers.get(endpoint)

        if not handler:
            raise ValueError(f"Endpoint {endpoint} not found in version {version}")

        # Execute handler
        logger.debug(f"Routing {endpoint} to version {version}")
        return handler(**kwargs)

    def list_versions(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List all API versions"""
        versions = [
            v for v in self.versions.values()
            if include_inactive or v.is_active()
        ]
        return [v.to_dict() for v in versions]


def version(version_string: str):
    """Decorator to mark endpoint with version"""
    def decorator(func: Callable):
        func._api_version = version_string
        return func
    return decorator


def deprecated(sunset_date: Optional[datetime] = None, message: Optional[str] = None):
    """Decorator to mark endpoint as deprecated"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log deprecation warning
            warning = f"Endpoint {func.__name__} is deprecated"
            if sunset_date:
                days_left = (sunset_date - datetime.now()).days
                warning += f" and will be removed in {days_left} days"
            if message:
                warning += f": {message}"

            logger.warning(warning)

            # Add deprecation header to response (if response object exists)
            result = func(*args, **kwargs)
            if hasattr(result, 'headers'):
                result.headers['X-API-Deprecated'] = 'true'
                if sunset_date:
                    result.headers['X-API-Sunset-Date'] = sunset_date.isoformat()

            return result
        return wrapper
    return decorator


class VersionNegotiator:
    """Negotiate API version with client"""

    def __init__(self, router: VersionRouter):
        self.router = router

    def negotiate_from_url(self, url: str) -> Optional[str]:
        """Extract version from URL path (e.g., /api/v2/players)"""
        parts = url.split('/')
        for part in parts:
            if part.startswith('v') and part[1:].replace('.', '').isdigit():
                version = part[1:]  # Remove 'v' prefix
                if self.router.get_version(version):
                    return version
        return None

    def negotiate_from_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract version from headers (e.g., Accept: application/vnd.nba.v2+json)"""
        accept_header = headers.get('Accept', '')

        # Look for version in accept header
        if 'vnd.nba.' in accept_header:
            parts = accept_header.split('vnd.nba.')
            if len(parts) > 1:
                version_part = parts[1].split('+')[0]  # e.g., "v2"
                if version_part.startswith('v'):
                    version = version_part[1:]
                    if self.router.get_version(version):
                        return version

        # Check X-API-Version header
        version_header = headers.get('X-API-Version')
        if version_header and self.router.get_version(version_header):
            return version_header

        return None

    def negotiate(
        self,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        default: Optional[str] = None
    ) -> str:
        """Negotiate version from multiple sources"""
        # Try URL first
        if url:
            version = self.negotiate_from_url(url)
            if version:
                return version

        # Try headers
        if headers:
            version = self.negotiate_from_header(headers)
            if version:
                return version

        # Use default or latest stable
        if default:
            return default

        return self.router.get_latest_stable_version() or self.router.default_version or '1.0'


# NBA MCP API Versions
def create_nba_api_versions() -> VersionRouter:
    """Create NBA MCP API version definitions"""
    router = VersionRouter()

    # Version 1.0 - Initial release
    v1 = APIVersion(
        version="1.0",
        status=VersionStatus.DEPRECATED,
        release_date=datetime(2024, 1, 1),
        deprecation_date=datetime(2025, 6, 1),
        sunset_date=datetime(2025, 12, 31),
        changelog=[
            "Initial release",
            "Basic player and game endpoints",
            "Simple statistics calculations"
        ],
        breaking_changes=[],
        migration_guide_url="https://docs.nba-mcp.com/migration/v1-to-v2"
    )
    router.register_version(v1)

    # Version 2.0 - ML features
    v2 = APIVersion(
        version="2.0",
        status=VersionStatus.STABLE,
        release_date=datetime(2025, 1, 1),
        deprecation_date=None,
        sunset_date=None,
        changelog=[
            "Added ML-powered predictions",
            "Advanced analytics endpoints",
            "Real-time stats streaming",
            "Improved error handling"
        ],
        breaking_changes=[
            "Changed response format for /players endpoint",
            "Removed deprecated /stats/simple endpoint",
            "Updated authentication mechanism"
        ],
        migration_guide_url="https://docs.nba-mcp.com/migration/v1-to-v2"
    )
    router.register_version(v2)

    # Version 3.0 - Beta features
    v3 = APIVersion(
        version="3.0",
        status=VersionStatus.BETA,
        release_date=datetime(2025, 10, 1),
        deprecation_date=None,
        sunset_date=None,
        changelog=[
            "GraphQL support",
            "WebSocket for real-time updates",
            "Advanced ML models (PER, BPM)",
            "Multi-tenant support"
        ],
        breaking_changes=[
            "New authentication flow",
            "Pagination changes",
            "Rate limiting updates"
        ],
        migration_guide_url="https://docs.nba-mcp.com/migration/v2-to-v3"
    )
    router.register_version(v3)

    return router


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== API Versioning Demo ===\n")

    # Create router with NBA versions
    router = create_nba_api_versions()

    # Register v1 endpoints
    @version("1.0")
    def get_player_v1(player_id: int):
        return {
            'player_id': player_id,
            'name': 'LeBron James',
            'ppg': 25.0  # Simple format
        }

    router.register_endpoint("1.0", "get_player", get_player_v1)

    # Register v2 endpoints
    @version("2.0")
    def get_player_v2(player_id: int):
        return {
            'player_id': player_id,
            'personal': {
                'name': 'LeBron James',
                'team': 'Lakers'
            },
            'stats': {
                'ppg': 25.0,
                'rpg': 8.0,
                'apg': 7.0
            },
            'predictions': {
                'next_game_performance': 'excellent'
            }
        }

    router.register_endpoint("2.0", "get_player", get_player_v2)

    # Test routing
    print("--- Version Routing ---")
    print("\nVersion 1.0 response:")
    result_v1 = router.route("get_player", version="1.0", player_id=23)
    print(result_v1)

    print("\nVersion 2.0 response:")
    result_v2 = router.route("get_player", version="2.0", player_id=23)
    print(result_v2)

    # List versions
    print("\n--- Available Versions ---")
    for version_info in router.list_versions(include_inactive=False):
        print(f"\nVersion {version_info['version']}:")
        print(f"  Status: {version_info['status']}")
        print(f"  Deprecated: {version_info['is_deprecated']}")
        if version_info['days_until_sunset']:
            print(f"  Days until sunset: {version_info['days_until_sunset']}")
        print(f"  Changelog: {', '.join(version_info['changelog'][:2])}")

    # Version negotiation
    print("\n--- Version Negotiation ---")
    negotiator = VersionNegotiator(router)

    # From URL
    url = "/api/v2/players/23"
    negotiated_version = negotiator.negotiate(url=url)
    print(f"Version from URL '{url}': {negotiated_version}")

    # From headers
    headers = {'Accept': 'application/vnd.nba.v2+json'}
    negotiated_version = negotiator.negotiate(headers=headers)
    print(f"Version from headers: {negotiated_version}")

    # Default
    negotiated_version = negotiator.negotiate()
    print(f"Default version: {negotiated_version}")

    # Deprecation warning
    print("\n--- Deprecation Warning ---")

    @deprecated(
        sunset_date=datetime(2025, 12, 31),
        message="Use /v2/players/{id} instead"
    )
    def old_endpoint():
        return {"data": "old format"}

    result = old_endpoint()
    print(f"Old endpoint result: {result}")

    print("\n=== Demo Complete ===")

