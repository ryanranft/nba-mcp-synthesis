"""
Test script for Four-Model Book Analysis System
Tests the 4-model system on 2 books to validate quality and cost before full deployment.
"""

import asyncio
import os
import logging
from four_model_book_analyzer import FourModelBookAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_four_model_analysis():
    """
    Test the FourModelBookAnalyzer with sample books.
    """
    logger.info("Starting 4-model analysis test...")

    # Check API keys
    required_keys = ["GOOGLE_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        logger.error(f"Missing required API keys: {missing_keys}")
        logger.error("Please set all required environment variables:")
        for key in missing_keys:
            logger.error(f"  export {key}=your_api_key_here")
        return

    # Sample book content (truncated for brevity)
    sample_books = [
        {
            "id": "test_ml_systems",
            "title": "Designing Machine Learning Systems",
            "author": "Chip Huyen",
            "s3_path": "books/Designing_Machine_Learning_Systems.pdf",
            "content": """
            Designing Machine Learning Systems: An Iterative Process for Production-Ready ML Applications
            By Chip Huyen

            Chapter 1: Introduction to ML Systems Design

            Machine learning systems are complex, involving data collection, feature engineering, model training,
            deployment, and monitoring. Unlike traditional software, ML systems interact with dynamic data,
            making them prone to issues like data drift and model decay.

            Key challenges include:
            - Data quality and consistency
            - Feature store management
            - Model versioning and reproducibility
            - Monitoring and alerting for performance degradation
            - Scalability of training and inference
            - Explainability and interpretability of models

            A robust ML system requires careful design across the entire lifecycle.
            It's an iterative process, starting with a prototype and gradually adding
            production-grade components.

            Chapter 2: Data Engineering for ML

            Data is the fuel for ML. Effective data engineering is crucial.
            Concepts:
            - Feature Stores: Centralized repositories for features, ensuring consistency and reusability.
              Online feature stores for low-latency inference, offline for training.
            - Data Versioning: Tracking changes to data over time, essential for reproducibility.
            - Data Validation: Ensuring data quality and detecting anomalies before they impact models.
            - Data Pipelines: Automated workflows for data ingestion, transformation, and loading.

            Chapter 3: Model Development and Training

            This chapter covers model selection, training, and evaluation.
            - Experiment Tracking: Tools like MLflow to log parameters, metrics, and models.
            - Automated Retraining: Pipelines that automatically retrain models when performance degrades or new data arrives.
            - Hyperparameter Tuning: Optimizing model performance.

            Chapter 4: Deployment and Operations (MLOps)

            Deploying ML models to production and maintaining them.
            - Model Serving: REST APIs, batch inference.
            - A/B Testing: Comparing different model versions in production.
            - Shadow Deployment: Deploying a new model alongside an old one to observe its performance without impacting users.
            - Monitoring: Tracking model predictions, data drift, and system health.
            - Rollback Strategies: Quickly reverting to previous stable versions.
            """
        },
        {
            "id": "test_statistics_601",
            "title": "Statistics 601 Advanced Statistical Methods",
            "author": "Various Authors",
            "s3_path": "books/STATISTICS_601_Advanced_Statistical_Methods.pdf",
            "content": """
            Statistics 601: Advanced Statistical Methods
            Comprehensive Guide to Statistical Analysis

            Chapter 1: Hypothesis Testing

            Hypothesis testing is a fundamental statistical method for making decisions based on data.
            The process involves:
            - Formulating null and alternative hypotheses
            - Choosing appropriate test statistics
            - Calculating p-values
            - Making decisions based on significance levels

            Advanced concepts include:
            - Multiple testing corrections (Bonferroni, FDR)
            - Power analysis for experimental design
            - Effect size calculations
            - Non-parametric alternatives

            Chapter 2: Regression Analysis

            Regression analysis examines relationships between variables.
            Types include:
            - Linear regression
            - Logistic regression
            - Polynomial regression
            - Multiple regression

            Key considerations:
            - Assumption checking (linearity, independence, homoscedasticity)
            - Model selection and validation
            - Handling multicollinearity
            - Outlier detection and treatment

            Chapter 3: Time Series Analysis

            Time series data requires special statistical methods.
            Components:
            - Trend analysis
            - Seasonal patterns
            - Cyclical variations
            - Random noise

            Methods:
            - ARIMA models
            - Exponential smoothing
            - Seasonal decomposition
            - Forecasting techniques

            Chapter 4: Bayesian Statistics

            Bayesian methods provide a probabilistic framework for statistical inference.
            Key concepts:
            - Prior distributions
            - Likelihood functions
            - Posterior distributions
            - Bayesian updating

            Applications:
            - Parameter estimation
            - Model comparison
            - Decision making under uncertainty
            - Hierarchical modeling
            """
        }
    ]

    analyzer = FourModelBookAnalyzer()

    total_cost = 0.0
    total_recommendations = 0

    for i, book in enumerate(sample_books, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing Book {i}: {book['title']}")
        logger.info(f"{'='*60}")

        try:
            result = await analyzer.analyze_book(book)

            if result.success:
                logger.info(f"\n--- {book['title']} Results ---")
                logger.info(f"Total Cost: ${result.total_cost:.4f}")
                logger.info(f"  Readers: ${result.google_cost + result.deepseek_cost:.4f}")
                logger.info(f"    Google Gemini: ${result.google_cost:.4f}")
                logger.info(f"    DeepSeek: ${result.deepseek_cost:.4f}")
                logger.info(f"  Synthesizers: ${result.claude_cost + result.gpt4_cost:.4f}")
                logger.info(f"    Claude: ${result.claude_cost:.4f}")
                logger.info(f"    GPT-4: ${result.gpt4_cost:.4f}")
                logger.info(f"Total Tokens: {result.total_tokens:,}")
                logger.info(f"Processing Time: {result.total_time:.1f}s")

                recommendations = result.recommendations
                logger.info(f"Recommendations Found: {len(recommendations)}")

                critical_count = sum(1 for r in recommendations if r.get('priority') == 'CRITICAL')
                important_count = sum(1 for r in recommendations if r.get('priority') == 'IMPORTANT')

                logger.info(f"  Critical (2/2 vote): {critical_count}")
                logger.info(f"  Important (1/2 vote): {important_count}")

                # Show sample recommendations
                logger.info(f"\n--- Sample Recommendations ---")
                for j, rec in enumerate(recommendations[:3], 1):
                    logger.info(f"{j}. {rec.get('title', 'Unknown')}")
                    logger.info(f"   Priority: {rec.get('priority', 'Unknown')}")
                    logger.info(f"   Consensus: {rec.get('consensus_score', 'Unknown')}")
                    logger.info(f"   Phase: {rec.get('mapped_phase', 'Unknown')}")
                    logger.info(f"   Time: {rec.get('time_estimate', 'Unknown')}")
                    logger.info("-" * 40)

                total_cost += result.total_cost
                total_recommendations += len(recommendations)

                # Validate results
                assert len(recommendations) > 0, "No recommendations were extracted."
                assert result.total_cost > 0, "Cost was not tracked."
                assert result.total_tokens > 0, "Tokens were not tracked."
                assert critical_count + important_count == len(recommendations), "All recommendations should be Critical or Important"

                logger.info(f"✅ Book {i} test completed successfully!")

            else:
                logger.error(f"❌ Book {i} test failed: {result.error}")
                return

        except Exception as e:
            logger.error(f"❌ Book {i} test failed with exception: {str(e)}")
            return

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Books tested: {len(sample_books)}")
    logger.info(f"Total cost: ${total_cost:.4f}")
    logger.info(f"Total recommendations: {total_recommendations}")
    logger.info(f"Average cost per book: ${total_cost/len(sample_books):.4f}")
    logger.info(f"Average recommendations per book: {total_recommendations/len(sample_books):.1f}")

    # Cost projection for full deployment
    estimated_books = 17
    projected_cost = total_cost * (estimated_books / len(sample_books))
    logger.info(f"\nProjected cost for {estimated_books} books: ${projected_cost:.2f}")

    logger.info(f"\n🎉 All tests completed successfully!")
    logger.info(f"✅ 4-model analysis system is ready for full deployment")


if __name__ == "__main__":
    asyncio.run(test_four_model_analysis())
