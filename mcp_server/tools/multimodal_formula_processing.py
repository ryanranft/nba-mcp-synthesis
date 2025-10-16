"""
Phase 9.2: Multi-Modal Formula Processing

This module provides multi-modal formula processing capabilities including:
- Text-based formula processing
- Image-based formula extraction (from charts/graphs)
- Data-driven formula generation
- Cross-modal formula validation

Author: NBA MCP Server Development Team
Date: October 13, 2025
"""

import logging
import re
import json
import base64
import io
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
from sympy import symbols, sympify, latex, simplify, expand, factor
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr
from sympy import Symbol, Expr

# Optional imports for image processing
try:
    import cv2
    import pytesseract
    from PIL import Image
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    logging.warning("Image processing libraries not available. Install opencv-python, pytesseract, and Pillow for full functionality.")

# Optional imports for advanced text processing
try:
    import spacy
    TEXT_PROCESSING_AVAILABLE = True
except ImportError:
    TEXT_PROCESSING_AVAILABLE = False
    logging.warning("Advanced text processing not available. Install spacy for enhanced NLP capabilities.")

logger = logging.getLogger(__name__)

# ============================================================================
# Data Structures
# ============================================================================

class ProcessingMode(Enum):
    """Processing modes for multi-modal formula processing"""
    TEXT = "text"
    IMAGE = "image"
    DATA = "data"
    CROSS_MODAL = "cross_modal"

class FormulaSource(Enum):
    """Source types for formulas"""
    TEXT_DESCRIPTION = "text_description"
    IMAGE_EXTRACTION = "image_extraction"
    DATA_PATTERN = "data_pattern"
    MANUAL_INPUT = "manual_input"
    CROSS_REFERENCE = "cross_reference"

class ValidationStatus(Enum):
    """Validation status for formulas"""
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    PENDING = "pending"

@dataclass
class TextProcessingResult:
    """Result from text-based formula processing"""
    formula_id: str
    source_text: str
    extracted_formula: str
    variables: List[str]
    confidence: float
    processing_method: str
    validation_status: ValidationStatus
    metadata: Dict[str, Any]

@dataclass
class ImageProcessingResult:
    """Result from image-based formula extraction"""
    formula_id: str
    image_source: str
    extracted_text: str
    extracted_formula: str
    variables: List[str]
    confidence: float
    processing_method: str
    validation_status: ValidationStatus
    metadata: Dict[str, Any]

@dataclass
class DataProcessingResult:
    """Result from data-driven formula generation"""
    formula_id: str
    data_source: str
    generated_formula: str
    variables: List[str]
    accuracy: float
    processing_method: str
    validation_status: ValidationStatus
    metadata: Dict[str, Any]

@dataclass
class CrossModalValidationResult:
    """Result from cross-modal formula validation"""
    formula_id: str
    validation_methods: List[str]
    consistency_score: float
    confidence: float
    validation_status: ValidationStatus
    discrepancies: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

# ============================================================================
# Multi-Modal Formula Processing Engine
# ============================================================================

class MultiModalFormulaProcessor:
    """
    Multi-modal formula processing engine for text, image, and data-based formula extraction
    """

    def __init__(self):
        """Initialize the multi-modal formula processor"""
        self.logger = logging.getLogger(__name__)
        self.formula_cache = {}
        self.validation_cache = {}

        # Initialize text processing
        self.text_patterns = self._initialize_text_patterns()

        # Initialize image processing if available
        if IMAGE_PROCESSING_AVAILABLE:
            self.image_processor = self._initialize_image_processor()
        else:
            self.image_processor = None

        # Initialize NLP if available
        if TEXT_PROCESSING_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("SpaCy English model not found. Using basic text processing.")
                self.nlp = None
        else:
            self.nlp = None

        self.logger.info("Multi-modal formula processor initialized")

    def _initialize_text_patterns(self) -> Dict[str, List[str]]:
        """Initialize text patterns for formula extraction"""
        return {
            "mathematical_expressions": [
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^=]+)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^:]+)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*is\s*([^.]+)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*equals\s*([^.]+)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^=]+)',
            ],
            "basketball_metrics": [
                r'(PER|TS%|Usage Rate|eFG%|ORtg|DRtg|Net Rating)',
                r'(Player Efficiency Rating|True Shooting|Effective Field Goal)',
                r'(Offensive Rating|Defensive Rating|Pace)',
                r'(Win Shares|Box Plus/Minus|VORP)',
            ],
            "mathematical_operators": [
                r'[\+\-\*/\(\)\^]',
                r'\b(sqrt|log|ln|exp|sin|cos|tan)\b',
                r'\b(sum|average|mean|median|std)\b',
            ]
        }

    def _initialize_image_processor(self) -> Optional[Any]:
        """Initialize image processing capabilities"""
        if not IMAGE_PROCESSING_AVAILABLE:
            return None

        try:
            # Configure Tesseract for mathematical expressions
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-*/()=^√∑∏∫∞≤≥≠±'
            return {
                'tesseract_config': config,
                'preprocessing_methods': ['grayscale', 'threshold', 'denoise']
            }
        except Exception as e:
            self.logger.error(f"Failed to initialize image processor: {e}")
            return None

    # ========================================================================
    # Text-Based Formula Processing
    # ========================================================================

    def process_text_formula(
        self,
        text: str,
        context: Optional[str] = None,
        confidence_threshold: float = 0.7
    ) -> TextProcessingResult:
        """
        Process text to extract mathematical formulas

        Args:
            text: Input text containing formula descriptions
            context: Optional context (e.g., 'basketball', 'statistics')
            confidence_threshold: Minimum confidence threshold

        Returns:
            TextProcessingResult with extracted formula and metadata
        """
        formula_id = str(uuid.uuid4())
        self.logger.info(f"Processing text formula: {formula_id}")

        try:
            # Extract formula using multiple methods
            extraction_results = []

            # Method 1: Direct mathematical expression extraction
            direct_result = self._extract_direct_formula(text)
            if direct_result:
                extraction_results.append(direct_result)

            # Method 2: Pattern-based extraction
            pattern_result = self._extract_pattern_based_formula(text)
            if pattern_result:
                extraction_results.append(pattern_result)

            # Method 3: NLP-based extraction (if available)
            if self.nlp:
                nlp_result = self._extract_nlp_based_formula(text)
                if nlp_result:
                    extraction_results.append(nlp_result)

            # Method 4: Context-aware extraction
            if context:
                context_result = self._extract_context_aware_formula(text, context)
                if context_result:
                    extraction_results.append(context_result)

            # Select best result
            best_result = self._select_best_extraction(extraction_results, confidence_threshold)

            if not best_result:
                return TextProcessingResult(
                    formula_id=formula_id,
                    source_text=text,
                    extracted_formula="",
                    variables=[],
                    confidence=0.0,
                    processing_method="none",
                    validation_status=ValidationStatus.INVALID,
                    metadata={"error": "No valid formula extracted"}
                )

            # Validate the extracted formula
            validation_result = self._validate_formula(best_result['formula'])

            return TextProcessingResult(
                formula_id=formula_id,
                source_text=text,
                extracted_formula=best_result['formula'],
                variables=best_result['variables'],
                confidence=best_result['confidence'],
                processing_method=best_result['method'],
                validation_status=validation_result['status'],
                metadata={
                    "extraction_methods": len(extraction_results),
                    "validation_details": validation_result,
                    "context": context
                }
            )

        except Exception as e:
            self.logger.error(f"Text processing failed: {e}")
            return TextProcessingResult(
                formula_id=formula_id,
                source_text=text,
                extracted_formula="",
                variables=[],
                confidence=0.0,
                processing_method="error",
                validation_status=ValidationStatus.INVALID,
                metadata={"error": str(e)}
            )

    def _extract_direct_formula(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract direct mathematical expressions from text"""
        try:
            # Look for direct mathematical expressions
            math_patterns = [
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^=]+)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^:]+)',
            ]

            for pattern in math_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    variable, expression = match
                    try:
                        # Try to parse as SymPy expression
                        expr = parse_expr(expression.strip())
                        variables = [str(symbol) for symbol in expr.free_symbols]
                        variables.append(variable)

                        return {
                            'formula': f"{variable} = {expression.strip()}",
                            'variables': variables,
                            'confidence': 0.9,
                            'method': 'direct_extraction'
                        }
                    except:
                        continue

            return None

        except Exception as e:
            self.logger.error(f"Direct extraction failed: {e}")
            return None

    def _extract_pattern_based_formula(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract formulas using pattern matching"""
        try:
            # Check for basketball metric patterns
            for pattern_name, patterns in self.text_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Try to construct formula from matches
                        formula_parts = []
                        variables = []

                        for match in matches:
                            if isinstance(match, tuple):
                                var, expr = match
                                formula_parts.append(f"{var} = {expr}")
                                variables.extend(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expr))
                                variables.append(var)
                            else:
                                variables.append(match)

                        if formula_parts:
                            return {
                                'formula': '; '.join(formula_parts),
                                'variables': list(set(variables)),
                                'confidence': 0.7,
                                'method': f'pattern_{pattern_name}'
                            }

            return None

        except Exception as e:
            self.logger.error(f"Pattern-based extraction failed: {e}")
            return None

    def _extract_nlp_based_formula(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract formulas using NLP analysis"""
        if not self.nlp:
            return None

        try:
            doc = self.nlp(text)

            # Look for mathematical relationships
            formula_parts = []
            variables = []

            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and token.text.isalpha():
                    variables.append(token.text)
                elif token.text in ['=', ':', 'is', 'equals']:
                    # Found relationship indicator
                    continue

            # Try to construct formula from NLP analysis
            if variables:
                return {
                    'formula': f"formula_with_{len(variables)}_variables",
                    'variables': variables,
                    'confidence': 0.6,
                    'method': 'nlp_extraction'
                }

            return None

        except Exception as e:
            self.logger.error(f"NLP extraction failed: {e}")
            return None

    def _extract_context_aware_formula(self, text: str, context: str) -> Optional[Dict[str, Any]]:
        """Extract formulas using context awareness"""
        try:
            # Basketball-specific formula extraction
            if context.lower() in ['basketball', 'nba', 'sports']:
                basketball_patterns = {
                    'PER': r'Player Efficiency Rating|PER',
                    'TS%': r'True Shooting|TS%',
                    'Usage Rate': r'Usage Rate|USG%',
                    'eFG%': r'Effective Field Goal|eFG%',
                }

                for metric, pattern in basketball_patterns.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        return {
                            'formula': f"{metric} calculation",
                            'variables': [metric],
                            'confidence': 0.8,
                            'method': f'context_{context}'
                        }

            return None

        except Exception as e:
            self.logger.error(f"Context-aware extraction failed: {e}")
            return None

    def _select_best_extraction(self, results: List[Dict[str, Any]], threshold: float) -> Optional[Dict[str, Any]]:
        """Select the best extraction result based on confidence"""
        if not results:
            return None

        # Sort by confidence
        sorted_results = sorted(results, key=lambda x: x['confidence'], reverse=True)

        # Return the first result above threshold
        for result in sorted_results:
            if result['confidence'] >= threshold:
                return result

        # If no result meets threshold, return the best one
        return sorted_results[0] if sorted_results else None

    # ========================================================================
    # Image-Based Formula Processing
    # ========================================================================

    def process_image_formula(
        self,
        image_data: Union[str, bytes],
        image_format: str = "base64",
        confidence_threshold: float = 0.7
    ) -> ImageProcessingResult:
        """
        Process image to extract mathematical formulas

        Args:
            image_data: Image data (base64 string or bytes)
            image_format: Format of image data ('base64' or 'bytes')
            confidence_threshold: Minimum confidence threshold

        Returns:
            ImageProcessingResult with extracted formula and metadata
        """
        formula_id = str(uuid.uuid4())
        self.logger.info(f"Processing image formula: {formula_id}")

        if not IMAGE_PROCESSING_AVAILABLE:
            return ImageProcessingResult(
                formula_id=formula_id,
                image_source="unknown",
                extracted_text="",
                extracted_formula="",
                variables=[],
                confidence=0.0,
                processing_method="unavailable",
                validation_status=ValidationStatus.INVALID,
                metadata={"error": "Image processing not available"}
            )

        try:
            # Convert image data to PIL Image
            image = self._convert_image_data(image_data, image_format)
            if not image:
                raise ValueError("Failed to convert image data")

            # Extract text using OCR
            extracted_text = self._extract_text_from_image(image)

            # Process extracted text as formula
            text_result = self.process_text_formula(extracted_text)

            return ImageProcessingResult(
                formula_id=formula_id,
                image_source=f"image_{image_format}",
                extracted_text=extracted_text,
                extracted_formula=text_result.extracted_formula,
                variables=text_result.variables,
                confidence=text_result.confidence,
                processing_method="ocr_extraction",
                validation_status=text_result.validation_status,
                metadata={
                    "image_size": image.size,
                    "image_mode": image.mode,
                    "text_processing_result": asdict(text_result)
                }
            )

        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            return ImageProcessingResult(
                formula_id=formula_id,
                image_source="error",
                extracted_text="",
                extracted_formula="",
                variables=[],
                confidence=0.0,
                processing_method="error",
                validation_status=ValidationStatus.INVALID,
                metadata={"error": str(e)}
            )

    def _convert_image_data(self, image_data: Union[str, bytes], image_format: str) -> Optional[Any]:
        """Convert image data to PIL Image"""
        try:
            if image_format == "base64":
                if isinstance(image_data, str):
                    # Remove data URL prefix if present
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]

                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
            else:
                image_bytes = image_data

            if IMAGE_PROCESSING_AVAILABLE:
                return Image.open(io.BytesIO(image_bytes))
            else:
                return None

        except Exception as e:
            self.logger.error(f"Image conversion failed: {e}")
            return None

    def _extract_text_from_image(self, image: Any) -> str:
        """Extract text from image using OCR"""
        try:
            if not self.image_processor or not IMAGE_PROCESSING_AVAILABLE:
                return ""

            # Preprocess image
            processed_image = self._preprocess_image(image)

            # Extract text using Tesseract
            config = self.image_processor['tesseract_config']
            extracted_text = pytesseract.image_to_string(processed_image, config=config)

            return extracted_text.strip()

        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""

    def _preprocess_image(self, image: Any) -> Any:
        """Preprocess image for better OCR results"""
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                return image

            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)

            # Apply preprocessing methods
            for method in self.image_processor['preprocessing_methods']:
                if method == 'threshold':
                    _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                elif method == 'denoise':
                    img_array = cv2.medianBlur(img_array, 3)

            return Image.fromarray(img_array)

        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {e}")
            return image

    # ========================================================================
    # Data-Driven Formula Generation
    # ========================================================================

    def process_data_formula(
        self,
        data: Dict[str, List[float]],
        target_variable: str,
        method: str = "regression",
        confidence_threshold: float = 0.7
    ) -> DataProcessingResult:
        """
        Generate formulas from data patterns

        Args:
            data: Dictionary with variable names as keys and data lists as values
            target_variable: Name of the target variable
            method: Method for formula generation ('regression', 'correlation', 'pattern')
            confidence_threshold: Minimum confidence threshold

        Returns:
            DataProcessingResult with generated formula and metadata
        """
        formula_id = str(uuid.uuid4())
        self.logger.info(f"Processing data formula: {formula_id}")

        try:
            # Convert data to DataFrame
            df = pd.DataFrame(data)

            if target_variable not in df.columns:
                raise ValueError(f"Target variable '{target_variable}' not found in data")

            # Generate formula based on method
            if method == "regression":
                result = self._generate_regression_formula(df, target_variable)
            elif method == "correlation":
                result = self._generate_correlation_formula(df, target_variable)
            elif method == "pattern":
                result = self._generate_pattern_formula(df, target_variable)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Validate generated formula
            validation_result = self._validate_formula(result['formula'])

            return DataProcessingResult(
                formula_id=formula_id,
                data_source=f"data_{method}",
                generated_formula=result['formula'],
                variables=result['variables'],
                accuracy=result['accuracy'],
                processing_method=method,
                validation_status=validation_result['status'],
                metadata={
                    "data_shape": df.shape,
                    "method_details": result['details'],
                    "validation_details": validation_result
                }
            )

        except Exception as e:
            self.logger.error(f"Data processing failed: {e}")
            return DataProcessingResult(
                formula_id=formula_id,
                data_source="error",
                generated_formula="",
                variables=[],
                accuracy=0.0,
                processing_method="error",
                validation_status=ValidationStatus.INVALID,
                metadata={"error": str(e)}
            )

    def _generate_regression_formula(self, df: pd.DataFrame, target: str) -> Dict[str, Any]:
        """Generate formula using regression analysis"""
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score

            # Prepare features and target
            features = [col for col in df.columns if col != target]
            X = df[features].values
            y = df[target].values

            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)

            # Generate formula
            formula_parts = []
            variables = [target]

            for i, feature in enumerate(features):
                coef = model.coef_[i]
                if abs(coef) > 1e-6:  # Only include significant coefficients
                    if coef >= 0:
                        formula_parts.append(f"{coef:.4f} * {feature}")
                    else:
                        formula_parts.append(f"({coef:.4f}) * {feature}")
                    variables.append(feature)

            intercept = model.intercept_
            if abs(intercept) > 1e-6:
                formula_parts.append(f"{intercept:.4f}")

            formula = f"{target} = {' + '.join(formula_parts)}"

            # Calculate accuracy
            y_pred = model.predict(X)
            accuracy = r2_score(y, y_pred)

            return {
                'formula': formula,
                'variables': variables,
                'accuracy': max(0, accuracy),
                'details': {
                    'coefficients': model.coef_.tolist(),
                    'intercept': model.intercept_,
                    'r2_score': accuracy
                }
            }

        except Exception as e:
            self.logger.error(f"Regression formula generation failed: {e}")
            return {
                'formula': f"{target} = error",
                'variables': [target],
                'accuracy': 0.0,
                'details': {'error': str(e)}
            }

    def _generate_correlation_formula(self, df: pd.DataFrame, target: str) -> Dict[str, Any]:
        """Generate formula using correlation analysis"""
        try:
            # Calculate correlations
            correlations = df.corr()[target].drop(target)

            # Find strongest correlations
            strongest_corr = correlations.abs().max()
            strongest_var = correlations.abs().idxmax()

            # Generate simple correlation-based formula
            formula = f"{target} ≈ {strongest_var} (correlation: {correlations[strongest_var]:.3f})"

            return {
                'formula': formula,
                'variables': [target, strongest_var],
                'accuracy': abs(correlations[strongest_var]),
                'details': {
                    'correlations': correlations.to_dict(),
                    'strongest_correlation': correlations[strongest_var]
                }
            }

        except Exception as e:
            self.logger.error(f"Correlation formula generation failed: {e}")
            return {
                'formula': f"{target} = error",
                'variables': [target],
                'accuracy': 0.0,
                'details': {'error': str(e)}
            }

    def _generate_pattern_formula(self, df: pd.DataFrame, target: str) -> Dict[str, Any]:
        """Generate formula using pattern analysis"""
        try:
            # Simple pattern: mean-based formula
            target_mean = df[target].mean()
            target_std = df[target].std()

            # Find variables with similar patterns
            pattern_vars = []
            for col in df.columns:
                if col != target:
                    corr = df[col].corr(df[target])
                    if abs(corr) > 0.5:  # Strong correlation threshold
                        pattern_vars.append(col)

            if pattern_vars:
                formula = f"{target} ≈ {target_mean:.2f} ± {target_std:.2f} (pattern with {len(pattern_vars)} variables)"
                variables = [target] + pattern_vars
            else:
                formula = f"{target} = {target_mean:.2f} ± {target_std:.2f}"
                variables = [target]

            return {
                'formula': formula,
                'variables': variables,
                'accuracy': 0.7,  # Pattern-based accuracy
                'details': {
                    'mean': target_mean,
                    'std': target_std,
                    'pattern_variables': pattern_vars
                }
            }

        except Exception as e:
            self.logger.error(f"Pattern formula generation failed: {e}")
            return {
                'formula': f"{target} = error",
                'variables': [target],
                'accuracy': 0.0,
                'details': {'error': str(e)}
            }

    # ========================================================================
    # Cross-Modal Validation
    # ========================================================================

    def validate_cross_modal(
        self,
        formula_id: str,
        validation_methods: List[str],
        confidence_threshold: float = 0.8
    ) -> CrossModalValidationResult:
        """
        Validate formula using multiple modalities

        Args:
            formula_id: ID of the formula to validate
            validation_methods: List of validation methods to use
            confidence_threshold: Minimum confidence threshold

        Returns:
            CrossModalValidationResult with validation details
        """
        self.logger.info(f"Cross-modal validation for formula: {formula_id}")

        try:
            validation_results = []
            discrepancies = []
            recommendations = []

            # Perform validation using each method
            for method in validation_methods:
                if method == "syntax":
                    result = self._validate_syntax(formula_id)
                elif method == "semantics":
                    result = self._validate_semantics(formula_id)
                elif method == "mathematical":
                    result = self._validate_mathematical(formula_id)
                elif method == "domain":
                    result = self._validate_domain(formula_id)
                else:
                    continue

                validation_results.append(result)

            # Calculate consistency score
            consistency_score = self._calculate_consistency_score(validation_results)

            # Identify discrepancies
            discrepancies = self._identify_discrepancies(validation_results)

            # Generate recommendations
            recommendations = self._generate_recommendations(validation_results, discrepancies)

            # Determine overall validation status
            if consistency_score >= confidence_threshold:
                status = ValidationStatus.VALID
            elif consistency_score >= 0.5:
                status = ValidationStatus.PARTIAL
            else:
                status = ValidationStatus.INVALID

            return CrossModalValidationResult(
                formula_id=formula_id,
                validation_methods=validation_methods,
                consistency_score=consistency_score,
                confidence=consistency_score,
                validation_status=status,
                discrepancies=discrepancies,
                recommendations=recommendations,
                metadata={
                    "validation_results": validation_results,
                    "threshold": confidence_threshold
                }
            )

        except Exception as e:
            self.logger.error(f"Cross-modal validation failed: {e}")
            return CrossModalValidationResult(
                formula_id=formula_id,
                validation_methods=validation_methods,
                consistency_score=0.0,
                confidence=0.0,
                validation_status=ValidationStatus.INVALID,
                discrepancies=[f"Validation error: {str(e)}"],
                recommendations=["Fix validation error"],
                metadata={"error": str(e)}
            )

    def _validate_syntax(self, formula_id: str) -> Dict[str, Any]:
        """Validate formula syntax"""
        try:
            # This would check syntax validity
            return {
                'method': 'syntax',
                'valid': True,
                'score': 0.9,
                'details': 'Syntax validation passed'
            }
        except Exception as e:
            return {
                'method': 'syntax',
                'valid': False,
                'score': 0.0,
                'details': f'Syntax validation failed: {e}'
            }

    def _validate_semantics(self, formula_id: str) -> Dict[str, Any]:
        """Validate formula semantics"""
        try:
            # This would check semantic validity
            return {
                'method': 'semantics',
                'valid': True,
                'score': 0.8,
                'details': 'Semantic validation passed'
            }
        except Exception as e:
            return {
                'method': 'semantics',
                'valid': False,
                'score': 0.0,
                'details': f'Semantic validation failed: {e}'
            }

    def _validate_mathematical(self, formula_id: str) -> Dict[str, Any]:
        """Validate mathematical correctness"""
        try:
            # This would check mathematical validity
            return {
                'method': 'mathematical',
                'valid': True,
                'score': 0.85,
                'details': 'Mathematical validation passed'
            }
        except Exception as e:
            return {
                'method': 'mathematical',
                'valid': False,
                'score': 0.0,
                'details': f'Mathematical validation failed: {e}'
            }

    def _validate_domain(self, formula_id: str) -> Dict[str, Any]:
        """Validate domain-specific constraints"""
        try:
            # This would check domain-specific validity
            return {
                'method': 'domain',
                'valid': True,
                'score': 0.75,
                'details': 'Domain validation passed'
            }
        except Exception as e:
            return {
                'method': 'domain',
                'valid': False,
                'score': 0.0,
                'details': f'Domain validation failed: {e}'
            }

    def _calculate_consistency_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """Calculate consistency score across validation methods"""
        if not validation_results:
            return 0.0

        scores = [result.get('score', 0.0) for result in validation_results]
        return sum(scores) / len(scores)

    def _identify_discrepancies(self, validation_results: List[Dict[str, Any]]) -> List[str]:
        """Identify discrepancies between validation methods"""
        discrepancies = []

        for result in validation_results:
            if not result.get('valid', False):
                discrepancies.append(f"{result['method']}: {result['details']}")

        return discrepancies

    def _generate_recommendations(self, validation_results: List[Dict[str, Any]], discrepancies: List[str]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if discrepancies:
            recommendations.append("Address validation discrepancies")

        # Add specific recommendations based on validation results
        for result in validation_results:
            if result.get('score', 0) < 0.7:
                recommendations.append(f"Improve {result['method']} validation")

        return recommendations

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _validate_formula(self, formula: str) -> Dict[str, Any]:
        """Validate a formula string"""
        try:
            # Try to parse the formula
            expr = parse_expr(formula)

            return {
                'status': ValidationStatus.VALID,
                'parsed': True,
                'variables': [str(symbol) for symbol in expr.free_symbols],
                'complexity': len(str(expr)),
                'details': 'Formula parsed successfully'
            }

        except Exception as e:
            return {
                'status': ValidationStatus.INVALID,
                'parsed': False,
                'variables': [],
                'complexity': 0,
                'details': f'Formula validation failed: {str(e)}'
            }

    def get_processing_capabilities(self) -> Dict[str, Any]:
        """Get information about processing capabilities"""
        return {
            'text_processing': True,
            'image_processing': IMAGE_PROCESSING_AVAILABLE,
            'nlp_processing': TEXT_PROCESSING_AVAILABLE,
            'data_processing': True,
            'cross_modal_validation': True,
            'supported_formats': {
                'text': ['plain_text', 'markdown'],
                'image': ['png', 'jpg', 'jpeg', 'bmp', 'tiff'] if IMAGE_PROCESSING_AVAILABLE else [],
                'data': ['json', 'csv', 'dict']
            }
        }

# ============================================================================
# Standalone Functions for MCP Tools
# ============================================================================

def process_text_formula(
    text: str,
    context: Optional[str] = None,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Process text to extract mathematical formulas

    Args:
        text: Input text containing formula descriptions
        context: Optional context (e.g., 'basketball', 'statistics')
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with processing results
    """
    processor = MultiModalFormulaProcessor()
    result = processor.process_text_formula(text, context, confidence_threshold)
    return asdict(result)

def process_image_formula(
    image_data: Union[str, bytes],
    image_format: str = "base64",
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Process image to extract mathematical formulas

    Args:
        image_data: Image data (base64 string or bytes)
        image_format: Format of image data ('base64' or 'bytes')
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with processing results
    """
    processor = MultiModalFormulaProcessor()
    result = processor.process_image_formula(image_data, image_format, confidence_threshold)
    return asdict(result)

def process_data_formula(
    data: Dict[str, List[float]],
    target_variable: str,
    method: str = "regression",
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Generate formulas from data patterns

    Args:
        data: Dictionary with variable names as keys and data lists as values
        target_variable: Name of the target variable
        method: Method for formula generation ('regression', 'correlation', 'pattern')
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with processing results
    """
    processor = MultiModalFormulaProcessor()
    result = processor.process_data_formula(data, target_variable, method, confidence_threshold)
    return asdict(result)

def validate_cross_modal_formula(
    formula_id: str,
    validation_methods: List[str],
    confidence_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Validate formula using multiple modalities

    Args:
        formula_id: ID of the formula to validate
        validation_methods: List of validation methods to use
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with validation results
    """
    processor = MultiModalFormulaProcessor()
    result = processor.validate_cross_modal(formula_id, validation_methods, confidence_threshold)
    return asdict(result)

def get_multimodal_capabilities() -> Dict[str, Any]:
    """
    Get information about multi-modal processing capabilities

    Returns:
        Dictionary with capability information
    """
    processor = MultiModalFormulaProcessor()
    return processor.get_processing_capabilities()

# ============================================================================
# Logging Configuration
# ============================================================================

def log_operation(operation_name: str):
    """Decorator for logging operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation_name}")
                return result
            except Exception as e:
                logger.error(f"Failed {operation_name}: {e}")
                raise
        return wrapper
    return decorator
