#!/usr/bin/env python3
"""
Code Generator from Implementation Plans

Automatically generates skeleton code from recommendation implementation steps.
Creates file structures, function stubs, and TODO comments to accelerate implementation.

Supports:
- Python modules and functions
- SQL scripts for database operations
- Configuration files (YAML, JSON)
- Test stubs
- Documentation templates

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """Represents a generated code file"""
    path: str
    content: str
    language: str
    file_type: str  # module, test, config, sql, doc


class CodeGenerator:
    """
    Generates skeleton code from recommendation implementation plans.

    Features:
    - Analyzes implementation steps to determine file structure
    - Generates Python modules with function stubs
    - Creates SQL scripts for database operations
    - Adds descriptive TODO comments
    - Generates test file stubs
    - Creates README templates
    """

    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': ['python', 'pandas', 'numpy', 'scikit', 'tensorflow', 'pytorch', 'model', 'class', 'function'],
        'sql': ['database', 'table', 'query', 'select', 'insert', 'update', 'schema', 'postgres', 'sql'],
        'javascript': ['javascript', 'node', 'react', 'api', 'frontend', 'express'],
        'config': ['config', 'yaml', 'json', 'settings', 'environment'],
    }

    # File type patterns
    FILE_TYPE_PATTERNS = {
        'ml_model': ['model', 'training', 'prediction', 'classifier', 'regression', 'neural'],
        'data_processing': ['etl', 'pipeline', 'transform', 'clean', 'preprocess', 'feature'],
        'database': ['database', 'schema', 'migration', 'query', 'table'],
        'api': ['api', 'endpoint', 'route', 'rest', 'service'],
        'test': ['test', 'unittest', 'pytest', 'validation'],
        'monitoring': ['monitor', 'logging', 'metrics', 'alert'],
        'deployment': ['deploy', 'docker', 'kubernetes', 'cicd'],
    }

    def __init__(self, project_root: str = ".", output_dir: str = "generated_code"):
        """
        Initialize code generator.

        Args:
            project_root: Root directory of the project
            output_dir: Directory to output generated code
        """
        self.project_root = Path(project_root)
        self.output_dir = self.project_root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🔧 Code Generator initialized")
        logger.info(f"   Project root: {self.project_root}")
        logger.info(f"   Output directory: {self.output_dir}")

    def generate_code(self, recommendation: Dict[str, Any]) -> List[GeneratedFile]:
        """
        Generate code files for a recommendation.

        Args:
            recommendation: Recommendation dictionary with implementation steps

        Returns:
            List of GeneratedFile objects
        """
        title = recommendation.get('title', 'Untitled')
        logger.info(f"🔨 Generating code for: {title}")

        # Determine primary language and file types
        language = self._detect_language(recommendation)
        file_types = self._detect_file_types(recommendation)

        generated_files = []

        # Generate main implementation file
        if language == 'python':
            main_file = self._generate_python_module(recommendation, file_types)
            generated_files.append(main_file)

            # Generate test file
            test_file = self._generate_python_test(recommendation)
            generated_files.append(test_file)

        elif language == 'sql':
            sql_file = self._generate_sql_script(recommendation)
            generated_files.append(sql_file)

        elif language == 'config':
            config_file = self._generate_config_file(recommendation)
            generated_files.append(config_file)

        # Generate README
        readme = self._generate_readme(recommendation, generated_files)
        generated_files.append(readme)

        logger.info(f"✅ Generated {len(generated_files)} files")

        return generated_files

    def _detect_language(self, rec: Dict[str, Any]) -> str:
        """Detect primary programming language from recommendation text"""
        text = (
            rec.get('title', '') + ' ' +
            rec.get('description', '') + ' ' +
            rec.get('technical_details', '')
        ).lower()

        # Score each language
        scores = {}
        for lang, keywords in self.LANGUAGE_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[lang] = score

        # Return language with highest score, default to Python
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            if best_lang[1] > 0:
                return best_lang[0]

        return 'python'  # Default

    def _detect_file_types(self, rec: Dict[str, Any]) -> List[str]:
        """Detect file types needed for recommendation"""
        text = (
            rec.get('title', '') + ' ' +
            rec.get('description', '') + ' ' +
            rec.get('technical_details', '')
        ).lower()

        file_types = []
        for ftype, keywords in self.FILE_TYPE_PATTERNS.items():
            if any(keyword in text for keyword in keywords):
                file_types.append(ftype)

        return file_types if file_types else ['general']

    def _generate_python_module(self, rec: Dict[str, Any], file_types: List[str]) -> GeneratedFile:
        """Generate Python module with function stubs"""
        title = rec.get('title', 'Untitled')
        description = rec.get('description', 'No description')
        steps = rec.get('implementation_steps', [])

        # Generate module name from title
        module_name = self._title_to_module_name(title)

        # Build module content
        lines = [
            '#!/usr/bin/env python3',
            '"""',
            title,
            '',
            description,
            '',
            f"Generated: {datetime.now().isoformat()}",
            'Source: NBA MCP Synthesis Code Generator',
            '"""',
            '',
            'import logging',
            'from typing import Dict, List, Any, Optional, Tuple',
            'from pathlib import Path',
            '',
            'logger = logging.getLogger(__name__)',
            '',
        ]

        # Add imports based on file types
        if 'ml_model' in file_types:
            lines.extend([
                '# Machine Learning imports',
                'import numpy as np',
                'import pandas as pd',
                'from sklearn.model_selection import train_test_split',
                '',
            ])

        if 'database' in file_types:
            lines.extend([
                '# Database imports',
                'import psycopg2',
                'from psycopg2 import pool',
                '',
            ])

        # Generate main class or function based on steps
        if 'ml_model' in file_types:
            lines.extend(self._generate_ml_model_class(title, steps))
        elif 'data_processing' in file_types:
            lines.extend(self._generate_pipeline_class(title, steps))
        else:
            lines.extend(self._generate_general_functions(title, steps))

        # Add main block
        lines.extend([
            '',
            '',
            'if __name__ == "__main__":',
            '    # TODO: Add command-line interface',
            '    logger.info("Running {}")'.format(title),
            '    pass',
            '',
        ])

        content = '\n'.join(lines)

        return GeneratedFile(
            path=f"{module_name}.py",
            content=content,
            language='python',
            file_type='module'
        )

    def _generate_ml_model_class(self, title: str, steps: List[str]) -> List[str]:
        """Generate machine learning model class structure"""
        class_name = self._title_to_class_name(title)

        lines = [
            '',
            f'class {class_name}:',
            '    """',
            f'    {title}',
            '',
            '    Implementation steps:',
        ]

        # Add steps as docstring
        for i, step in enumerate(steps[:10], 1):
            lines.append(f'    {i}. {step}')

        lines.extend([
            '    """',
            '',
            '    def __init__(self):',
            '        """Initialize model"""',
            '        self.model = None',
            '        self.is_trained = False',
            '        logger.info(f"Initialized {self.__class__.__name__}")',
            '',
            '    def prepare_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:',
            '        """',
            '        Prepare data for training.',
            '',
            '        Args:',
            '            data: Input dataframe',
            '',
            '        Returns:',
            '            Tuple of (features, target)',
            '        """',
            '        # TODO: Implement data preparation',
            '        raise NotImplementedError("Data preparation not yet implemented")',
            '',
            '    def train(self, X_train: pd.DataFrame, y_train: pd.Series):',
            '        """',
            '        Train the model.',
            '',
            '        Args:',
            '            X_train: Training features',
            '            y_train: Training target',
            '        """',
            '        # TODO: Implement model training',
            '        logger.info("Training model...")',
            '        raise NotImplementedError("Training not yet implemented")',
            '',
            '    def predict(self, X: pd.DataFrame) -> np.ndarray:',
            '        """',
            '        Make predictions.',
            '',
            '        Args:',
            '            X: Features for prediction',
            '',
            '        Returns:',
            '            Predictions array',
            '        """',
            '        if not self.is_trained:',
            '            raise ValueError("Model must be trained before prediction")',
            '',
            '        # TODO: Implement prediction',
            '        raise NotImplementedError("Prediction not yet implemented")',
            '',
            '    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:',
            '        """',
            '        Evaluate model performance.',
            '',
            '        Args:',
            '            X_test: Test features',
            '            y_test: Test target',
            '',
            '        Returns:',
            '            Dictionary of evaluation metrics',
            '        """',
            '        # TODO: Implement evaluation',
            '        raise NotImplementedError("Evaluation not yet implemented")',
            '',
        ])

        # Add methods for each implementation step
        for i, step in enumerate(steps[:5], 1):  # First 5 steps
            method_name = self._step_to_method_name(step)
            lines.extend([
                f'    def {method_name}(self):',
                '        """',
                f'        Step {i}: {step}',
                '        """',
                f'        # TODO: Implement step {i}',
                f'        raise NotImplementedError("Step {i} not yet implemented")',
                '',
            ])

        return lines

    def _generate_pipeline_class(self, title: str, steps: List[str]) -> List[str]:
        """Generate data pipeline class structure"""
        class_name = self._title_to_class_name(title)

        lines = [
            '',
            f'class {class_name}:',
            '    """',
            f'    {title}',
            '    """',
            '',
            '    def __init__(self):',
            '        """Initialize pipeline"""',
            '        logger.info(f"Initialized {self.__class__.__name__}")',
            '',
            '    def run(self, input_data: Any) -> Any:',
            '        """',
            '        Run the complete pipeline.',
            '',
            '        Args:',
            '            input_data: Input data to process',
            '',
            '        Returns:',
            '            Processed output',
            '        """',
            '        logger.info("Running pipeline...")',
            '',
        ]

        # Add pipeline steps
        for i, step in enumerate(steps[:10], 1):
            method_name = self._step_to_method_name(step)
            lines.append(f'        # Step {i}: {step}')
            lines.append(f'        input_data = self.{method_name}(input_data)')
            lines.append('')

        lines.extend([
            '        return input_data',
            '',
        ])

        # Add method for each step
        for i, step in enumerate(steps[:10], 1):
            method_name = self._step_to_method_name(step)
            lines.extend([
                f'    def {method_name}(self, data: Any) -> Any:',
                '        """',
                f'        {step}',
                '        """',
                f'        # TODO: Implement - {step}',
                '        logger.info(f"Executing step {i}: {step}")',
                '        return data',
                '',
            ])

        return lines

    def _generate_general_functions(self, title: str, steps: List[str]) -> List[str]:
        """Generate general functions from implementation steps"""
        lines = []

        # Main function
        main_func = self._title_to_function_name(title)
        lines.extend([
            '',
            f'def {main_func}():',
            '    """',
            f'    {title}',
            '',
            '    Implementation steps:',
        ])

        for i, step in enumerate(steps[:10], 1):
            lines.append(f'    {i}. {step}')

        lines.extend([
            '    """',
            '    logger.info("Starting {}")'.format(title),
            '',
        ])

        # Call each step function
        for i, step in enumerate(steps[:10], 1):
            func_name = self._step_to_function_name(step)
            lines.append(f'    # Step {i}: {step}')
            lines.append(f'    {func_name}()')
            lines.append('')

        lines.extend([
            '    logger.info("Completed {}")'.format(title),
            '',
        ])

        # Generate function for each step
        for i, step in enumerate(steps[:10], 1):
            func_name = self._step_to_function_name(step)
            lines.extend([
                '',
                f'def {func_name}():',
                '    """',
                f'    {step}',
                '    """',
                f'    # TODO: Implement - {step}',
                f'    logger.info("Step {i}: {step}")',
                '    raise NotImplementedError(f"Step {i} not yet implemented")',
                '',
            ])

        return lines

    def _generate_python_test(self, rec: Dict[str, Any]) -> GeneratedFile:
        """Generate pytest test file"""
        title = rec.get('title', 'Untitled')
        module_name = self._title_to_module_name(title)
        class_name = self._title_to_class_name(title)

        lines = [
            '#!/usr/bin/env python3',
            '"""',
            f'Tests for {title}',
            '',
            f"Generated: {datetime.now().isoformat()}",
            '"""',
            '',
            'import pytest',
            'import pandas as pd',
            'import numpy as np',
            f'from {module_name} import {class_name}',
            '',
            '',
            '@pytest.fixture',
            f'def {module_name}_instance():',
            f'    """Create {class_name} instance for testing"""',
            f'    return {class_name}()',
            '',
            '',
            f'def test_{module_name}_initialization({module_name}_instance):',
            '    """Test initialization"""',
            f'    assert {module_name}_instance is not None',
            '    # TODO: Add more initialization tests',
            '',
            '',
            f'def test_{module_name}_basic_functionality({module_name}_instance):',
            '    """Test basic functionality"""',
            '    # TODO: Implement basic functionality test',
            '    pytest.skip("Not yet implemented")',
            '',
            '',
            f'def test_{module_name}_edge_cases({module_name}_instance):',
            '    """Test edge cases"""',
            '    # TODO: Implement edge case tests',
            '    pytest.skip("Not yet implemented")',
            '',
            '',
            f'def test_{module_name}_error_handling({module_name}_instance):',
            '    """Test error handling"""',
            '    # TODO: Implement error handling tests',
            '    pytest.skip("Not yet implemented")',
            '',
        ]

        content = '\n'.join(lines)

        return GeneratedFile(
            path=f"test_{module_name}.py",
            content=content,
            language='python',
            file_type='test'
        )

    def _generate_sql_script(self, rec: Dict[str, Any]) -> GeneratedFile:
        """Generate SQL script"""
        title = rec.get('title', 'Untitled')
        description = rec.get('description', 'No description')
        steps = rec.get('implementation_steps', [])

        filename = self._title_to_module_name(title)

        lines = [
            '-- ' + title,
            '-- ' + description,
            f'-- Generated: {datetime.now().isoformat()}',
            '--',
            '',
            '-- TODO: Review and customize this SQL script',
            '',
        ]

        # Add commented implementation steps
        lines.append('/*')
        lines.append('Implementation Steps:')
        for i, step in enumerate(steps[:10], 1):
            lines.append(f'{i}. {step}')
        lines.append('*/')
        lines.append('')

        # Generate basic SQL structure based on keywords
        text = (rec.get('description', '') + ' ' + rec.get('technical_details', '')).lower()

        if 'create table' in text or 'schema' in text:
            lines.extend([
                '-- Create table',
                'CREATE TABLE IF NOT EXISTS example_table (',
                '    id SERIAL PRIMARY KEY,',
                '    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,',
                '    -- TODO: Add columns',
                ');',
                '',
                '-- Create indexes',
                '-- CREATE INDEX idx_example ON example_table(column_name);',
                '',
            ])

        elif 'query' in text or 'select' in text:
            lines.extend([
                '-- Query',
                'SELECT',
                '    -- TODO: Add columns',
                '    *',
                'FROM',
                '    -- TODO: Add table name',
                '    table_name',
                'WHERE',
                '    -- TODO: Add conditions',
                '    1=1',
                ';',
                '',
            ])

        else:
            lines.extend([
                '-- TODO: Add SQL statements',
                '',
            ])

        content = '\n'.join(lines)

        return GeneratedFile(
            path=f"{filename}.sql",
            content=content,
            language='sql',
            file_type='sql'
        )

    def _generate_config_file(self, rec: Dict[str, Any]) -> GeneratedFile:
        """Generate configuration file (YAML)"""
        title = rec.get('title', 'Untitled')
        filename = self._title_to_module_name(title)

        config = {
            'name': title,
            'description': rec.get('description', 'No description'),
            'generated': datetime.now().isoformat(),
            'settings': {
                '# TODO': 'Add configuration parameters',
            },
        }

        # Convert to YAML-like format
        lines = [
            f'# {title}',
            f'# Generated: {datetime.now().isoformat()}',
            '',
            f'name: "{title}"',
            f'description: "{rec.get("description", "No description")}"',
            '',
            'settings:',
            '  # TODO: Add configuration parameters',
            '  param1: value1',
            '  param2: value2',
            '',
        ]

        content = '\n'.join(lines)

        return GeneratedFile(
            path=f"{filename}_config.yaml",
            content=content,
            language='yaml',
            file_type='config'
        )

    def _generate_readme(self, rec: Dict[str, Any], generated_files: List[GeneratedFile]) -> GeneratedFile:
        """Generate README for the recommendation implementation"""
        title = rec.get('title', 'Untitled')
        description = rec.get('description', 'No description')
        steps = rec.get('implementation_steps', [])
        time_estimate = rec.get('time_estimate', 'Unknown')
        priority = rec.get('priority', 'MEDIUM')

        lines = [
            f'# {title}',
            '',
            f'**Priority**: {priority}',
            f'**Estimated Time**: {time_estimate}',
            f'**Generated**: {datetime.now().isoformat()}',
            '',
            '---',
            '',
            '## Description',
            '',
            description,
            '',
            '## Implementation Steps',
            '',
        ]

        for i, step in enumerate(steps, 1):
            lines.append(f'{i}. [ ] {step}')

        lines.extend([
            '',
            '## Generated Files',
            '',
        ])

        for gf in generated_files:
            if gf.file_type != 'doc':  # Don't list README itself
                lines.append(f'- `{gf.path}` ({gf.language}) - {gf.file_type}')

        lines.extend([
            '',
            '## Getting Started',
            '',
            '1. Review the generated code files',
            '2. Replace TODO comments with actual implementation',
            '3. Run tests: `pytest test_*.py`',
            '4. Update this README as you progress',
            '',
            '## Technical Details',
            '',
            rec.get('technical_details', 'No technical details provided'),
            '',
            '## Prerequisites',
            '',
            '- Python 3.11+',
            '- Dependencies: See generated code imports',
            '',
            '## Notes',
            '',
            '- This code was auto-generated as a starting point',
            '- All TODO comments must be addressed before production use',
            '- Tests are stubs and need implementation',
            '',
        ])

        content = '\n'.join(lines)

        return GeneratedFile(
            path='README.md',
            content=content,
            language='markdown',
            file_type='doc'
        )

    def _title_to_module_name(self, title: str) -> str:
        """Convert title to valid Python module name"""
        # Remove special characters and convert to snake_case
        name = re.sub(r'[^\w\s]', '', title.lower())
        name = re.sub(r'\s+', '_', name)
        return name[:50]  # Limit length

    def _title_to_class_name(self, title: str) -> str:
        """Convert title to valid Python class name (PascalCase)"""
        words = re.sub(r'[^\w\s]', '', title).split()
        return ''.join(word.capitalize() for word in words)[:50]

    def _title_to_function_name(self, title: str) -> str:
        """Convert title to valid Python function name"""
        name = self._title_to_module_name(title)
        return name[:50]

    def _step_to_method_name(self, step: str) -> str:
        """Convert implementation step to valid method name"""
        # Take first few words, convert to snake_case
        words = re.sub(r'[^\w\s]', '', step.lower()).split()[:5]
        name = '_'.join(words)
        return name[:50] if name else 'step'

    def _step_to_function_name(self, step: str) -> str:
        """Convert implementation step to valid function name"""
        return self._step_to_method_name(step)

    def save_generated_files(self, files: List[GeneratedFile], subdir: Optional[str] = None) -> Path:
        """
        Save generated files to disk.

        Args:
            files: List of GeneratedFile objects
            subdir: Optional subdirectory name (from recommendation title)

        Returns:
            Path to directory where files were saved
        """
        # Create subdirectory
        if subdir:
            output_path = self.output_dir / subdir
        else:
            output_path = self.output_dir / f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        output_path.mkdir(parents=True, exist_ok=True)

        # Save each file
        for gfile in files:
            file_path = output_path / gfile.path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                f.write(gfile.content)

            logger.info(f"   💾 Saved: {file_path}")

        logger.info(f"✅ Saved {len(files)} files to: {output_path}")
        return output_path


def main():
    """CLI for testing code generation"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Generate code from recommendation')
    parser.add_argument('--recommendation', required=True, help='Path to recommendation JSON')
    parser.add_argument('--output-dir', default='generated_code', help='Output directory')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    args = parser.parse_args()

    # Load recommendation
    with open(args.recommendation, 'r') as f:
        data = json.load(f)

    # Handle wrapped format
    if isinstance(data, dict) and 'recommendations' in data:
        recommendations = data['recommendations']
    elif isinstance(data, list):
        recommendations = data
    else:
        recommendations = [data]

    # Generate code for each recommendation
    generator = CodeGenerator(
        project_root=args.project_root,
        output_dir=args.output_dir
    )

    for rec in recommendations[:5]:  # Limit to first 5
        try:
            files = generator.generate_code(rec)

            # Create subdirectory from title
            title = rec.get('title', 'Untitled')
            subdir = generator._title_to_module_name(title)

            # Save files
            output_path = generator.save_generated_files(files, subdir)

            print(f"\n✅ Generated code for: {title}")
            print(f"   Location: {output_path}")
            print(f"   Files: {len(files)}")

        except Exception as e:
            logger.error(f"❌ Failed to generate code for {rec.get('title', 'Unknown')}: {e}")


if __name__ == '__main__':
    main()
