"""
Automated Documentation Generator

Generate comprehensive documentation automatically:
- Code documentation
- API specs
- Architecture diagrams
- User guides
- Change logs
- Metrics reports

Features:
- Markdown generation
- Diagram creation
- Code analysis
- Auto-updating
- Multi-format export
- Version tracking

Use Cases:
- API documentation
- System architecture docs
- User manuals
- Onboarding guides
- Release notes
"""

import ast
import inspect
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class FunctionDoc:
    """Function documentation"""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict[str, str]]
    returns: Optional[str]
    examples: List[str]


@dataclass
class ClassDoc:
    """Class documentation"""
    name: str
    docstring: Optional[str]
    methods: List[FunctionDoc]
    attributes: List[Dict[str, str]]


@dataclass
class ModuleDoc:
    """Module documentation"""
    name: str
    filepath: str
    docstring: Optional[str]
    classes: List[ClassDoc]
    functions: List[FunctionDoc]
    imports: List[str]


class CodeAnalyzer:
    """Analyze Python code for documentation"""

    def analyze_file(self, filepath: str) -> ModuleDoc:
        """Analyze a Python file"""
        with open(filepath, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        module_doc = ModuleDoc(
            name=Path(filepath).stem,
            filepath=filepath,
            docstring=ast.get_docstring(tree),
            classes=[],
            functions=[],
            imports=[]
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_doc.imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_doc.imports.append(node.module)

            elif isinstance(node, ast.ClassDef):
                class_doc = self._analyze_class(node)
                module_doc.classes.append(class_doc)

            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions
                if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    func_doc = self._analyze_function(node)
                    module_doc.functions.append(func_doc)

        return module_doc

    def _analyze_class(self, node: ast.ClassDef) -> ClassDoc:
        """Analyze a class"""
        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                func_doc = self._analyze_function(item)
                methods.append(func_doc)

            elif isinstance(item, ast.AnnAssign):
                # Class attributes
                if isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    attr_type = ast.unparse(item.annotation) if item.annotation else "Any"
                    attributes.append({'name': attr_name, 'type': attr_type})

        return ClassDoc(
            name=node.name,
            docstring=ast.get_docstring(node),
            methods=methods,
            attributes=attributes
        )

    def _analyze_function(self, node: ast.FunctionDef) -> FunctionDoc:
        """Analyze a function"""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            param_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
            parameters.append({'name': param_name, 'type': param_type})

        # Extract return type
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns)

        # Parse docstring for examples
        docstring = ast.get_docstring(node)
        examples = []
        if docstring:
            examples = self._extract_examples(docstring)

        return FunctionDoc(
            name=node.name,
            signature=f"{node.name}({', '.join(arg.arg for arg in node.args.args)})",
            docstring=docstring,
            parameters=parameters,
            returns=returns,
            examples=examples
        )

    def _extract_examples(self, docstring: str) -> List[str]:
        """Extract code examples from docstring"""
        examples = []
        in_example = False
        current_example = []

        for line in docstring.split('\n'):
            if 'Example:' in line or 'Examples:' in line:
                in_example = True
                continue

            if in_example:
                if line.strip().startswith('>>>') or line.strip().startswith('...'):
                    current_example.append(line.strip())
                elif current_example and line.strip() == '':
                    examples.append('\n'.join(current_example))
                    current_example = []
                    in_example = False

        if current_example:
            examples.append('\n'.join(current_example))

        return examples


class MarkdownGenerator:
    """Generate Markdown documentation"""

    def generate_module_docs(self, module_doc: ModuleDoc) -> str:
        """Generate documentation for a module"""
        lines = []

        # Title
        lines.append(f"# {module_doc.name}")
        lines.append("")

        # Module docstring
        if module_doc.docstring:
            lines.append(module_doc.docstring)
            lines.append("")

        # Imports
        if module_doc.imports:
            lines.append("## Dependencies")
            lines.append("")
            for imp in sorted(set(module_doc.imports))[:10]:  # Top 10
                lines.append(f"- `{imp}`")
            lines.append("")

        # Classes
        if module_doc.classes:
            lines.append("## Classes")
            lines.append("")

            for cls in module_doc.classes:
                lines.extend(self._generate_class_docs(cls))

        # Functions
        if module_doc.functions:
            lines.append("## Functions")
            lines.append("")

            for func in module_doc.functions:
                lines.extend(self._generate_function_docs(func))

        return '\n'.join(lines)

    def _generate_class_docs(self, class_doc: ClassDoc) -> List[str]:
        """Generate documentation for a class"""
        lines = []

        lines.append(f"### `{class_doc.name}`")
        lines.append("")

        if class_doc.docstring:
            lines.append(class_doc.docstring)
            lines.append("")

        # Attributes
        if class_doc.attributes:
            lines.append("**Attributes:**")
            lines.append("")
            for attr in class_doc.attributes:
                lines.append(f"- `{attr['name']}` ({attr['type']})")
            lines.append("")

        # Methods
        if class_doc.methods:
            lines.append("**Methods:**")
            lines.append("")

            for method in class_doc.methods:
                if not method.name.startswith('_'):  # Skip private methods
                    lines.append(f"#### `{method.signature}`")
                    lines.append("")

                    if method.docstring:
                        # First line of docstring
                        first_line = method.docstring.split('\n')[0]
                        lines.append(first_line)
                        lines.append("")

        return lines

    def _generate_function_docs(self, func_doc: FunctionDoc) -> List[str]:
        """Generate documentation for a function"""
        lines = []

        lines.append(f"### `{func_doc.signature}`")
        lines.append("")

        if func_doc.docstring:
            lines.append(func_doc.docstring)
            lines.append("")

        # Parameters
        if func_doc.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            for param in func_doc.parameters:
                lines.append(f"- `{param['name']}` ({param['type']})")
            lines.append("")

        # Returns
        if func_doc.returns:
            lines.append(f"**Returns:** `{func_doc.returns}`")
            lines.append("")

        # Examples
        if func_doc.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in func_doc.examples:
                lines.append("```python")
                lines.append(example)
                lines.append("```")
                lines.append("")

        return lines


class APIDocGenerator:
    """Generate API documentation"""

    def generate_openapi_spec(
        self,
        title: str,
        version: str,
        endpoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": "NBA MCP API"
            },
            "servers": [
                {"url": "https://api.nba-mcp.com/v1"}
            ],
            "paths": {}
        }

        for endpoint in endpoints:
            path = endpoint['path']
            method = endpoint['method'].lower()

            spec['paths'][path] = {
                method: {
                    "summary": endpoint.get('summary', ''),
                    "description": endpoint.get('description', ''),
                    "parameters": endpoint.get('parameters', []),
                    "responses": endpoint.get('responses', {
                        "200": {"description": "Successful response"}
                    })
                }
            }

        return spec

    def generate_api_markdown(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate API documentation in Markdown"""
        lines = [
            "# API Documentation",
            "",
            "## Endpoints",
            ""
        ]

        for endpoint in endpoints:
            lines.append(f"### {endpoint['method']} {endpoint['path']}")
            lines.append("")

            if 'description' in endpoint:
                lines.append(endpoint['description'])
                lines.append("")

            # Parameters
            if 'parameters' in endpoint:
                lines.append("**Parameters:**")
                lines.append("")
                for param in endpoint['parameters']:
                    lines.append(f"- `{param['name']}` ({param.get('type', 'string')}): {param.get('description', '')}")
                lines.append("")

            # Example request
            if 'example_request' in endpoint:
                lines.append("**Example Request:**")
                lines.append("")
                lines.append("```bash")
                lines.append(endpoint['example_request'])
                lines.append("```")
                lines.append("")

            # Example response
            if 'example_response' in endpoint:
                lines.append("**Example Response:**")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(endpoint['example_response'], indent=2))
                lines.append("```")
                lines.append("")

        return '\n'.join(lines)


class ArchitectureDiagrammer:
    """Generate architecture diagrams"""

    def generate_mermaid_diagram(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, str]]
    ) -> str:
        """Generate Mermaid diagram"""
        lines = ["```mermaid", "graph TD"]

        # Components
        for comp in components:
            comp_id = comp['id']
            comp_name = comp['name']
            comp_type = comp.get('type', 'component')

            if comp_type == 'database':
                lines.append(f"    {comp_id}[({comp_name})]")
            elif comp_type == 'service':
                lines.append(f"    {comp_id}[{comp_name}]")
            elif comp_type == 'external':
                lines.append(f"    {comp_id}{{{comp_name}}}")

        # Connections
        for conn in connections:
            from_id = conn['from']
            to_id = conn['to']
            label = conn.get('label', '')

            if label:
                lines.append(f"    {from_id} -->|{label}| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        lines.append("```")
        return '\n'.join(lines)

    def generate_sequence_diagram(self, interactions: List[Dict[str, str]]) -> str:
        """Generate Mermaid sequence diagram"""
        lines = ["```mermaid", "sequenceDiagram"]

        for interaction in interactions:
            actor = interaction['from']
            target = interaction['to']
            message = interaction['message']

            lines.append(f"    {actor}->>+{target}: {message}")

            if 'response' in interaction:
                lines.append(f"    {target}-->>-{actor}: {interaction['response']}")

        lines.append("```")
        return '\n'.join(lines)


class DocumentationGenerator:
    """Main documentation generator"""

    def __init__(self, output_dir: str = "docs/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.code_analyzer = CodeAnalyzer()
        self.markdown_gen = MarkdownGenerator()
        self.api_gen = APIDocGenerator()
        self.diagram_gen = ArchitectureDiagrammer()

    def generate_code_docs(self, source_dir: str, pattern: str = "*.py") -> None:
        """Generate documentation for Python files"""
        source_path = Path(source_dir)

        for filepath in source_path.rglob(pattern):
            if '__pycache__' in str(filepath) or 'test_' in filepath.name:
                continue

            try:
                module_doc = self.code_analyzer.analyze_file(str(filepath))
                markdown = self.markdown_gen.generate_module_docs(module_doc)

                # Write to output
                output_file = self.output_dir / f"{module_doc.name}.md"
                with open(output_file, 'w') as f:
                    f.write(markdown)

                logger.info(f"Generated docs for {module_doc.name}")
            except Exception as e:
                logger.error(f"Error generating docs for {filepath}: {e}")

    def generate_api_docs(self, endpoints: List[Dict[str, Any]]) -> None:
        """Generate API documentation"""
        # Markdown
        markdown = self.api_gen.generate_api_markdown(endpoints)
        output_file = self.output_dir / "API.md"
        with open(output_file, 'w') as f:
            f.write(markdown)

        # OpenAPI spec
        spec = self.api_gen.generate_openapi_spec(
            title="NBA MCP API",
            version="1.0.0",
            endpoints=endpoints
        )
        spec_file = self.output_dir / "openapi.json"
        with open(spec_file, 'w') as f:
            json.dump(spec, f, indent=2)

        logger.info("Generated API documentation")

    def generate_architecture_docs(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, str]]
    ) -> None:
        """Generate architecture documentation"""
        diagram = self.diagram_gen.generate_mermaid_diagram(components, connections)

        output_file = self.output_dir / "ARCHITECTURE.md"
        with open(output_file, 'w') as f:
            f.write("# System Architecture\n\n")
            f.write(diagram)

        logger.info("Generated architecture documentation")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Automated Documentation Generator Demo ===\n")

    # Create generator
    doc_gen = DocumentationGenerator(output_dir="docs/generated")

    # Generate architecture diagram
    print("--- Generating Architecture Diagram ---\n")
    components = [
        {"id": "A", "name": "MCP Server", "type": "service"},
        {"id": "B", "name": "PostgreSQL", "type": "database"},
        {"id": "C", "name": "S3", "type": "database"},
        {"id": "D", "name": "Redis", "type": "database"},
        {"id": "E", "name": "Client", "type": "external"}
    ]

    connections = [
        {"from": "E", "to": "A", "label": "API Request"},
        {"from": "A", "to": "B", "label": "Query"},
        {"from": "A", "to": "C", "label": "Read/Write"},
        {"from": "A", "to": "D", "label": "Cache"}
    ]

    doc_gen.generate_architecture_docs(components, connections)
    print("✓ Architecture diagram generated")

    # Generate API docs
    print("\n--- Generating API Documentation ---\n")
    endpoints = [
        {
            "path": "/api/players",
            "method": "GET",
            "summary": "List players",
            "description": "Get list of NBA players with pagination",
            "parameters": [
                {"name": "limit", "type": "integer", "description": "Max results (default: 50)"},
                {"name": "offset", "type": "integer", "description": "Pagination offset"}
            ],
            "example_request": "curl https://api.nba-mcp.com/v1/api/players?limit=10",
            "example_response": {"players": [{"id": 1, "name": "LeBron James"}]}
        }
    ]

    doc_gen.generate_api_docs(endpoints)
    print("✓ API documentation generated")

    print("\n=== Documentation Generated ===")
    print(f"Output directory: {doc_gen.output_dir}")

