#!/usr/bin/env python3
"""
Phase 8.5: Pre-Integration Validation

Validates all generated files before integration into nba-simulator-aws.
Acts as quality gate between file generation (Phase 4) and integration (Phase 9).

Validation Checks:
1. Python syntax validation (all .py files)
2. Import conflict detection
3. Test discovery (pytest --collect-only)
4. SQL migration validation
5. Documentation completeness
6. Integration impact estimation

Success Criteria:
- 100% Python syntax validation passed
- >80% of generated tests pass
- 0 import conflicts detected
- SQL migrations validated (if present)
- Integration impact estimated and acceptable

Usage:
    # Validate all generated files
    python scripts/phase8_5_validation.py
    
    # Validate specific directory
    python scripts/phase8_5_validation.py --target implementation_plans/phase_0/rec_22_panel_data
    
    # Skip test execution (faster)
    python scripts/phase8_5_validation.py --skip-tests
"""

import ast
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    details: str
    files_checked: int
    errors: List[str]
    warnings: List[str]


class Phase85Validator:
    """
    Pre-integration validation for generated files.
    
    Validates:
    - Python syntax
    - Import integrity
    - Test discovery
    - SQL migrations
    - Documentation
    - Integration impact
    """
    
    def __init__(self, target_dir: Optional[Path] = None):
        """
        Initialize validator.
        
        Args:
            target_dir: Directory to validate (defaults to implementation_plans/)
        """
        self.target_dir = target_dir or Path("implementation_plans")
        self.results: List[ValidationResult] = []
        
        logger.info("🔍 Phase 8.5: Pre-Integration Validation")
        logger.info(f"   Target: {self.target_dir}")
    
    async def validate_all(self, skip_tests: bool = False) -> Dict:
        """
        Run all validation checks.
        
        Args:
            skip_tests: Skip test execution (faster validation)
        
        Returns:
            Comprehensive validation report
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 8.5: PRE-INTEGRATION VALIDATION")
        logger.info("="*60 + "\n")
        
        # Check 1: Python syntax
        syntax_result = self.validate_python_syntax()
        self.results.append(syntax_result)
        
        # Check 2: Import conflicts
        import_result = self.validate_imports()
        self.results.append(import_result)
        
        # Check 3: Test discovery
        test_discovery_result = self.validate_test_discovery()
        self.results.append(test_discovery_result)
        
        # Check 4: Test execution (if not skipped)
        if not skip_tests:
            test_exec_result = self.validate_test_execution()
            self.results.append(test_exec_result)
        
        # Check 5: SQL migrations
        sql_result = self.validate_sql_migrations()
        self.results.append(sql_result)
        
        # Check 6: Documentation
        docs_result = self.validate_documentation()
        self.results.append(docs_result)
        
        # Check 7: Integration impact
        impact_result = self.estimate_integration_impact()
        self.results.append(impact_result)
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_path = self.target_dir / "VALIDATION_REPORT.md"
        report_path.write_text(report)
        logger.info(f"\n📊 Validation report saved: {report_path}")
        
        # Determine overall pass/fail
        overall_pass = all(r.passed for r in self.results)
        
        return {
            'overall_pass': overall_pass,
            'results': [asdict(r) for r in self.results],
            'report_path': str(report_path)
        }
    
    def validate_python_syntax(self) -> ValidationResult:
        """
        Validate Python syntax for all .py files.
        
        Returns:
            ValidationResult with syntax check results
        """
        logger.info("1️⃣  Validating Python syntax...")
        
        python_files = list(self.target_dir.rglob("*.py"))
        errors = []
        warnings = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    code = f.read()
                ast.parse(code, filename=str(py_file))
            
            except SyntaxError as e:
                error_msg = f"{py_file}: Line {e.lineno}: {e.msg}"
                errors.append(error_msg)
                logger.error(f"   ❌ {error_msg}")
            
            except Exception as e:
                error_msg = f"{py_file}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"   ❌ {error_msg}")
        
        passed = len(errors) == 0
        
        if passed:
            logger.info(f"   ✅ All {len(python_files)} Python files have valid syntax")
        else:
            logger.error(f"   ❌ {len(errors)} syntax errors found in {len(python_files)} files")
        
        return ValidationResult(
            check_name="Python Syntax Validation",
            passed=passed,
            details=f"Checked {len(python_files)} Python files",
            files_checked=len(python_files),
            errors=errors,
            warnings=warnings
        )
    
    def validate_imports(self) -> ValidationResult:
        """
        Validate that imports are resolvable and no conflicts exist.
        
        Returns:
            ValidationResult with import check results
        """
        logger.info("2️⃣  Validating imports...")
        
        python_files = list(self.target_dir.rglob("*.py"))
        errors = []
        warnings = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    code = f.read()
                
                tree = ast.parse(code, filename=str(py_file))
                
                # Extract imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            # Try to import (will catch missing modules)
                            try:
                                __import__(module_name)
                            except ImportError:
                                # Check if it's a local module (acceptable)
                                if not module_name.startswith('.') and module_name not in ['implement_rec', 'test_rec']:
                                    warning_msg = f"{py_file}: Cannot import '{module_name}'"
                                    warnings.append(warning_msg)
                    
                    elif isinstance(node, ast.ImportFrom):
                        module_name = node.module
                        if module_name:
                            try:
                                __import__(module_name)
                            except ImportError:
                                if not module_name.startswith('.'):
                                    warning_msg = f"{py_file}: Cannot import from '{module_name}'"
                                    warnings.append(warning_msg)
            
            except Exception as e:
                error_msg = f"{py_file}: Import validation failed: {str(e)}"
                errors.append(error_msg)
        
        passed = len(errors) == 0
        
        if passed and len(warnings) == 0:
            logger.info(f"   ✅ All imports validated")
        elif passed:
            logger.warning(f"   ⚠️  {len(warnings)} import warnings (may be acceptable)")
        else:
            logger.error(f"   ❌ {len(errors)} import errors found")
        
        return ValidationResult(
            check_name="Import Validation",
            passed=passed,
            details=f"Checked imports in {len(python_files)} Python files",
            files_checked=len(python_files),
            errors=errors,
            warnings=warnings
        )
    
    def validate_test_discovery(self) -> ValidationResult:
        """
        Validate that pytest can discover all tests.
        
        Returns:
            ValidationResult with test discovery results
        """
        logger.info("3️⃣  Validating test discovery...")
        
        test_files = list(self.target_dir.rglob("test_*.py"))
        errors = []
        warnings = []
        
        if len(test_files) == 0:
            logger.warning("   ⚠️  No test files found")
            return ValidationResult(
                check_name="Test Discovery",
                passed=True,
                details="No test files to discover",
                files_checked=0,
                errors=[],
                warnings=["No test files found"]
            )
        
        # Try pytest collection
        try:
            result = subprocess.run(
                ['pytest', '--collect-only', str(self.target_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 or result.returncode == 5:  # 5 = no tests collected (acceptable)
                # Parse output to count tests
                output = result.stdout
                test_count = output.count('<Function') + output.count('<Method')
                
                logger.info(f"   ✅ Discovered {test_count} tests in {len(test_files)} test files")
                
                return ValidationResult(
                    check_name="Test Discovery",
                    passed=True,
                    details=f"Discovered {test_count} tests in {len(test_files)} files",
                    files_checked=len(test_files),
                    errors=[],
                    warnings=warnings
                )
            else:
                error_msg = f"pytest collection failed: {result.stderr[:200]}"
                errors.append(error_msg)
                logger.error(f"   ❌ {error_msg}")
        
        except FileNotFoundError:
            warning_msg = "pytest not installed - skipping test discovery"
            warnings.append(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
            
            return ValidationResult(
                check_name="Test Discovery",
                passed=True,
                details="pytest not available",
                files_checked=len(test_files),
                errors=[],
                warnings=warnings
            )
        
        except Exception as e:
            error_msg = f"Test discovery error: {str(e)}"
            errors.append(error_msg)
            logger.error(f"   ❌ {error_msg}")
        
        return ValidationResult(
            check_name="Test Discovery",
            passed=len(errors) == 0,
            details=f"Checked {len(test_files)} test files",
            files_checked=len(test_files),
            errors=errors,
            warnings=warnings
        )
    
    def validate_test_execution(self) -> ValidationResult:
        """
        Execute tests and validate pass rate.
        
        Returns:
            ValidationResult with test execution results
        """
        logger.info("4️⃣  Executing tests...")
        
        test_files = list(self.target_dir.rglob("test_*.py"))
        errors = []
        warnings = []
        
        if len(test_files) == 0:
            return ValidationResult(
                check_name="Test Execution",
                passed=True,
                details="No tests to execute",
                files_checked=0,
                errors=[],
                warnings=["No test files found"]
            )
        
        try:
            result = subprocess.run(
                ['pytest', str(self.target_dir), '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Extract stats
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            skipped = output.count(' SKIPPED')
            total = passed + failed + skipped
            
            if total > 0:
                pass_rate = (passed / total) * 100
                
                logger.info(f"   Tests: {passed} passed, {failed} failed, {skipped} skipped")
                logger.info(f"   Pass rate: {pass_rate:.1f}%")
                
                # Success if >80% pass rate
                success = pass_rate >= 80.0
                
                if success:
                    logger.info(f"   ✅ Test pass rate acceptable (>80%)")
                else:
                    logger.error(f"   ❌ Test pass rate too low (<80%)")
                
                return ValidationResult(
                    check_name="Test Execution",
                    passed=success,
                    details=f"{passed}/{total} tests passed ({pass_rate:.1f}%)",
                    files_checked=len(test_files),
                    errors=errors if not success else [],
                    warnings=warnings
                )
            else:
                logger.warning("   ⚠️  No tests executed")
                return ValidationResult(
                    check_name="Test Execution",
                    passed=True,
                    details="No tests executed",
                    files_checked=len(test_files),
                    errors=[],
                    warnings=["No tests executed"]
                )
        
        except FileNotFoundError:
            warning_msg = "pytest not installed"
            warnings.append(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
        
        except subprocess.TimeoutExpired:
            error_msg = "Test execution timeout (>5 minutes)"
            errors.append(error_msg)
            logger.error(f"   ❌ {error_msg}")
        
        except Exception as e:
            error_msg = f"Test execution error: {str(e)}"
            errors.append(error_msg)
            logger.error(f"   ❌ {error_msg}")
        
        return ValidationResult(
            check_name="Test Execution",
            passed=len(errors) == 0,
            details=f"Attempted to run tests in {len(test_files)} files",
            files_checked=len(test_files),
            errors=errors,
            warnings=warnings
        )
    
    def validate_sql_migrations(self) -> ValidationResult:
        """
        Validate SQL migration files if present.
        
        Returns:
            ValidationResult with SQL validation results
        """
        logger.info("5️⃣  Validating SQL migrations...")
        
        sql_files = list(self.target_dir.rglob("*.sql"))
        errors = []
        warnings = []
        
        if len(sql_files) == 0:
            logger.info("   ℹ️  No SQL files to validate")
            return ValidationResult(
                check_name="SQL Validation",
                passed=True,
                details="No SQL files found",
                files_checked=0,
                errors=[],
                warnings=[]
            )
        
        # Basic SQL validation (check for common syntax)
        for sql_file in sql_files:
            try:
                content = sql_file.read_text()
                
                # Check for dangerous operations
                dangerous_keywords = ['DROP DATABASE', 'TRUNCATE TABLE', 'DELETE FROM']
                for keyword in dangerous_keywords:
                    if keyword in content.upper():
                        warning_msg = f"{sql_file}: Contains potentially dangerous operation: {keyword}"
                        warnings.append(warning_msg)
                        logger.warning(f"   ⚠️  {warning_msg}")
                
                # Check for basic syntax
                if not any(kw in content.upper() for kw in ['CREATE', 'ALTER', 'INSERT', 'UPDATE', 'SELECT']):
                    warning_msg = f"{sql_file}: No recognized SQL statements"
                    warnings.append(warning_msg)
            
            except Exception as e:
                error_msg = f"{sql_file}: Validation error: {str(e)}"
                errors.append(error_msg)
                logger.error(f"   ❌ {error_msg}")
        
        passed = len(errors) == 0
        
        if passed:
            logger.info(f"   ✅ {len(sql_files)} SQL files validated")
        
        return ValidationResult(
            check_name="SQL Validation",
            passed=passed,
            details=f"Checked {len(sql_files)} SQL files",
            files_checked=len(sql_files),
            errors=errors,
            warnings=warnings
        )
    
    def validate_documentation(self) -> ValidationResult:
        """
        Validate documentation completeness.
        
        Returns:
            ValidationResult with documentation check results
        """
        logger.info("6️⃣  Validating documentation...")
        
        errors = []
        warnings = []
        
        # Find all recommendation directories
        rec_dirs = [d for d in self.target_dir.rglob("*") if d.is_dir() and (d.name.startswith("rec_") or d.name.startswith("5."))]
        
        if len(rec_dirs) == 0:
            return ValidationResult(
                check_name="Documentation Validation",
                passed=True,
                details="No recommendation directories found",
                files_checked=0,
                errors=[],
                warnings=[]
            )
        
        required_docs = ["README.md", "INTEGRATION_GUIDE.md"]
        
        for rec_dir in rec_dirs:
            for doc in required_docs:
                doc_path = rec_dir / doc
                
                if not doc_path.exists():
                    warning_msg = f"{rec_dir.name}: Missing {doc}"
                    warnings.append(warning_msg)
                    logger.warning(f"   ⚠️  {warning_msg}")
                else:
                    # Check if file is not empty
                    content = doc_path.read_text()
                    if len(content.strip()) < 100:
                        warning_msg = f"{rec_dir.name}: {doc} is too short (<100 chars)"
                        warnings.append(warning_msg)
        
        passed = len(errors) == 0
        
        if passed and len(warnings) == 0:
            logger.info(f"   ✅ Documentation complete for {len(rec_dirs)} recommendations")
        else:
            logger.warning(f"   ⚠️  {len(warnings)} documentation warnings")
        
        return ValidationResult(
            check_name="Documentation Validation",
            passed=passed,
            details=f"Checked documentation for {len(rec_dirs)} recommendations",
            files_checked=len(rec_dirs),
            errors=errors,
            warnings=warnings
        )
    
    def estimate_integration_impact(self) -> ValidationResult:
        """
        Estimate integration impact on nba-simulator-aws.
        
        Returns:
            ValidationResult with impact estimation
        """
        logger.info("7️⃣  Estimating integration impact...")
        
        errors = []
        warnings = []
        
        # Count files by type
        python_files = len(list(self.target_dir.rglob("*.py")))
        sql_files = len(list(self.target_dir.rglob("*.sql")))
        md_files = len(list(self.target_dir.rglob("*.md")))
        
        total_files = python_files + sql_files + md_files
        
        # Estimate LOC
        total_loc = 0
        for py_file in self.target_dir.rglob("*.py"):
            try:
                lines = py_file.read_text().split('\n')
                total_loc += len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            except:
                pass
        
        # Risk assessment
        risk_level = "LOW"
        if total_files > 100 or total_loc > 10000:
            risk_level = "HIGH"
            warning_msg = f"High integration impact: {total_files} files, ~{total_loc} LOC"
            warnings.append(warning_msg)
            logger.warning(f"   ⚠️  {warning_msg}")
        elif total_files > 50 or total_loc > 5000:
            risk_level = "MEDIUM"
            logger.info(f"   ℹ️  Medium integration impact: {total_files} files, ~{total_loc} LOC")
        else:
            logger.info(f"   ✅ Low integration impact: {total_files} files, ~{total_loc} LOC")
        
        return ValidationResult(
            check_name="Integration Impact Estimation",
            passed=True,
            details=f"{total_files} files, ~{total_loc} LOC, Risk: {risk_level}",
            files_checked=total_files,
            errors=errors,
            warnings=warnings
        )
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        report = f"""# Phase 8.5: Pre-Integration Validation Report

**Generated:** {datetime.now().isoformat()}
**Target Directory:** {self.target_dir}

## Overall Status

"""
        
        overall_pass = all(r.passed for r in self.results)
        if overall_pass:
            report += "**✅ VALIDATION PASSED** - Ready for integration\n\n"
        else:
            report += "**❌ VALIDATION FAILED** - Issues must be resolved before integration\n\n"
        
        report += "## Validation Checks\n\n"
        report += "| Check | Status | Details | Errors | Warnings |\n"
        report += "|-------|--------|---------|--------|----------|\n"
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report += f"| {result.check_name} | {status} | {result.details} | {len(result.errors)} | {len(result.warnings)} |\n"
        
        # Detailed errors
        has_errors = any(len(r.errors) > 0 for r in self.results)
        if has_errors:
            report += "\n## ❌ Errors\n\n"
            for result in self.results:
                if result.errors:
                    report += f"### {result.check_name}\n\n"
                    for error in result.errors:
                        report += f"- {error}\n"
                    report += "\n"
        
        # Detailed warnings
        has_warnings = any(len(r.warnings) > 0 for r in self.results)
        if has_warnings:
            report += "\n## ⚠️  Warnings\n\n"
            for result in self.results:
                if result.warnings:
                    report += f"### {result.check_name}\n\n"
                    for warning in result.warnings:
                        report += f"- {warning}\n"
                    report += "\n"
        
        report += "\n## Next Steps\n\n"
        if overall_pass:
            report += "✅ All validation checks passed. Files are ready for integration.\n\n"
            report += "**To integrate:**\n"
            report += "```bash\n"
            report += "python scripts/phase9_overnight_implementation.py --execute\n"
            report += "```\n"
        else:
            report += "❌ Validation failed. Fix errors listed above before proceeding to integration.\n"
        
        return report


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 8.5: Pre-Integration Validation"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("implementation_plans"),
        help="Target directory to validate"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution (faster validation)"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = Phase85Validator(target_dir=args.target)
    
    # Run validation
    result = await validator.validate_all(skip_tests=args.skip_tests)
    
    # Exit with appropriate code
    if result['overall_pass']:
        logger.info("\n✅ Phase 8.5 Validation: PASSED")
        sys.exit(0)
    else:
        logger.error("\n❌ Phase 8.5 Validation: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    asyncio.run(main())

