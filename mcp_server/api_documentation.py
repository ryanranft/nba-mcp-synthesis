"""
API Documentation Generator Module
Automatically generate OpenAPI/Swagger documentation.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIDocumentationGenerator:
    """Generate API documentation automatically"""

    def __init__(
        self,
        title: str = "NBA MCP API",
        version: str = "1.0.0",
        description: str = "NBA Machine Learning & Analytics API",
    ):
        """
        Initialize API documentation generator.

        Args:
            title: API title
            version: API version
            description: API description
        """
        self.title = title
        self.version = version
        self.description = description
        self.endpoints: List[Dict] = []
        self.schemas: Dict[str, Dict] = {}

    def add_endpoint(
        self,
        path: str,
        method: str,
        summary: str,
        description: Optional[str] = None,
        parameters: Optional[List[Dict]] = None,
        request_body: Optional[Dict] = None,
        responses: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Add an API endpoint.

        Args:
            path: Endpoint path (e.g., "/api/predictions")
            method: HTTP method (GET, POST, etc.)
            summary: Short summary
            description: Detailed description
            parameters: Query/path parameters
            request_body: Request body schema
            responses: Response schemas
            tags: Category tags
        """
        endpoint = {
            "path": path,
            "method": method.upper(),
            "summary": summary,
            "description": description or summary,
            "parameters": parameters or [],
            "request_body": request_body,
            "responses": responses
            or {
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"},
                "500": {"description": "Internal Server Error"},
            },
            "tags": tags or ["General"],
        }

        self.endpoints.append(endpoint)
        logger.info(f"Added endpoint: {method.upper()} {path}")

    def add_schema(
        self,
        name: str,
        properties: Dict[str, Dict],
        required: Optional[List[str]] = None,
        description: Optional[str] = None,
    ):
        """
        Add a data schema.

        Args:
            name: Schema name
            properties: Schema properties
            required: Required fields
            description: Schema description
        """
        self.schemas[name] = {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "description": description,
        }

        logger.info(f"Added schema: {name}")

    def generate_openapi_spec(self) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 specification.

        Returns:
            OpenAPI spec dictionary
        """
        paths = {}

        for endpoint in self.endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                "summary": endpoint["summary"],
                "description": endpoint["description"],
                "tags": endpoint["tags"],
                "parameters": endpoint["parameters"],
                "responses": endpoint["responses"],
            }

            if endpoint["request_body"]:
                paths[path][method]["requestBody"] = endpoint["request_body"]

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": paths,
            "components": {"schemas": self.schemas},
        }

        return spec

    def generate_markdown_docs(self) -> str:
        """
        Generate Markdown documentation.

        Returns:
            Markdown string
        """
        md = f"# {self.title}\n\n"
        md += f"**Version:** {self.version}\n\n"
        md += f"{self.description}\n\n"
        md += "---\n\n"

        # Group by tags
        by_tags = {}
        for endpoint in self.endpoints:
            for tag in endpoint["tags"]:
                if tag not in by_tags:
                    by_tags[tag] = []
                by_tags[tag].append(endpoint)

        # Document each tag
        for tag, endpoints in sorted(by_tags.items()):
            md += f"## {tag}\n\n"

            for endpoint in endpoints:
                md += f"### `{endpoint['method']} {endpoint['path']}`\n\n"
                md += f"{endpoint['description']}\n\n"

                if endpoint["parameters"]:
                    md += "**Parameters:**\n\n"
                    for param in endpoint["parameters"]:
                        required = " (required)" if param.get("required") else ""
                        md += f"- `{param['name']}`{required}: {param.get('description', 'No description')}\n"
                    md += "\n"

                if endpoint["request_body"]:
                    md += "**Request Body:**\n\n"
                    md += "```json\n"
                    md += json.dumps(endpoint["request_body"], indent=2)
                    md += "\n```\n\n"

                md += "**Responses:**\n\n"
                for code, response in endpoint["responses"].items():
                    md += f"- `{code}`: {response['description']}\n"
                md += "\n"
                md += "---\n\n"

        # Schemas
        if self.schemas:
            md += "## Data Schemas\n\n"
            for name, schema in self.schemas.items():
                md += f"### {name}\n\n"
                if schema.get("description"):
                    md += f"{schema['description']}\n\n"
                md += "**Properties:**\n\n"
                for prop_name, prop_def in schema["properties"].items():
                    required = (
                        " (required)" if prop_name in schema.get("required", []) else ""
                    )
                    md += f"- `{prop_name}`{required}: {prop_def.get('type', 'unknown')} - {prop_def.get('description', '')}\n"
                md += "\n"

        return md

    def save_documentation(self, format: str = "both", output_dir: str = "./api_docs"):
        """
        Save documentation to files.

        Args:
            format: "openapi", "markdown", or "both"
            output_dir: Output directory
        """
        from pathlib import Path

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if format in ["openapi", "both"]:
            spec = self.generate_openapi_spec()
            spec_file = Path(output_dir) / "openapi.json"
            with open(spec_file, "w") as f:
                json.dump(spec, f, indent=2)
            logger.info(f"Saved OpenAPI spec to {spec_file}")

        if format in ["markdown", "both"]:
            md = self.generate_markdown_docs()
            md_file = Path(output_dir) / "API.md"
            with open(md_file, "w") as f:
                f.write(md)
            logger.info(f"Saved Markdown docs to {md_file}")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("API DOCUMENTATION GENERATOR DEMO")
    print("=" * 80)

    doc_gen = APIDocumentationGenerator(
        title="NBA MCP API",
        version="1.0.0",
        description="Machine Learning and Analytics API for NBA data",
    )

    # Add schemas
    print("\n" + "=" * 80)
    print("ADDING DATA SCHEMAS")
    print("=" * 80)

    doc_gen.add_schema(
        name="PredictionRequest",
        properties={
            "player_id": {"type": "string", "description": "Player identifier"},
            "season": {"type": "integer", "description": "Season year"},
            "features": {"type": "array", "description": "Feature values"},
        },
        required=["player_id", "season"],
        description="Request for player performance prediction",
    )

    doc_gen.add_schema(
        name="PredictionResponse",
        properties={
            "prediction_id": {"type": "string", "description": "Prediction identifier"},
            "prediction": {"type": "number", "description": "Predicted value"},
            "confidence": {"type": "number", "description": "Confidence score (0-1)"},
            "model_version": {"type": "string", "description": "Model version used"},
        },
        description="Prediction response",
    )

    print("✅ Added 2 schemas")

    # Add endpoints
    print("\n" + "=" * 80)
    print("ADDING API ENDPOINTS")
    print("=" * 80)

    doc_gen.add_endpoint(
        path="/api/predictions",
        method="POST",
        summary="Create prediction",
        description="Generate a prediction for player performance",
        request_body={
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PredictionRequest"}
                }
            }
        },
        responses={
            "200": {
                "description": "Prediction successful",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/PredictionResponse"}
                    }
                },
            },
            "400": {"description": "Invalid request"},
            "500": {"description": "Server error"},
        },
        tags=["Predictions"],
    )

    doc_gen.add_endpoint(
        path="/api/models",
        method="GET",
        summary="List models",
        description="Get list of available models",
        parameters=[
            {
                "name": "stage",
                "in": "query",
                "description": "Filter by stage (development, staging, production)",
                "required": False,
                "schema": {"type": "string"},
            }
        ],
        tags=["Models"],
    )

    doc_gen.add_endpoint(
        path="/api/health",
        method="GET",
        summary="Health check",
        description="Check API health status",
        responses={
            "200": {"description": "Healthy"},
            "503": {"description": "Unhealthy"},
        },
        tags=["System"],
    )

    print("✅ Added 3 endpoints")

    # Generate OpenAPI spec
    print("\n" + "=" * 80)
    print("GENERATING OPENAPI SPECIFICATION")
    print("=" * 80)

    spec = doc_gen.generate_openapi_spec()
    print(f"\nOpenAPI Version: {spec['openapi']}")
    print(f"Endpoints: {len(spec['paths'])}")
    print(f"Schemas: {len(spec['components']['schemas'])}")

    # Generate Markdown
    print("\n" + "=" * 80)
    print("GENERATING MARKDOWN DOCUMENTATION")
    print("=" * 80)

    md = doc_gen.generate_markdown_docs()
    print(f"\nMarkdown length: {len(md)} characters")
    print("\nPreview:")
    print(md[:500] + "...")

    # Save documentation
    print("\n" + "=" * 80)
    print("SAVING DOCUMENTATION")
    print("=" * 80)

    doc_gen.save_documentation(format="both", output_dir="./demo_api_docs")
    print("\n✅ Documentation saved to ./demo_api_docs/")

    print("\n" + "=" * 80)
    print("API Documentation Demo Complete!")
    print("=" * 80)
