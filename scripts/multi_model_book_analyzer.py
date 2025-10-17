#!/usr/bin/env python3
"""
Multi-Model Book Analyzer

This module provides ensemble analysis using DeepSeek, Claude (via MCP), and Ollama
with consensus voting to analyze books and generate recommendations.

Features:
- 3-model consensus voting (3/3 = Critical, 2/3 = Important, 1/3 = skip)
- Cost tracking across all models
- Real PDF/EPUB reading via MCP tools
- Async/await support for parallel processing
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from mcp_server.env_helper import get_hierarchical_env

# Import synthesis modules
from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from synthesis.models.ollama_model import OllamaModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Response from a single model"""

    model_name: str
    recommendations: List[Dict[str, Any]]
    cost: float
    tokens_used: int
    processing_time: float
    error: Optional[str] = None


@dataclass
class ConsensusResult:
    """Consensus result from multiple models"""

    unanimous_recommendations: List[Dict[str, Any]]  # 3/3 agreement
    majority_recommendations: List[Dict[str, Any]]  # 2/3 agreement
    total_cost: float
    total_tokens: int
    total_time: float
    model_responses: List[ModelResponse]


class MultiModelBookAnalyzer:
    """Analyzes books using multiple LLMs with consensus voting"""

    def __init__(self, config_path: str = "config/multi_model_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.models = self._initialize_models()
        self.cost_tracker = CostTracker()

    def _load_config(self) -> Dict[str, Any]:
        """Load multi-model configuration"""
        default_config = {
            "models": {
                "deepseek": {
                    "enabled": True,
                    "api_key_env": "DEEPSEEK_API_KEY",
                    "model": "deepseek-chat",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
                "claude": {
                    "enabled": True,
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
                "ollama": {
                    "enabled": True,
                    "model": "llama3.1:70b",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                },
            },
            "consensus": {
                "unanimous_threshold": 3,  # 3/3 models must agree for Critical
                "majority_threshold": 2,  # 2/3 models must agree for Important
                "min_agreement": 1,  # Minimum models for consideration
            },
            "analysis": {
                "max_chunk_size": 50000,  # Characters per chunk
                "overlap_size": 5000,  # Overlap between chunks
                "max_iterations": 5,  # Max recursive iterations
            },
        }

        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # Save default config
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize model instances"""
        models = {}

        if self.config["models"]["deepseek"]["enabled"]:
            try:
                models["deepseek"] = DeepSeekModel(
                    api_key=get_hierarchical_env(
                        self.config["models"]["deepseek"]["api_key_env"],
                        "NBA_MCP_SYNTHESIS",
                        "WORKFLOW",
                    ),
                    model=self.config["models"]["deepseek"]["model"],
                )
                logger.info("✅ DeepSeek model initialized")
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek initialization failed: {e}")

        if self.config["models"]["claude"]["enabled"]:
            try:
                models["claude"] = ClaudeModel()
                logger.info("✅ Claude model initialized")
            except Exception as e:
                logger.warning(f"⚠️ Claude initialization failed: {e}")

        if self.config["models"]["ollama"]["enabled"]:
            try:
                models["ollama"] = OllamaModel(
                    model=self.config["models"]["ollama"]["model"]
                )
                logger.info("✅ Ollama model initialized")
            except Exception as e:
                logger.warning(f"⚠️ Ollama initialization failed: {e}")

        if not models:
            raise RuntimeError(
                "No models could be initialized. Check API keys and configuration."
            )

        return models

    async def analyze_book(
        self, book_data: Dict[str, Any], existing_recommendations: List[Dict] = None
    ) -> ConsensusResult:
        """
        Analyze a book using multiple models with consensus voting

        Args:
            book_data: Book metadata and content
            existing_recommendations: Existing recommendations for context-aware analysis

        Returns:
            ConsensusResult with unanimous and majority recommendations
        """
        logger.info(
            f"🔍 Starting multi-model analysis of: {book_data.get('title', 'Unknown')}"
        )

        # Prepare analysis prompt
        prompt = self._build_analysis_prompt(book_data, existing_recommendations)

        # Run models in parallel
        tasks = []
        for model_name, model in self.models.items():
            task = self._analyze_with_model(model_name, model, prompt, book_data)
            tasks.append(task)

        # Wait for all models to complete
        model_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        valid_responses = []
        for i, response in enumerate(model_responses):
            if isinstance(response, Exception):
                model_name = list(self.models.keys())[i]
                logger.error(f"❌ {model_name} failed: {response}")
                valid_responses.append(
                    ModelResponse(
                        model_name=model_name,
                        recommendations=[],
                        cost=0.0,
                        tokens_used=0,
                        processing_time=0.0,
                        error=str(response),
                    )
                )
            else:
                valid_responses.append(response)

        # Calculate consensus
        consensus = self._calculate_consensus(valid_responses)

        # Update cost tracking
        self.cost_tracker.add_session(consensus.total_cost, consensus.total_tokens)

        logger.info(f"✅ Multi-model analysis complete:")
        logger.info(
            f"   Unanimous (Critical): {len(consensus.unanimous_recommendations)}"
        )
        logger.info(
            f"   Majority (Important): {len(consensus.majority_recommendations)}"
        )
        logger.info(f"   Total cost: ${consensus.total_cost:.2f}")

        return consensus

    async def _analyze_with_model(
        self, model_name: str, model: Any, prompt: str, book_data: Dict
    ) -> ModelResponse:
        """Analyze with a single model"""
        start_time = datetime.now()

        try:
            logger.info(f"🤖 Running {model_name} analysis...")

            # Use synthesis framework for actual API calls
            response = await synthesize_with_mcp_context(
                prompt=prompt,
                context_data={
                    "book_title": book_data.get("title", ""),
                    "book_author": book_data.get("author", ""),
                    "analysis_type": "book_recommendations",
                },
                models=[model_name],  # Use specific model
            )

            # Parse response into recommendations
            recommendations = self._parse_model_response(response, model_name)

            # Calculate cost and tokens
            cost = model.calculate_cost(response.get("tokens_used", 0))
            tokens_used = response.get("tokens_used", 0)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ {model_name} complete: {len(recommendations)} recommendations, ${cost:.2f}"
            )

            return ModelResponse(
                model_name=model_name,
                recommendations=recommendations,
                cost=cost,
                tokens_used=tokens_used,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"❌ {model_name} analysis failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return ModelResponse(
                model_name=model_name,
                recommendations=[],
                cost=0.0,
                tokens_used=0,
                processing_time=processing_time,
                error=str(e),
            )

    def _build_analysis_prompt(
        self, book_data: Dict[str, Any], existing_recommendations: List[Dict] = None
    ) -> str:
        """Build analysis prompt for book recommendations"""

        base_prompt = f"""
You are analyzing the book "{book_data.get('title', 'Unknown')}" by {book_data.get('author', 'Unknown')}
to extract actionable recommendations for the NBA MCP Synthesis and NBA Simulator AWS projects.

Book Context:
- Title: {book_data.get('title', 'Unknown')}
- Author: {book_data.get('author', 'Unknown')}
- Genre: {book_data.get('genre', 'Technical')}
- Pages: {book_data.get('pages', 'Unknown')}

Analysis Focus:
Extract specific, actionable recommendations that can enhance:
1. NBA data collection and processing pipelines
2. Machine learning model development and deployment
3. Statistical analysis and validation frameworks
4. System architecture and scalability
5. Data quality and monitoring systems

For each recommendation, provide:
- Title: Clear, specific recommendation name
- Description: Detailed explanation of what to implement
- Priority: CRITICAL, IMPORTANT, or NICE-TO-HAVE
- Source Chapter: Which chapter/section this comes from
- Time Estimate: Hours required for implementation
- Impact: Expected benefit to the NBA projects
- Status: PENDING (always)

Output Format (JSON):
{{
    "recommendations": [
        {{
            "title": "Specific Recommendation Name",
            "description": "Detailed description of what to implement and why",
            "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
            "source_chapter": "Chapter X: Title",
            "time_estimate": "X hours",
            "impact": "Expected benefit description",
            "status": "PENDING",
            "source_book_id": "{book_data.get('id', 'unknown')}"
        }}
    ]
}}
"""

        if existing_recommendations:
            existing_context = "\n\nExisting Recommendations (avoid duplicates):\n"
            for rec in existing_recommendations[:10]:  # Limit context
                existing_context += f"- {rec.get('title', 'Unknown')}: {rec.get('description', '')[:100]}...\n"

            base_prompt += existing_context
            base_prompt += "\n\nFocus on NEW recommendations that are significantly different from the above."

        return base_prompt

    def _parse_model_response(
        self, response: Dict[str, Any], model_name: str
    ) -> List[Dict[str, Any]]:
        """Parse model response into structured recommendations"""
        try:
            # Extract JSON from response
            content = response.get("content", "")

            # Try to find JSON in the response
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                recommendations = parsed.get("recommendations", [])

                # Validate and clean recommendations
                cleaned_recs = []
                for rec in recommendations:
                    if self._validate_recommendation(rec):
                        cleaned_recs.append(rec)

                return cleaned_recs
            else:
                logger.warning(f"⚠️ {model_name}: No JSON found in response")
                return []

        except Exception as e:
            logger.error(f"❌ {model_name}: Failed to parse response: {e}")
            return []

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate recommendation has required fields"""
        required_fields = [
            "title",
            "description",
            "priority",
            "source_chapter",
            "time_estimate",
            "impact",
        ]
        return all(field in rec and rec[field] for field in required_fields)

    def _calculate_consensus(
        self, model_responses: List[ModelResponse]
    ) -> ConsensusResult:
        """Calculate consensus from multiple model responses"""

        # Collect all recommendations with model votes
        recommendation_votes = {}

        for response in model_responses:
            if response.error:
                continue

            for rec in response.recommendations:
                # Create a key based on title similarity
                key = self._get_recommendation_key(rec)

                if key not in recommendation_votes:
                    recommendation_votes[key] = {
                        "recommendation": rec,
                        "votes": [],
                        "models": [],
                    }

                recommendation_votes[key]["votes"].append(rec)
                recommendation_votes[key]["models"].append(response.model_name)

        # Calculate consensus
        unanimous_recommendations = []
        majority_recommendations = []

        for key, vote_data in recommendation_votes.items():
            vote_count = len(vote_data["votes"])
            models_count = len(self.models)

            if vote_count >= self.config["consensus"]["unanimous_threshold"]:
                # All models agree - Critical priority
                best_rec = self._merge_recommendations(vote_data["votes"])
                best_rec["priority"] = "CRITICAL"
                best_rec["consensus_score"] = f"{vote_count}/{models_count}"
                best_rec["agreeing_models"] = vote_data["models"]
                unanimous_recommendations.append(best_rec)

            elif vote_count >= self.config["consensus"]["majority_threshold"]:
                # Majority agree - Important priority
                best_rec = self._merge_recommendations(vote_data["votes"])
                best_rec["priority"] = "IMPORTANT"
                best_rec["consensus_score"] = f"{vote_count}/{models_count}"
                best_rec["agreeing_models"] = vote_data["models"]
                majority_recommendations.append(best_rec)

        # Calculate totals
        total_cost = sum(response.cost for response in model_responses)
        total_tokens = sum(response.tokens_used for response in model_responses)
        total_time = sum(response.processing_time for response in model_responses)

        return ConsensusResult(
            unanimous_recommendations=unanimous_recommendations,
            majority_recommendations=majority_recommendations,
            total_cost=total_cost,
            total_tokens=total_tokens,
            total_time=total_time,
            model_responses=model_responses,
        )

    def _get_recommendation_key(self, rec: Dict[str, Any]) -> str:
        """Generate a key for recommendation similarity matching"""
        title = rec.get("title", "").lower().strip()
        # Simple key based on first few words
        words = title.split()[:3]
        return " ".join(words)

    def _merge_recommendations(
        self, recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge multiple similar recommendations into one"""
        if not recommendations:
            return {}

        # Use the first recommendation as base
        merged = recommendations[0].copy()

        # Merge descriptions if multiple
        if len(recommendations) > 1:
            descriptions = [rec.get("description", "") for rec in recommendations]
            merged["description"] = " | ".join(set(descriptions))

        return merged


class CostTracker:
    """Tracks API costs across all models"""

    def __init__(self, cost_file: str = "analysis_results/cost_tracking.json"):
        self.cost_file = cost_file
        self.session_costs = []
        self.total_cost = 0.0
        self.total_tokens = 0

    def add_session(self, cost: float, tokens: int):
        """Add a session's cost and tokens"""
        self.session_costs.append(
            {"timestamp": datetime.now().isoformat(), "cost": cost, "tokens": tokens}
        )
        self.total_cost += cost
        self.total_tokens += tokens

        # Save to file
        self._save_costs()

    def _save_costs(self):
        """Save cost tracking to file"""
        os.makedirs(os.path.dirname(self.cost_file), exist_ok=True)

        cost_data = {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "session_costs": self.session_costs,
            "last_updated": datetime.now().isoformat(),
        }

        with open(self.cost_file, "w") as f:
            json.dump(cost_data, f, indent=2)

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "session_count": len(self.session_costs),
            "average_per_session": (
                self.total_cost / len(self.session_costs) if self.session_costs else 0
            ),
        }


async def main():
    """Test the multi-model analyzer"""
    analyzer = MultiModelBookAnalyzer()

    # Test with sample book data
    test_book = {
        "id": "test_book",
        "title": "Designing Machine Learning Systems",
        "author": "Chip Huyen",
        "genre": "Machine Learning",
        "pages": 461,
    }

    print("🧪 Testing Multi-Model Book Analyzer...")
    result = await analyzer.analyze_book(test_book)

    print(f"\n📊 Results:")
    print(f"   Unanimous (Critical): {len(result.unanimous_recommendations)}")
    print(f"   Majority (Important): {len(result.majority_recommendations)}")
    print(f"   Total cost: ${result.total_cost:.2f}")
    print(f"   Total tokens: {result.total_tokens:,}")

    # Show sample recommendations
    if result.unanimous_recommendations:
        print(f"\n🎯 Sample Critical Recommendation:")
        rec = result.unanimous_recommendations[0]
        print(f"   Title: {rec['title']}")
        print(f"   Consensus: {rec['consensus_score']}")
        print(f"   Models: {', '.join(rec['agreeing_models'])}")


if __name__ == "__main__":
    asyncio.run(main())
