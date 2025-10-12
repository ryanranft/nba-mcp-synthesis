"""API Documentation (OpenAPI/Swagger) - IMPORTANT 10"""
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict]
    responses: Dict[int, Dict]
    tags: List[str]


class OpenAPIGenerator:
    """Generate OpenAPI 3.0 specification"""

    def __init__(self, title: str, version: str, description: str):
        self.title = title
        self.version = version
        self.description = description
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, Dict] = {}

    def add_endpoint(self, endpoint: APIEndpoint):
        """Add an endpoint to documentation"""
        self.endpoints.append(endpoint)

    def add_schema(self, name: str, schema: Dict):
        """Add a schema definition"""
        self.schemas[name] = schema

    def generate(self) -> Dict[str, Any]:
        """Generate OpenAPI spec"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Local development"},
                {"url": "https://api.nba-mcp.com", "description": "Production"}
            ],
            "paths": self._generate_paths(),
            "components": {
                "schemas": self.schemas,
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    },
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            },
            "security": [
                {"BearerAuth": []},
                {"ApiKeyAuth": []}
            ]
        }
        return spec

    def _generate_paths(self) -> Dict:
        """Generate paths section"""
        paths = {}
        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            paths[endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "parameters": endpoint.parameters,
                "responses": endpoint.responses
            }

        return paths


# NBA MCP API Documentation
nba_api = OpenAPIGenerator(
    title="NBA MCP API",
    version="1.0.0",
    description="NBA Machine Learning Context Protocol API"
)

# Add schemas
nba_api.add_schema("Player", {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "team": {"type": "string"},
        "position": {"type": "string"}
    }
})

nba_api.add_schema("Game", {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "home_team": {"type": "string"},
        "away_team": {"type": "string"},
        "date": {"type": "string", "format": "date"}
    }
})

# Add endpoints
nba_api.add_endpoint(APIEndpoint(
    path="/api/players",
    method="GET",
    summary="List players",
    description="Get a list of NBA players with optional filters",
    parameters=[
        {
            "name": "team",
            "in": "query",
            "schema": {"type": "string"},
            "description": "Filter by team name"
        },
        {
            "name": "season",
            "in": "query",
            "schema": {"type": "integer"},
            "description": "Filter by season"
        }
    ],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Player"}
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"}
    },
    tags=["Players"]
))

nba_api.add_endpoint(APIEndpoint(
    path="/api/games",
    method="GET",
    summary="List games",
    description="Get a list of NBA games",
    parameters=[
        {
            "name": "season",
            "in": "query",
            "schema": {"type": "integer"},
            "required": True,
            "description": "Season year"
        }
    ],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Game"}
                    }
                }
            }
        }
    },
    tags=["Games"]
))

# Generate and save spec
def save_openapi_spec(filename: str = "openapi.json"):
    """Save OpenAPI spec to file"""
    import json
    spec = nba_api.generate()
    with open(filename, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"✅ OpenAPI spec saved to {filename}")


if __name__ == "__main__":
    save_openapi_spec()

