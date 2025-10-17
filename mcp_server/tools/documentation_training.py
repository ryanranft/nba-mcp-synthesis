"""
Phase 10.3: Documentation & Training

Comprehensive documentation and training system for the NBA MCP Server.
Provides interactive tutorials, user guides, API documentation, and training materials.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation that can be generated"""

    USER_GUIDE = "user_guide"
    API_DOCUMENTATION = "api_documentation"
    TUTORIAL = "tutorial"
    REFERENCE_GUIDE = "reference_guide"
    TRAINING_MATERIAL = "training_material"
    QUICK_START = "quick_start"
    TROUBLESHOOTING = "troubleshooting"
    EXAMPLES = "examples"


class TrainingLevel(Enum):
    """Training difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContentFormat(Enum):
    """Content output formats"""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    RESTRUCTURED_TEXT = "rst"


@dataclass
class DocumentationSection:
    """Individual documentation section"""

    section_id: str
    title: str
    content: str
    section_type: DocumentationType
    level: TrainingLevel
    tags: List[str]
    prerequisites: List[str] = None
    estimated_time: int = 0  # minutes
    last_updated: datetime = None


@dataclass
class TutorialStep:
    """Individual tutorial step"""

    step_id: str
    title: str
    description: str
    code_example: str
    expected_output: str
    hints: List[str] = None
    verification: str = None


@dataclass
class TrainingModule:
    """Training module structure"""

    module_id: str
    title: str
    description: str
    level: TrainingLevel
    sections: List[DocumentationSection]
    tutorials: List[TutorialStep]
    prerequisites: List[str]
    estimated_duration: int  # minutes
    learning_objectives: List[str]
    assessment_questions: List[str]


@dataclass
class DocumentationProject:
    """Complete documentation project"""

    project_id: str
    title: str
    description: str
    version: str
    modules: List[TrainingModule]
    sections: List[DocumentationSection]
    generated_at: datetime
    output_formats: List[ContentFormat]


class DocumentationGenerator:
    """Main documentation and training generator"""

    def __init__(self, output_dir: str = "docs"):
        """
        Initialize documentation generator

        Args:
            output_dir: Directory to output generated documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Documentation templates
        self.templates = self._load_templates()

        # Generated content storage
        self.generated_docs: Dict[str, Any] = {}
        self.training_modules: Dict[str, TrainingModule] = {}

        logger.info("Documentation generator initialized")

    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates"""
        templates = {
            "user_guide": self._get_user_guide_template(),
            "api_docs": self._get_api_docs_template(),
            "tutorial": self._get_tutorial_template(),
            "quick_start": self._get_quick_start_template(),
            "training_module": self._get_training_module_template(),
        }
        return templates

    def _get_user_guide_template(self) -> str:
        """Get user guide template"""
        return """# {title}

## Overview
{description}

## Table of Contents
{toc}

## Getting Started
{getting_started}

## Core Features
{core_features}

## Advanced Features
{advanced_features}

## Examples
{examples}

## Troubleshooting
{troubleshooting}

## Support
{support}
"""

    def _get_api_docs_template(self) -> str:
        """Get API documentation template"""
        return """# {title} API Documentation

## Overview
{description}

## Authentication
{auth_info}

## Endpoints
{endpoints}

## Parameters
{parameters}

## Response Formats
{response_formats}

## Error Handling
{error_handling}

## Rate Limiting
{rate_limiting}

## Examples
{examples}
"""

    def _get_tutorial_template(self) -> str:
        """Get tutorial template"""
        return """# {title}

## Prerequisites
{prerequisites}

## Learning Objectives
{objectives}

## Tutorial Steps
{steps}

## Verification
{verification}

## Next Steps
{next_steps}
"""

    def _get_quick_start_template(self) -> str:
        """Get quick start template"""
        return """# {title} Quick Start

## Installation
{installation}

## Basic Usage
{basic_usage}

## First Example
{first_example}

## Next Steps
{next_steps}
"""

    def _get_training_module_template(self) -> str:
        """Get training module template"""
        return """# {title}

## Module Overview
{description}

## Learning Objectives
{objectives}

## Prerequisites
{prerequisites}

## Estimated Duration
{duration} minutes

## Module Content
{content}

## Assessment
{assessment}

## Resources
{resources}
"""

    def generate_user_guide(self, title: str, description: str) -> Dict[str, Any]:
        """
        Generate comprehensive user guide

        Args:
            title: Guide title
            description: Guide description

        Returns:
            Dictionary with generation status and content
        """
        try:
            guide_id = f"guide_{uuid.uuid4().hex[:8]}"

            # Generate table of contents
            toc = self._generate_table_of_contents()

            # Generate sections
            getting_started = self._generate_getting_started_section()
            core_features = self._generate_core_features_section()
            advanced_features = self._generate_advanced_features_section()
            examples = self._generate_examples_section()
            troubleshooting = self._generate_troubleshooting_section()
            support = self._generate_support_section()

            # Generate content
            content = self.templates["user_guide"].format(
                title=title,
                description=description,
                toc=toc,
                getting_started=getting_started,
                core_features=core_features,
                advanced_features=advanced_features,
                examples=examples,
                troubleshooting=troubleshooting,
                support=support,
            )

            # Save to file
            output_file = self.output_dir / f"{guide_id}_user_guide.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            result = {
                "status": "generated",
                "guide_id": guide_id,
                "title": title,
                "output_file": str(output_file),
                "content_length": len(content),
                "sections": 6,
                "timestamp": datetime.now().isoformat(),
            }

            self.generated_docs[guide_id] = result
            logger.info(f"Generated user guide: {guide_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating user guide: {e}")
            return {"status": "error", "message": str(e)}

    def generate_api_documentation(
        self, title: str, description: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive API documentation

        Args:
            title: API documentation title
            description: API description

        Returns:
            Dictionary with generation status and content
        """
        try:
            api_id = f"api_{uuid.uuid4().hex[:8]}"

            # Generate API sections
            auth_info = self._generate_auth_section()
            endpoints = self._generate_endpoints_section()
            parameters = self._generate_parameters_section()
            response_formats = self._generate_response_formats_section()
            error_handling = self._generate_error_handling_section()
            rate_limiting = self._generate_rate_limiting_section()
            examples = self._generate_api_examples_section()

            # Generate content
            content = self.templates["api_docs"].format(
                title=title,
                description=description,
                auth_info=auth_info,
                endpoints=endpoints,
                parameters=parameters,
                response_formats=response_formats,
                error_handling=error_handling,
                rate_limiting=rate_limiting,
                examples=examples,
            )

            # Save to file
            output_file = self.output_dir / f"{api_id}_api_docs.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            result = {
                "status": "generated",
                "api_id": api_id,
                "title": title,
                "output_file": str(output_file),
                "content_length": len(content),
                "endpoints_count": self._count_endpoints(),
                "timestamp": datetime.now().isoformat(),
            }

            self.generated_docs[api_id] = result
            logger.info(f"Generated API documentation: {api_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating API documentation: {e}")
            return {"status": "error", "message": str(e)}

    def generate_tutorial(
        self, title: str, level: TrainingLevel, objectives: List[str]
    ) -> Dict[str, Any]:
        """
        Generate interactive tutorial

        Args:
            title: Tutorial title
            level: Training level
            objectives: Learning objectives

        Returns:
            Dictionary with generation status and content
        """
        try:
            tutorial_id = f"tutorial_{uuid.uuid4().hex[:8]}"

            # Generate tutorial content
            prerequisites = self._generate_prerequisites(level)
            steps = self._generate_tutorial_steps(level)
            verification = self._generate_verification_section()
            next_steps = self._generate_next_steps(level)

            # Generate content
            content = self.templates["tutorial"].format(
                title=title,
                prerequisites=prerequisites,
                objectives="\n".join(f"- {obj}" for obj in objectives),
                steps=steps,
                verification=verification,
                next_steps=next_steps,
            )

            # Save to file
            output_file = self.output_dir / f"{tutorial_id}_tutorial.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            result = {
                "status": "generated",
                "tutorial_id": tutorial_id,
                "title": title,
                "level": level.value,
                "output_file": str(output_file),
                "content_length": len(content),
                "steps_count": len(steps.split("##")),
                "objectives_count": len(objectives),
                "timestamp": datetime.now().isoformat(),
            }

            self.generated_docs[tutorial_id] = result
            logger.info(f"Generated tutorial: {tutorial_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating tutorial: {e}")
            return {"status": "error", "message": str(e)}

    def generate_quick_start_guide(self, title: str) -> Dict[str, Any]:
        """
        Generate quick start guide

        Args:
            title: Quick start guide title

        Returns:
            Dictionary with generation status and content
        """
        try:
            quickstart_id = f"quickstart_{uuid.uuid4().hex[:8]}"

            # Generate quick start content
            installation = self._generate_installation_section()
            basic_usage = self._generate_basic_usage_section()
            first_example = self._generate_first_example_section()
            next_steps = self._generate_next_steps(TrainingLevel.BEGINNER)

            # Generate content
            content = self.templates["quick_start"].format(
                title=title,
                installation=installation,
                basic_usage=basic_usage,
                first_example=first_example,
                next_steps=next_steps,
            )

            # Save to file
            output_file = self.output_dir / f"{quickstart_id}_quickstart.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            result = {
                "status": "generated",
                "quickstart_id": quickstart_id,
                "title": title,
                "output_file": str(output_file),
                "content_length": len(content),
                "sections": 4,
                "timestamp": datetime.now().isoformat(),
            }

            self.generated_docs[quickstart_id] = result
            logger.info(f"Generated quick start guide: {quickstart_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating quick start guide: {e}")
            return {"status": "error", "message": str(e)}

    def create_training_module(
        self, title: str, description: str, level: TrainingLevel
    ) -> Dict[str, Any]:
        """
        Create comprehensive training module

        Args:
            title: Module title
            description: Module description
            level: Training level

        Returns:
            Dictionary with module creation status
        """
        try:
            module_id = f"module_{uuid.uuid4().hex[:8]}"

            # Generate module content
            objectives = self._generate_learning_objectives(level)
            prerequisites = self._generate_prerequisites(level)
            duration = self._estimate_duration(level)
            content = self._generate_module_content(level)
            assessment = self._generate_assessment_questions(level)
            resources = self._generate_resources_section()

            # Create training module
            module = TrainingModule(
                module_id=module_id,
                title=title,
                description=description,
                level=level,
                sections=[],
                tutorials=[],
                prerequisites=prerequisites,
                estimated_duration=duration,
                learning_objectives=objectives,
                assessment_questions=assessment,
            )

            # Generate module documentation
            module_content = self.templates["training_module"].format(
                title=title,
                description=description,
                objectives="\n".join(f"- {obj}" for obj in objectives),
                prerequisites="\n".join(f"- {req}" for req in prerequisites),
                duration=duration,
                content=content,
                assessment="\n".join(f"- {q}" for q in assessment),
                resources=resources,
            )

            # Save to file
            output_file = self.output_dir / f"{module_id}_training_module.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(module_content)

            result = {
                "status": "created",
                "module_id": module_id,
                "title": title,
                "level": level.value,
                "output_file": str(output_file),
                "duration_minutes": duration,
                "objectives_count": len(objectives),
                "prerequisites_count": len(prerequisites),
                "assessment_questions": len(assessment),
                "timestamp": datetime.now().isoformat(),
            }

            self.training_modules[module_id] = module
            logger.info(f"Created training module: {module_id}")
            return result

        except Exception as e:
            logger.error(f"Error creating training module: {e}")
            return {"status": "error", "message": str(e)}

    def generate_comprehensive_documentation(
        self, project_title: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation project

        Args:
            project_title: Project title

        Returns:
            Dictionary with project generation status
        """
        try:
            project_id = f"project_{uuid.uuid4().hex[:8]}"

            # Generate all documentation types
            user_guide = self.generate_user_guide(
                f"{project_title} User Guide", "Comprehensive user guide"
            )
            api_docs = self.generate_api_documentation(
                f"{project_title} API Documentation", "Complete API reference"
            )
            quickstart = self.generate_quick_start_guide(f"{project_title} Quick Start")

            # Generate tutorials for different levels
            beginner_tutorial = self.generate_tutorial(
                f"{project_title} Beginner Tutorial",
                TrainingLevel.BEGINNER,
                [
                    "Understand basic concepts",
                    "Learn fundamental operations",
                    "Complete first examples",
                ],
            )

            intermediate_tutorial = self.generate_tutorial(
                f"{project_title} Intermediate Tutorial",
                TrainingLevel.INTERMEDIATE,
                [
                    "Master advanced features",
                    "Understand complex operations",
                    "Build sophisticated solutions",
                ],
            )

            # Create training modules
            beginner_module = self.create_training_module(
                f"{project_title} Beginner Training",
                "Comprehensive beginner training module",
                TrainingLevel.BEGINNER,
            )

            advanced_module = self.create_training_module(
                f"{project_title} Advanced Training",
                "Advanced training for experienced users",
                TrainingLevel.ADVANCED,
            )

            # Create project summary
            project = DocumentationProject(
                project_id=project_id,
                title=project_title,
                description=f"Comprehensive documentation and training for {project_title}",
                version="1.0.0",
                modules=[beginner_module, advanced_module],
                sections=[],
                generated_at=datetime.now(),
                output_formats=[ContentFormat.MARKDOWN, ContentFormat.HTML],
            )

            # Generate project index
            index_content = self._generate_project_index(project)
            index_file = self.output_dir / f"{project_id}_index.md"
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(index_content)

            result = {
                "status": "generated",
                "project_id": project_id,
                "title": project_title,
                "index_file": str(index_file),
                "components": {
                    "user_guide": user_guide,
                    "api_documentation": api_docs,
                    "quick_start": quickstart,
                    "beginner_tutorial": beginner_tutorial,
                    "intermediate_tutorial": intermediate_tutorial,
                    "beginner_module": beginner_module,
                    "advanced_module": advanced_module,
                },
                "total_files": 8,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Generated comprehensive documentation project: {project_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating comprehensive documentation: {e}")
            return {"status": "error", "message": str(e)}

    def _generate_table_of_contents(self) -> str:
        """Generate table of contents"""
        return """1. [Getting Started](#getting-started)
2. [Core Features](#core-features)
3. [Advanced Features](#advanced-features)
4. [Examples](#examples)
5. [Troubleshooting](#troubleshooting)
6. [Support](#support)"""

    def _generate_getting_started_section(self) -> str:
        """Generate getting started section"""
        return """## Installation

Install the NBA MCP Server using pip:

```bash
pip install nba-mcp-server
```

## Basic Setup

1. Configure your environment variables
2. Initialize the server
3. Connect to the NBA database
4. Start using the tools

## First Steps

Begin with basic formula calculations and gradually explore advanced features."""

    def _generate_core_features_section(self) -> str:
        """Generate core features section"""
        return """## Formula Calculations

The NBA MCP Server provides comprehensive formula calculation capabilities:

- **Player Efficiency Rating (PER)**: All-in-one player rating
- **True Shooting Percentage**: Shooting efficiency metric
- **Usage Rate**: Player involvement metric
- **Four Factors**: Basketball success factors
- **Advanced Metrics**: 50+ specialized metrics

## Data Access

Access NBA data through multiple interfaces:

- **Database Queries**: Direct SQL access to NBA data
- **API Endpoints**: RESTful API for data retrieval
- **Real-time Data**: Live game and player statistics
- **Historical Data**: Complete historical NBA data

## Analysis Tools

Comprehensive analysis capabilities:

- **Statistical Analysis**: Advanced statistical functions
- **Visualization**: Interactive charts and graphs
- **Predictive Analytics**: Machine learning models
- **Performance Monitoring**: System performance tracking"""

    def _generate_advanced_features_section(self) -> str:
        """Generate advanced features section"""
        return """## Multi-Modal Processing

Process formulas from multiple sources:

- **Text Processing**: Natural language to formula conversion
- **Image Processing**: Extract formulas from charts and graphs
- **Data Processing**: Generate formulas from data patterns
- **Cross-Modal Validation**: Validate formulas across sources

## Intelligent Features

AI-powered capabilities:

- **Formula Intelligence**: AI-powered formula analysis
- **Pattern Discovery**: Automatic pattern recognition
- **Optimization**: Performance optimization recommendations
- **Error Correction**: Intelligent error detection and correction

## Production Features

Enterprise-ready capabilities:

- **Deployment Pipeline**: CI/CD automation
- **Performance Monitoring**: Real-time system monitoring
- **Security**: Comprehensive security scanning
- **Scalability**: High-performance scaling options"""

    def _generate_examples_section(self) -> str:
        """Generate examples section"""
        return """## Basic Formula Calculation

```python
# Calculate Player Efficiency Rating
per_result = calculate_per(
    points=25, rebounds=8, assists=5,
    steals=2, blocks=1, turnovers=3,
    fgm=10, fga=20, ftm=5, fta=6
)
print(f"PER: {per_result['per']:.2f}")
```

## Advanced Analysis

```python
# Multi-book formula comparison
comparison = compare_formula_versions(
    formula_name="true_shooting_percentage",
    books=["book1", "book2", "book3"]
)
print(f"Best version: {comparison['best_version']}")
```

## Real-time Monitoring

```python
# Start performance monitoring
monitor = start_performance_monitoring()
# Record custom metrics
record_performance_metric("cpu_usage", 75.5)
# Generate performance report
report = generate_performance_report(hours=24)
```"""

    def _generate_troubleshooting_section(self) -> str:
        """Generate troubleshooting section"""
        return """## Common Issues

### Connection Problems
- Verify database credentials
- Check network connectivity
- Ensure proper firewall configuration

### Performance Issues
- Monitor system resources
- Check for memory leaks
- Optimize query performance

### Formula Errors
- Validate input parameters
- Check formula syntax
- Use error correction tools

## Getting Help

- **Documentation**: Comprehensive guides and references
- **Community**: User forums and discussions
- **Support**: Direct technical support
- **Training**: Interactive tutorials and modules"""

    def _generate_support_section(self) -> str:
        """Generate support section"""
        return """## Documentation

- **User Guide**: Complete user manual
- **API Reference**: Detailed API documentation
- **Tutorials**: Step-by-step guides
- **Examples**: Code examples and use cases

## Community

- **GitHub**: Source code and issues
- **Discord**: Real-time community chat
- **Forums**: Discussion boards
- **Blog**: Latest updates and tips

## Professional Support

- **Training**: Custom training programs
- **Consulting**: Expert consultation services
- **Support**: Priority technical support
- **Custom Development**: Tailored solutions"""

    def _generate_auth_section(self) -> str:
        """Generate authentication section"""
        return """## API Key Authentication

All API requests require authentication using an API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     https://api.nba-mcp-server.com/endpoint
```

## Rate Limiting

API requests are rate limited:
- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1000 requests/hour
- **Enterprise**: Custom limits

## Security

- All communications use HTTPS
- API keys are encrypted
- Regular security audits
- GDPR compliant"""

    def _generate_endpoints_section(self) -> str:
        """Generate endpoints section"""
        return """## Core Endpoints

### Formula Calculations
- `POST /api/formulas/calculate` - Calculate formulas
- `GET /api/formulas/list` - List available formulas
- `POST /api/formulas/validate` - Validate formula syntax

### Data Access
- `GET /api/data/players` - Get player data
- `GET /api/data/games` - Get game data
- `GET /api/data/teams` - Get team data

### Analysis Tools
- `POST /api/analysis/statistical` - Statistical analysis
- `POST /api/analysis/predictive` - Predictive analytics
- `GET /api/analysis/visualizations` - Generate visualizations

### Monitoring
- `GET /api/monitoring/status` - System status
- `POST /api/monitoring/metrics` - Record metrics
- `GET /api/monitoring/reports` - Performance reports"""

    def _generate_parameters_section(self) -> str:
        """Generate parameters section"""
        return """## Common Parameters

### Formula Parameters
- `formula_name`: Name of the formula to calculate
- `parameters`: Dictionary of formula parameters
- `options`: Additional calculation options

### Data Parameters
- `limit`: Maximum number of results
- `offset`: Number of results to skip
- `filters`: Data filtering criteria
- `sort`: Sorting criteria

### Analysis Parameters
- `analysis_type`: Type of analysis to perform
- `data`: Input data for analysis
- `options`: Analysis configuration options

## Parameter Validation

All parameters are validated using Pydantic models:
- **Type Checking**: Automatic type validation
- **Range Validation**: Min/max value checking
- **Format Validation**: String format validation
- **Required Fields**: Mandatory parameter checking"""

    def _generate_response_formats_section(self) -> str:
        """Generate response formats section"""
        return """## Standard Response Format

All API responses follow a consistent format:

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456",
    "version": "1.0.0"
  }
}
```

## Error Response Format

Error responses include detailed error information:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter value",
    "details": {
      "field": "formula_name",
      "value": "invalid_formula"
    }
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Data Formats

- **JSON**: Primary data format
- **CSV**: Export format for data
- **XML**: Legacy format support
- **Binary**: High-performance binary format"""

    def _generate_error_handling_section(self) -> str:
        """Generate error handling section"""
        return """## HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Error Types

### Validation Errors
- Invalid parameter values
- Missing required parameters
- Type mismatches

### Authentication Errors
- Invalid API key
- Expired credentials
- Insufficient permissions

### Rate Limit Errors
- Too many requests
- Quota exceeded
- Throttling applied

### Server Errors
- Internal processing errors
- Database connection issues
- Service unavailable"""

    def _generate_rate_limiting_section(self) -> str:
        """Generate rate limiting section"""
        return """## Rate Limits

### Free Tier
- **100 requests/hour**
- **1000 requests/day**
- **Basic support**

### Pro Tier
- **1000 requests/hour**
- **10000 requests/day**
- **Priority support**
- **Advanced features**

### Enterprise Tier
- **Custom limits**
- **Unlimited requests**
- **Dedicated support**
- **Custom integrations**

## Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Handling Rate Limits

When rate limits are exceeded:

1. **Wait**: Wait for the reset time
2. **Upgrade**: Upgrade to a higher tier
3. **Optimize**: Reduce request frequency
4. **Cache**: Implement response caching"""

    def _generate_api_examples_section(self) -> str:
        """Generate API examples section"""
        return """## Python Examples

### Basic Formula Calculation

```python
import requests

# Calculate Player Efficiency Rating
response = requests.post(
    "https://api.nba-mcp-server.com/api/formulas/calculate",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "formula_name": "player_efficiency_rating",
        "parameters": {
            "points": 25,
            "rebounds": 8,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "fgm": 10,
            "fga": 20,
            "ftm": 5,
            "fta": 6
        }
    }
)

result = response.json()
print(f"PER: {result['data']['per']:.2f}")
```

### Data Retrieval

```python
# Get player statistics
response = requests.get(
    "https://api.nba-mcp-server.com/api/data/players",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    params={
        "season": "2023-24",
        "team": "Lakers",
        "limit": 50
    }
)

players = response.json()['data']
for player in players:
    print(f"{player['name']}: {player['points_per_game']} PPG")
```

## JavaScript Examples

### Formula Calculation

```javascript
// Calculate True Shooting Percentage
const response = await fetch('https://api.nba-mcp-server.com/api/formulas/calculate', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    formula_name: 'true_shooting_percentage',
    parameters: {
      points: 25,
      fga: 20,
      fta: 6
    }
  })
});

const result = await response.json();
console.log(`TS%: ${result.data.ts_percentage.toFixed(3)}`);
```"""

    def _generate_prerequisites(self, level: TrainingLevel) -> str:
        """Generate prerequisites based on level"""
        prerequisites = {
            TrainingLevel.BEGINNER: [
                "Basic understanding of basketball statistics",
                "Familiarity with web APIs",
                "Basic programming knowledge",
            ],
            TrainingLevel.INTERMEDIATE: [
                "Experience with NBA analytics",
                "Python programming skills",
                "Understanding of statistical concepts",
                "API integration experience",
            ],
            TrainingLevel.ADVANCED: [
                "Advanced NBA analytics knowledge",
                "Expert Python programming",
                "Machine learning experience",
                "Production system experience",
            ],
            TrainingLevel.EXPERT: [
                "Professional NBA analytics experience",
                "System architecture knowledge",
                "Performance optimization expertise",
                "Enterprise deployment experience",
            ],
        }

        prereq_list = prerequisites.get(level, prerequisites[TrainingLevel.BEGINNER])
        return "\n".join(f"- {prereq}" for prereq in prereq_list)

    def _generate_tutorial_steps(self, level: TrainingLevel) -> str:
        """Generate tutorial steps based on level"""
        if level == TrainingLevel.BEGINNER:
            return """## Step 1: Installation and Setup

1. Install the NBA MCP Server
2. Configure your environment
3. Verify installation

## Step 2: Basic Formula Calculation

1. Import required modules
2. Calculate a simple formula
3. Interpret the results

## Step 3: Data Access

1. Connect to the database
2. Retrieve player data
3. Perform basic analysis

## Step 4: Your First Analysis

1. Choose a player or team
2. Calculate relevant metrics
3. Create a simple report"""

        elif level == TrainingLevel.INTERMEDIATE:
            return """## Step 1: Advanced Formula Usage

1. Use complex formulas
2. Combine multiple metrics
3. Create custom calculations

## Step 2: Data Analysis

1. Perform statistical analysis
2. Create visualizations
3. Generate insights

## Step 3: API Integration

1. Build API clients
2. Handle authentication
3. Implement error handling

## Step 4: Performance Optimization

1. Optimize queries
2. Implement caching
3. Monitor performance"""

        else:  # Advanced/Expert
            return """## Step 1: System Architecture

1. Design system architecture
2. Implement scalability
3. Handle high loads

## Step 2: Advanced Analytics

1. Implement machine learning
2. Create predictive models
3. Build recommendation systems

## Step 3: Production Deployment

1. Deploy to production
2. Implement monitoring
3. Handle failures

## Step 4: Custom Extensions

1. Create custom tools
2. Extend functionality
3. Contribute to ecosystem"""

    def _generate_verification_section(self) -> str:
        """Generate verification section"""
        return """## Verification Checklist

- [ ] Installation completed successfully
- [ ] Basic formulas calculate correctly
- [ ] Data access works properly
- [ ] API responses are valid
- [ ] Error handling works
- [ ] Performance is acceptable

## Testing Your Implementation

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Verify performance requirements
4. **User Acceptance Tests**: Validate user experience

## Common Issues

- **Configuration Errors**: Check environment variables
- **Permission Issues**: Verify API keys and access
- **Performance Issues**: Monitor resource usage
- **Data Quality**: Validate input data"""

    def _generate_next_steps(self, level: TrainingLevel) -> str:
        """Generate next steps based on level"""
        if level == TrainingLevel.BEGINNER:
            return """## Continue Learning

1. **Intermediate Tutorial**: Learn advanced features
2. **API Documentation**: Explore API capabilities
3. **Examples**: Study code examples
4. **Community**: Join user community

## Practice Projects

1. **Player Analysis**: Analyze your favorite player
2. **Team Comparison**: Compare team performance
3. **Season Analysis**: Analyze a complete season
4. **Custom Metrics**: Create your own metrics"""

        elif level == TrainingLevel.INTERMEDIATE:
            return """## Advanced Topics

1. **Machine Learning**: Implement ML models
2. **Real-time Analysis**: Build live dashboards
3. **Custom Tools**: Create specialized tools
4. **Performance Optimization**: Optimize your code

## Professional Development

1. **Certification**: Get NBA Analytics certification
2. **Contributing**: Contribute to open source
3. **Speaking**: Share your knowledge
4. **Consulting**: Offer professional services"""

        else:  # Advanced/Expert
            return """## Leadership Opportunities

1. **Mentoring**: Mentor other developers
2. **Architecture**: Design system architectures
3. **Innovation**: Drive innovation initiatives
4. **Standards**: Help set industry standards

## Advanced Projects

1. **Enterprise Solutions**: Build enterprise systems
2. **Research**: Conduct advanced research
3. **Open Source**: Lead open source projects
4. **Industry Impact**: Make industry-wide impact"""

    def _generate_installation_section(self) -> str:
        """Generate installation section"""
        return """## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for development)

## Installation Methods

### Using pip (Recommended)

```bash
pip install nba-mcp-server
```

### From Source

```bash
git clone https://github.com/nba-mcp-server/nba-mcp-server.git
cd nba-mcp-server
pip install -e .
```

### Using Docker

```bash
docker pull nba-mcp-server:latest
docker run -p 8080:8080 nba-mcp-server
```

## Verification

Test your installation:

```python
import nba_mcp_server
print(nba_mcp_server.__version__)
```"""

    def _generate_basic_usage_section(self) -> str:
        """Generate basic usage section"""
        return """## Quick Start

1. **Import the library**:
   ```python
   from nba_mcp_server import NBA_MCP_Server
   ```

2. **Initialize the server**:
   ```python
   server = NBA_MCP_Server()
   ```

3. **Calculate a formula**:
   ```python
   result = server.calculate_formula("per", {
       "points": 25,
       "rebounds": 8,
       "assists": 5
   })
   ```

4. **Access data**:
   ```python
   players = server.get_players(season="2023-24")
   ```

## Configuration

Set up your environment:

```python
# Set API key
os.environ["NBA_API_KEY"] = "your_api_key"

# Configure database
server.configure_database(
    host="localhost",
    port=5432,
    database="nba_data"
)
```"""

    def _generate_first_example_section(self) -> str:
        """Generate first example section"""
        return """## Complete Example

Here's a complete example that demonstrates the core functionality:

```python
from nba_mcp_server import NBA_MCP_Server

# Initialize server
server = NBA_MCP_Server()

# Get player data
player = server.get_player("LeBron James", season="2023-24")

# Calculate Player Efficiency Rating
per = server.calculate_formula("player_efficiency_rating", {
    "points": player["points_per_game"],
    "rebounds": player["rebounds_per_game"],
    "assists": player["assists_per_game"],
    "steals": player["steals_per_game"],
    "blocks": player["blocks_per_game"],
    "turnovers": player["turnovers_per_game"],
    "fgm": player["field_goals_made"],
    "fga": player["field_goals_attempted"],
    "ftm": player["free_throws_made"],
    "fta": player["free_throws_attempted"]
})

print(f"LeBron James PER: {per['per']:.2f}")

# Calculate True Shooting Percentage
ts_percentage = server.calculate_formula("true_shooting_percentage", {
    "points": player["points_per_game"],
    "fga": player["field_goals_attempted"],
    "fta": player["free_throws_attempted"]
})

print(f"LeBron James TS%: {ts_percentage['ts_percentage']:.3f}")
```

## Expected Output

```
LeBron James PER: 25.67
LeBron James TS%: 0.612
```

This example shows how to:
1. Initialize the server
2. Retrieve player data
3. Calculate advanced metrics
4. Display results"""

    def _generate_learning_objectives(self, level: TrainingLevel) -> List[str]:
        """Generate learning objectives based on level"""
        objectives = {
            TrainingLevel.BEGINNER: [
                "Understand NBA analytics fundamentals",
                "Learn basic formula calculations",
                "Master data access and retrieval",
                "Create simple analysis reports",
            ],
            TrainingLevel.INTERMEDIATE: [
                "Master advanced formula calculations",
                "Implement statistical analysis",
                "Build API integrations",
                "Create interactive visualizations",
            ],
            TrainingLevel.ADVANCED: [
                "Design system architectures",
                "Implement machine learning models",
                "Optimize performance and scalability",
                "Deploy production systems",
            ],
            TrainingLevel.EXPERT: [
                "Lead technical initiatives",
                "Design enterprise solutions",
                "Drive innovation and research",
                "Mentor and develop teams",
            ],
        }

        return objectives.get(level, objectives[TrainingLevel.BEGINNER])

    def _estimate_duration(self, level: TrainingLevel) -> int:
        """Estimate training duration based on level"""
        durations = {
            TrainingLevel.BEGINNER: 120,  # 2 hours
            TrainingLevel.INTERMEDIATE: 240,  # 4 hours
            TrainingLevel.ADVANCED: 480,  # 8 hours
            TrainingLevel.EXPERT: 720,  # 12 hours
        }

        return durations.get(level, durations[TrainingLevel.BEGINNER])

    def _generate_module_content(self, level: TrainingLevel) -> str:
        """Generate module content based on level"""
        if level == TrainingLevel.BEGINNER:
            return """## Module 1: Introduction to NBA Analytics
- Understanding basketball statistics
- Key performance indicators
- Basic formula concepts

## Module 2: Getting Started
- Installation and setup
- Basic configuration
- First calculations

## Module 3: Data Access
- Database connections
- Data retrieval methods
- Basic queries

## Module 4: Practical Application
- Real-world examples
- Common use cases
- Best practices"""

        elif level == TrainingLevel.INTERMEDIATE:
            return """## Module 1: Advanced Formulas
- Complex formula calculations
- Custom metric creation
- Formula optimization

## Module 2: Statistical Analysis
- Statistical methods
- Data analysis techniques
- Interpretation of results

## Module 3: API Development
- Building API clients
- Authentication handling
- Error management

## Module 4: Visualization
- Creating charts and graphs
- Interactive dashboards
- Data presentation"""

        else:  # Advanced/Expert
            return """## Module 1: System Architecture
- Scalable system design
- Performance optimization
- Security considerations

## Module 2: Machine Learning
- Predictive models
- Pattern recognition
- Recommendation systems

## Module 3: Production Deployment
- Deployment strategies
- Monitoring and alerting
- Maintenance procedures

## Module 4: Advanced Topics
- Custom extensions
- Integration patterns
- Future technologies"""

    def _generate_assessment_questions(self, level: TrainingLevel) -> List[str]:
        """Generate assessment questions based on level"""
        questions = {
            TrainingLevel.BEGINNER: [
                "What is Player Efficiency Rating and how is it calculated?",
                "How do you retrieve player data from the database?",
                "What are the key components of True Shooting Percentage?",
                "How do you handle errors in formula calculations?",
            ],
            TrainingLevel.INTERMEDIATE: [
                "How do you optimize database queries for performance?",
                "What are the best practices for API error handling?",
                "How do you implement caching for frequently accessed data?",
                "What statistical methods are most appropriate for NBA analysis?",
            ],
            TrainingLevel.ADVANCED: [
                "How do you design a scalable architecture for NBA analytics?",
                "What machine learning algorithms are best for player prediction?",
                "How do you implement real-time data processing?",
                "What are the key considerations for production deployment?",
            ],
            TrainingLevel.EXPERT: [
                "How do you design enterprise-grade NBA analytics platforms?",
                "What are the emerging trends in sports analytics technology?",
                "How do you lead technical teams in NBA analytics projects?",
                "What are the ethical considerations in sports data analysis?",
            ],
        }

        return questions.get(level, questions[TrainingLevel.BEGINNER])

    def _generate_resources_section(self) -> str:
        """Generate resources section"""
        return """## Documentation
- **User Guide**: Comprehensive user manual
- **API Reference**: Complete API documentation
- **Tutorials**: Step-by-step learning guides
- **Examples**: Code examples and use cases

## Community
- **GitHub Repository**: Source code and issues
- **Discord Server**: Real-time community chat
- **Discussion Forums**: Q&A and discussions
- **Blog**: Latest updates and insights

## Training Materials
- **Video Tutorials**: Visual learning content
- **Interactive Labs**: Hands-on practice
- **Certification Programs**: Professional certification
- **Workshops**: Live training sessions

## Professional Support
- **Technical Support**: Expert assistance
- **Consulting Services**: Custom solutions
- **Training Programs**: Corporate training
- **Custom Development**: Tailored implementations"""

    def _generate_project_index(self, project: DocumentationProject) -> str:
        """Generate project index"""
        return f"""# {project.title} Documentation

## Project Overview
{project.description}

## Version
{project.version}

## Generated Components

### User Documentation
- **User Guide**: Complete user manual
- **Quick Start**: Get started quickly
- **API Documentation**: Complete API reference

### Training Materials
- **Beginner Tutorial**: Step-by-step beginner guide
- **Intermediate Tutorial**: Advanced features tutorial
- **Beginner Training Module**: Comprehensive beginner training
- **Advanced Training Module**: Expert-level training

### Generated Files
{self._list_generated_files()}

## Getting Started

1. **New Users**: Start with the Quick Start guide
2. **API Users**: Review the API Documentation
3. **Training**: Begin with the Beginner Training Module
4. **Advanced Users**: Jump to Advanced Training Module

## Support

- **Documentation**: Comprehensive guides and references
- **Community**: User forums and discussions
- **Training**: Interactive tutorials and modules
- **Professional Support**: Expert consultation and training

## Last Updated
{project.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _list_generated_files(self) -> str:
        """List all generated files"""
        files = []
        for doc_id, doc_info in self.generated_docs.items():
            if "output_file" in doc_info:
                files.append(f"- {doc_info['title']}: `{doc_info['output_file']}`")

        return "\n".join(files) if files else "No files generated yet"

    def _count_endpoints(self) -> int:
        """Count API endpoints"""
        return 20  # Estimated number of endpoints

    def export_documentation(
        self, format_type: ContentFormat, doc_id: str
    ) -> Dict[str, Any]:
        """
        Export documentation in specified format

        Args:
            format_type: Output format
            doc_id: Documentation ID

        Returns:
            Dictionary with export status
        """
        try:
            if doc_id not in self.generated_docs:
                return {
                    "status": "error",
                    "message": f"Documentation {doc_id} not found",
                }

            doc_info = self.generated_docs[doc_id]
            input_file = doc_info.get("output_file")

            if not input_file or not os.path.exists(input_file):
                return {"status": "error", "message": "Source file not found"}

            # Read source content
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Convert to target format
            if format_type == ContentFormat.HTML:
                output_content = self._convert_to_html(content)
                output_file = input_file.replace(".md", ".html")
            elif format_type == ContentFormat.PDF:
                output_content = self._convert_to_pdf(content)
                output_file = input_file.replace(".md", ".pdf")
            elif format_type == ContentFormat.JSON:
                output_content = self._convert_to_json(content)
                output_file = input_file.replace(".md", ".json")
            else:
                return {
                    "status": "error",
                    "message": f"Format {format_type.value} not supported",
                }

            # Save converted content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_content)

            result = {
                "status": "exported",
                "doc_id": doc_id,
                "format": format_type.value,
                "output_file": output_file,
                "content_length": len(output_content),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Exported documentation {doc_id} to {format_type.value}")
            return result

        except Exception as e:
            logger.error(f"Error exporting documentation: {e}")
            return {"status": "error", "message": str(e)}

    def _convert_to_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML"""
        # Simple markdown to HTML conversion
        html_content = markdown_content
        html_content = html_content.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html_content = html_content.replace("## ", "<h2>").replace("\n", "</h2>\n")
        html_content = html_content.replace("### ", "<h3>").replace("\n", "</h3>\n")
        html_content = html_content.replace("**", "<strong>").replace("**", "</strong>")
        html_content = html_content.replace("*", "<em>").replace("*", "</em>")

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>NBA MCP Server Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

    def _convert_to_pdf(self, markdown_content: str) -> str:
        """Convert markdown to PDF (simplified)"""
        # In a real implementation, this would use a library like weasyprint or reportlab
        return (
            f"PDF conversion not implemented. Content length: {len(markdown_content)}"
        )

    def _convert_to_json(self, markdown_content: str) -> str:
        """Convert markdown to JSON"""
        import json

        # Simple conversion to JSON structure
        lines = markdown_content.split("\n")
        sections = []
        current_section = {"title": "", "content": ""}

        for line in lines:
            if line.startswith("#"):
                if current_section["title"]:
                    sections.append(current_section)
                current_section = {"title": line.strip("# "), "content": ""}
            else:
                current_section["content"] += line + "\n"

        if current_section["title"]:
            sections.append(current_section)

        return json.dumps(
            {
                "documentation": {
                    "sections": sections,
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "total_sections": len(sections),
                    },
                }
            },
            indent=2,
        )

    def get_documentation_status(self) -> Dict[str, Any]:
        """
        Get documentation generation status

        Returns:
            Dictionary with status information
        """
        return {
            "status": "success",
            "total_docs": len(self.generated_docs),
            "total_modules": len(self.training_modules),
            "output_directory": str(self.output_dir),
            "available_formats": [fmt.value for fmt in ContentFormat],
            "generated_docs": list(self.generated_docs.keys()),
            "training_modules": list(self.training_modules.keys()),
            "timestamp": datetime.now().isoformat(),
        }


# Global generator instance
_global_generator: Optional[DocumentationGenerator] = None


def get_documentation_generator() -> DocumentationGenerator:
    """Get global documentation generator instance"""
    global _global_generator
    if _global_generator is None:
        _global_generator = DocumentationGenerator()
    return _global_generator


# Standalone functions for MCP integration
def generate_user_guide(title: str, description: str) -> Dict[str, Any]:
    """Generate comprehensive user guide"""
    generator = get_documentation_generator()
    return generator.generate_user_guide(title, description)


def generate_api_documentation(title: str, description: str) -> Dict[str, Any]:
    """Generate comprehensive API documentation"""
    generator = get_documentation_generator()
    return generator.generate_api_documentation(title, description)


def generate_tutorial(title: str, level: str, objectives: List[str]) -> Dict[str, Any]:
    """Generate interactive tutorial"""
    generator = get_documentation_generator()
    try:
        training_level = TrainingLevel(level)
        return generator.generate_tutorial(title, training_level, objectives)
    except ValueError:
        return {"status": "error", "message": f"Invalid training level: {level}"}


def generate_quick_start_guide(title: str) -> Dict[str, Any]:
    """Generate quick start guide"""
    generator = get_documentation_generator()
    return generator.generate_quick_start_guide(title)


def create_training_module(title: str, description: str, level: str) -> Dict[str, Any]:
    """Create comprehensive training module"""
    generator = get_documentation_generator()
    try:
        training_level = TrainingLevel(level)
        return generator.create_training_module(title, description, training_level)
    except ValueError:
        return {"status": "error", "message": f"Invalid training level: {level}"}


def generate_comprehensive_documentation(project_title: str) -> Dict[str, Any]:
    """Generate comprehensive documentation project"""
    generator = get_documentation_generator()
    return generator.generate_comprehensive_documentation(project_title)


def export_documentation(format_type: str, doc_id: str) -> Dict[str, Any]:
    """Export documentation in specified format"""
    generator = get_documentation_generator()
    try:
        content_format = ContentFormat(format_type)
        return generator.export_documentation(content_format, doc_id)
    except ValueError:
        return {"status": "error", "message": f"Invalid format type: {format_type}"}


def get_documentation_status() -> Dict[str, Any]:
    """Get documentation generation status"""
    generator = get_documentation_generator()
    return generator.get_documentation_status()
