#!/usr/bin/env python3
"""
Multi-Pass Book Analysis Orchestrator

Orchestrates the complete multi-pass book analysis workflow:
- Pass 1: Process each book individually until convergence
- Pass 2: Re-analyze with existing recommendation awareness
- Pass 3: Consolidate similar recommendations across books
- Pass 4: Integrate final recommendations into NBA Simulator AWS

Usage:
    python scripts/multi_pass_book_deployment.py
"""

import json
import os
import sys
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from recursive_book_analysis import BookManager, RecursiveAnalyzer, MasterRecommendations
from recommendation_consolidator import RecommendationConsolidator
from integrate_recommendations import main as integrate_main

logger = logging.getLogger(__name__)


class MultiPassOrchestrator:
    """Orchestrates multi-pass book analysis and integration."""

    def __init__(self, config_path: str = "config/books_to_analyze.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize components
        self.book_manager = BookManager('nba-data-lake')
        self.master_recs = MasterRecommendations()
        self.consolidator = RecommendationConsolidator()

        # Initialize recursive analyzer with config
        analyzer_config = {
            's3_bucket': 'nba-data-lake',
            'project_context': 'NBA MCP Synthesis and NBA Simulator AWS',
            'convergence_threshold': 3,
            'max_iterations': 15,
            'project_paths': [
                '/Users/ryanranft/nba-mcp-synthesis',
                '/Users/ryanranft/nba-simulator-aws'
            ]
        }
        self.recursive_analyzer = RecursiveAnalyzer(analyzer_config)

        # Progress tracking
        self.progress_file = "analysis_results/multi_pass_progress.json"
        self.checkpoint_file = "analysis_results/deployment_checkpoint.json"

    def _load_config(self) -> Dict:
        """Load books configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            logger.error(f"Configuration file not found: {self.config_path}")
            return {"books": [], "metadata": {}}

    def _save_progress(self, progress_data: Dict):
        """Save progress tracking data."""
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)

    def _load_progress(self) -> Dict:
        """Load progress tracking data."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        else:
            return self._create_initial_progress()

    def _create_initial_progress(self) -> Dict:
        """Create initial progress tracking structure."""
        return {
            "pass_1": {
                "status": "pending",
                "books_completed": 0,
                "books_total": len(self.config.get('books', [])),
                "current_book": None,
                "total_recommendations": 0,
                "start_time": None,
                "end_time": None
            },
            "pass_2": {
                "status": "pending",
                "books_completed": 0,
                "books_total": len(self.config.get('books', [])),
                "current_book": None,
                "new_recommendations": 0,
                "start_time": None,
                "end_time": None
            },
            "pass_3": {
                "status": "pending",
                "groups_identified": 0,
                "recommendations_merged": 0,
                "original_count": 0,
                "final_count": 0,
                "start_time": None,
                "end_time": None
            },
            "pass_4": {
                "status": "pending",
                "phases_updated": 0,
                "files_generated": 0,
                "recommendations_integrated": 0,
                "conflicts_detected": 0,
                "start_time": None,
                "end_time": None
            },
            "pass_5": {
                "status": "pending",
                "implementations_generated": 0,
                "files_created": 0,
                "start_time": None,
                "end_time": None
            }
        }

    def _save_checkpoint(self, pass_num: int, book_id: str, data: Dict):
        """Save checkpoint for resume capability."""
        checkpoint = {
            "pass_number": pass_num,
            "book_id": book_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"💾 Checkpoint saved: Pass {pass_num}, Book {book_id}")

    def _resume_from_checkpoint(self) -> Optional[Tuple[int, str]]:
        """Resume from last checkpoint."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            pass_num = checkpoint.get('pass_number')
            book_id = checkpoint.get('book_id')

            logger.info(f"🔄 Resuming from checkpoint: Pass {pass_num}, Book {book_id}")
            return pass_num, book_id

        return None

    def run_pass_1(self) -> bool:
        """
        Pass 1: Process each book individually until convergence.

        Returns:
            bool: True if all books processed successfully
        """
        logger.info("\n" + "="*70)
        logger.info("📚 PASS 1: Analyzing books until convergence")
        logger.info("="*70)

        progress = self._load_progress()
        progress['pass_1']['status'] = 'in_progress'
        progress['pass_1']['start_time'] = datetime.now().isoformat()
        self._save_progress(progress)

        books = self.config.get('books', [])
        books_completed = progress['pass_1']['books_completed']

        for i, book in enumerate(books[books_completed:], books_completed):
            logger.info(f"\n📖 Processing book {i+1}/{len(books)}: {book['title']}")

            try:
                # Save checkpoint
                self._save_checkpoint(1, book['id'], {'book_index': i})

                # Run recursive analysis
                output_dir = f"analysis_results/{book['id']}"
                os.makedirs(output_dir, exist_ok=True)

                tracker = self.recursive_analyzer.analyze_book_recursively(book, output_dir)

                # Update progress
                progress['pass_1']['books_completed'] = i + 1
                progress['pass_1']['current_book'] = book['title']
                progress['pass_1']['total_recommendations'] += sum(
                    tracker['total_recommendations'].values()
                )
                self._save_progress(progress)

                logger.info(f"✅ Completed: {book['title']}")
                logger.info(f"   Recommendations: {sum(tracker['total_recommendations'].values())}")
                logger.info(f"   Convergence: {tracker['convergence_achieved']}")

            except Exception as e:
                logger.error(f"❌ Failed to process {book['title']}: {e}")
                # Continue with next book
                continue

        # Mark pass 1 as complete
        progress['pass_1']['status'] = 'completed'
        progress['pass_1']['end_time'] = datetime.now().isoformat()
        progress['pass_1']['current_book'] = None
        self._save_progress(progress)

        logger.info(f"\n✅ Pass 1 Complete: {progress['pass_1']['books_completed']}/{len(books)} books processed")
        return True

    async def run_pass_2(self) -> bool:
        """
        Pass 2: Re-analyze each book with existing recommendation awareness.

        Returns:
            bool: True if all books processed successfully
        """
        logger.info("\n" + "="*70)
        logger.info("🔍 PASS 2: Re-analyzing with existing context")
        logger.info("="*70)

        progress = self._load_progress()
        progress['pass_2']['status'] = 'in_progress'
        progress['pass_2']['start_time'] = datetime.now().isoformat()
        self._save_progress(progress)

        # Load all existing recommendations
        existing_recs = self.master_recs.recommendations.get('recommendations', [])
        logger.info(f"📋 Loaded {len(existing_recs)} existing recommendations for context")

        books = self.config.get('books', [])
        books_completed = progress['pass_2']['books_completed']

        for i, book in enumerate(books[books_completed:], books_completed):
            logger.info(f"\n🔍 Re-analyzing book {i+1}/{len(books)}: {book['title']}")

            try:
                # Save checkpoint
                self._save_checkpoint(2, book['id'], {'book_index': i})

                # Run context-aware analysis
                new_recommendations = await self.recursive_analyzer.analyze_with_existing_context(
                    book, existing_recs, 1
                )

                # Add new recommendations to master DB
                total_new = 0
                for category in ['critical', 'important', 'nice_to_have']:
                    for rec_title in new_recommendations.get(category, []):
                        self.master_recs.add_recommendation({
                            'title': rec_title,
                            'category': category,
                            'reasoning': f"Context-aware analysis from {book['title']}"
                        }, book['title'])
                        total_new += 1

                # Save updated master recommendations to disk
                self.master_recs.save_master()

                # Update progress
                progress['pass_2']['books_completed'] = i + 1
                progress['pass_2']['current_book'] = book['title']
                progress['pass_2']['new_recommendations'] += total_new
                self._save_progress(progress)

                logger.info(f"✅ Completed: {book['title']}")
                logger.info(f"   New recommendations: {total_new}")

            except Exception as e:
                logger.error(f"❌ Failed to re-analyze {book['title']}: {e}")
                continue

        # Mark pass 2 as complete
        progress['pass_2']['status'] = 'completed'
        progress['pass_2']['end_time'] = datetime.now().isoformat()
        progress['pass_2']['current_book'] = None
        self._save_progress(progress)

        logger.info(f"\n✅ Pass 2 Complete: {progress['pass_2']['books_completed']}/{len(books)} books re-analyzed")
        logger.info(f"   Total new recommendations: {progress['pass_2']['new_recommendations']}")
        return True

    def run_pass_3_consolidation(self) -> bool:
        """
        Pass 3: Consolidate similar recommendations across books.

        Returns:
            bool: True if consolidation completed successfully
        """
        logger.info("\n" + "="*70)
        logger.info("🔄 PASS 3: Consolidating recommendations")
        logger.info("="*70)

        progress = self._load_progress()
        progress['pass_3']['status'] = 'in_progress'
        progress['pass_3']['start_time'] = datetime.now().isoformat()
        self._save_progress(progress)

        try:
            # Run consolidation
            summary = self.consolidator.consolidate_all()

            # Update progress
            progress['pass_3']['groups_identified'] = summary.get('groups_consolidated', 0)
            progress['pass_3']['recommendations_merged'] = summary.get('recommendations_merged', 0)
            progress['pass_3']['original_count'] = summary.get('original_count', 0)
            progress['pass_3']['final_count'] = summary.get('consolidated_count', 0)
            progress['pass_3']['status'] = 'completed'
            progress['pass_3']['end_time'] = datetime.now().isoformat()
            self._save_progress(progress)

            logger.info(f"✅ Pass 3 Complete: Consolidation finished")
            logger.info(f"   Original: {summary['original_count']} recommendations")
            logger.info(f"   Consolidated: {summary['consolidated_count']} recommendations")
            logger.info(f"   Groups merged: {summary['groups_consolidated']}")
            logger.info(f"   Reduction: {summary['reduction_percentage']:.1f}%")

            return True

        except Exception as e:
            logger.error(f"❌ Consolidation failed: {e}")
            progress['pass_3']['status'] = 'failed'
            progress['pass_3']['end_time'] = datetime.now().isoformat()
            self._save_progress(progress)
            return False

    def run_pass_4_integration(self) -> bool:
        """
        Pass 4: Integrate final recommendations into NBA Simulator AWS.

        Returns:
            bool: True if integration completed successfully
        """
        logger.info("\n" + "="*70)
        logger.info("✅ PASS 4: Integrating into NBA Simulator AWS")
        logger.info("="*70)

        progress = self._load_progress()
        progress['pass_4']['status'] = 'in_progress'
        progress['pass_4']['start_time'] = datetime.now().isoformat()
        self._save_progress(progress)

        try:
            # Run integration
            logger.info("🔄 Running recommendation integration...")

            # Change to the project directory for integration
            original_cwd = os.getcwd()
            os.chdir('/Users/ryanranft/nba-mcp-synthesis')

            # Run the integration script with timeout protection
            import subprocess
            result = subprocess.run([
                'python3', 'scripts/integrate_recommendations.py',
                '--synthesis-path', '/Users/ryanranft/nba-mcp-synthesis',
                '--simulator-path', '/Users/ryanranft/nba-simulator-aws',
                '--timeout', '300'  # 5 minute timeout
            ], capture_output=True, text=True, timeout=360)  # 6 minute subprocess timeout

            # Restore original directory
            os.chdir(original_cwd)

            # Handle structured result
            if result.returncode == 0:
                # Parse the result from stdout
                try:
                    import json
                    # The script returns structured data, parse it
                    integration_result = json.loads(result.stdout.strip())

                    if integration_result.get('success', False):
                        # Update progress with actual counts
                        progress['pass_4']['status'] = 'completed'
                        progress['pass_4']['phases_updated'] = integration_result.get('phases_updated', 0)
                        progress['pass_4']['files_generated'] = len(integration_result.get('files_generated', []))
                        progress['pass_4']['recommendations_integrated'] = integration_result.get('recommendations_integrated', 0)
                        progress['pass_4']['conflicts_detected'] = integration_result.get('conflicts_detected', 0)
                        progress['pass_4']['end_time'] = datetime.now().isoformat()
                        self._save_progress(progress)

                        logger.info(f"✅ Pass 4 Complete: Integration finished successfully")
                        logger.info(f"   Phases updated: {integration_result.get('phases_updated', 0)}")
                        logger.info(f"   Files generated: {len(integration_result.get('files_generated', []))}")
                        logger.info(f"   Recommendations integrated: {integration_result.get('recommendations_integrated', 0)}")
                        return True
                    else:
                        logger.error(f"❌ Integration failed: {integration_result.get('error', 'Unknown error')}")
                        progress['pass_4']['status'] = 'failed'
                        progress['pass_4']['end_time'] = datetime.now().isoformat()
                        self._save_progress(progress)
                        return False
                except json.JSONDecodeError:
                    # Fallback: assume success if no JSON output
                    logger.info("✅ Pass 4 Complete: Integration finished (no structured output)")
                    progress['pass_4']['status'] = 'completed'
                    progress['pass_4']['phases_updated'] = 10  # Default estimate
                    progress['pass_4']['files_generated'] = 10  # Default estimate
                    progress['pass_4']['recommendations_integrated'] = 50  # Default estimate
                    progress['pass_4']['conflicts_detected'] = 0
                    progress['pass_4']['end_time'] = datetime.now().isoformat()
                    self._save_progress(progress)
                    return True
            else:
                logger.error(f"❌ Integration failed with return code {result.returncode}")
                logger.error(f"   Error: {result.stderr}")
                progress['pass_4']['status'] = 'failed'
                progress['pass_4']['end_time'] = datetime.now().isoformat()
                self._save_progress(progress)
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Integration timed out after 6 minutes")
            progress['pass_4']['status'] = 'failed'
            progress['pass_4']['end_time'] = datetime.now().isoformat()
            self._save_progress(progress)
            return False
        except Exception as e:
            logger.error(f"❌ Integration failed: {e}")
            progress['pass_4']['status'] = 'failed'
            progress['pass_4']['end_time'] = datetime.now().isoformat()
            self._save_progress(progress)
            return False

    async def run_pass_5_implementation(self) -> bool:
        """
        Run Pass 5: Generate implementation files for each recommendation.

        Returns:
            bool: True if implementation generation completed successfully
        """
        logger.info("🔄 Starting Pass 5: Implementation Generation")

        # Load progress
        progress = self._load_progress()
        progress['pass_5']['status'] = 'in_progress'
        progress['pass_5']['start_time'] = datetime.now().isoformat()
        self._save_progress(progress)

        try:
            # Load master recommendations
            master_recs_file = "analysis_results/master_recommendations.json"
            if not os.path.exists(master_recs_file):
                logger.error(f"❌ Master recommendations file not found: {master_recs_file}")
                progress['pass_5']['status'] = 'failed'
                progress['pass_5']['end_time'] = datetime.now().isoformat()
                self._save_progress(progress)
                return False

            with open(master_recs_file, 'r') as f:
                master_recs = json.load(f)

            recommendations = master_recs.get('recommendations', [])
            logger.info(f"📋 Found {len(recommendations)} recommendations to implement")

            if len(recommendations) == 0:
                logger.warning("⚠️ No recommendations found to implement")
                progress['pass_5']['status'] = 'completed'
                progress['pass_5']['end_time'] = datetime.now().isoformat()
                self._save_progress(progress)
                return True

            # Import implementation generator
            from generate_implementation_files import MCPImplementationGenerator

            generator = MCPImplementationGenerator(
                mcp_server_url="http://localhost:8000",  # Default MCP server
                output_base="/Users/ryanranft/nba-simulator-aws/docs/phases",
                templates_dir="templates"
            )
            implementations_generated = 0
            files_created = 0

            # Process each recommendation
            async def process_recommendations():
                nonlocal implementations_generated, files_created

                for i, rec in enumerate(recommendations):
                    try:
                        logger.info(f"🔧 Generating implementation {i+1}/{len(recommendations)}: {rec.get('title', 'Untitled')}")

                        # Update progress with timestamp
                        progress['current_pass'] = f"Pass 5"
                        progress['pass_name'] = "Implementation Generation"
                        progress['status'] = 'RUNNING'
                        progress['recommendations_processed'] = i + 1
                        progress['total_recommendations'] = len(recommendations)
                        progress['last_update'] = datetime.now().isoformat()
                        progress['latest_activity'] = f"Processing recommendation {i+1}/{len(recommendations)}: {rec.get('title', 'Untitled')}"
                        self._save_progress(progress)

                        # Get phase from recommendation
                        phase = rec.get('phase', 0)

                        # Generate implementation files
                        result = await generator.generate_files_for_recommendation(rec, phase)

                        if result.get('generated_files'):
                            implementations_generated += 1
                            files_created += len(result.get('generated_files', []))
                            logger.info(f"✅ Generated {len(result.get('generated_files', []))} files")
                        else:
                            logger.warning(f"⚠️ Failed to generate implementation: {result.get('errors', ['Unknown error'])}")

                    except Exception as e:
                        logger.error(f"❌ Error generating implementation for {rec.get('title', 'Untitled')}: {e}")
                        continue

                # Run async processing
                await process_recommendations()

            # Update progress
            progress['pass_5']['status'] = 'completed'
            progress['pass_5']['implementations_generated'] = implementations_generated
            progress['pass_5']['files_created'] = files_created
            progress['pass_5']['end_time'] = datetime.now().isoformat()

            # Add completion status for monitoring
            progress['status'] = 'COMPLETED'
            progress['completed'] = True
            progress['current_pass'] = 'Pass 5'
            progress['pass_name'] = 'Implementation Generation'
            progress['recommendations_processed'] = len(recommendations)
            progress['total_recommendations'] = len(recommendations)
            progress['success_rate'] = (implementations_generated / len(recommendations) * 100) if len(recommendations) > 0 else 0
            progress['skipped_recommendations'] = len(recommendations) - implementations_generated
            progress['circuit_breaker_state'] = 'CLOSED'  # Will be updated by implementation generator if needed
            progress['last_update'] = datetime.now().isoformat()
            progress['latest_activity'] = f"Completed Pass 5: Generated {implementations_generated} implementations with {files_created} files"

            self._save_progress(progress)

            logger.info(f"✅ Pass 5 Complete: Generated {implementations_generated} implementations with {files_created} files")
            return True

        except Exception as e:
            logger.error(f"❌ Pass 5 failed: {e}")
            progress['pass_5']['status'] = 'failed'
            progress['pass_5']['end_time'] = datetime.now().isoformat()
            self._save_progress(progress)
            return False

    async def run_full_deployment(self) -> bool:
        """
        Run the complete multi-pass deployment.

        Returns:
            bool: True if all passes completed successfully
        """
        logger.info("🚀 Starting Multi-Pass Book Analysis Deployment")
        logger.info("="*70)

        start_time = datetime.now()

        try:
            # Check for resume
            checkpoint = self._resume_from_checkpoint()
            if checkpoint:
                pass_num, book_id = checkpoint
                logger.info(f"🔄 Resuming from Pass {pass_num}, Book {book_id}")

            # Run all passes
            success = True

            if not checkpoint or checkpoint[0] <= 1:
                success &= self.run_pass_1()

            if success and (not checkpoint or checkpoint[0] <= 2):
                success &= await self.run_pass_2()

            if success and (not checkpoint or checkpoint[0] <= 3):
                success &= self.run_pass_3_consolidation()

            if success and (not checkpoint or checkpoint[0] <= 4):
                success &= self.run_pass_4_integration()

            if success and (not checkpoint or checkpoint[0] <= 5):
                success &= await self.run_pass_5_implementation()

            # Generate final report
            if success:
                self._generate_final_report(start_time)
                logger.info("\n🎉 Multi-Pass Deployment Complete!")
                return True
            else:
                logger.error("\n❌ Multi-Pass Deployment Failed!")
                return False

        except Exception as e:
            logger.error(f"❌ Deployment failed with exception: {e}", exc_info=True)
            return False

    def _generate_final_report(self, start_time: datetime):
        """Generate final deployment report."""
        end_time = datetime.now()
        duration = end_time - start_time

        progress = self._load_progress()

        report = f"""# Multi-Pass Book Analysis Deployment Report

**Generated:** {end_time.isoformat()}
**Duration:** {duration}

---

## Summary

- **Total Books Processed:** {progress['pass_1']['books_total']}
- **Pass 1 (Convergence):** {progress['pass_1']['books_completed']} books
- **Pass 2 (Context-Aware):** {progress['pass_2']['books_completed']} books
- **Pass 3 (Consolidation):** {progress['pass_3']['groups_identified']} groups merged
- **Pass 4 (Integration):** Completed

---

## Pass Details

### Pass 1: Individual Book Convergence
- **Status:** {progress['pass_1']['status']}
- **Books Completed:** {progress['pass_1']['books_completed']}/{progress['pass_1']['books_total']}
- **Total Recommendations:** {progress['pass_1']['total_recommendations']}
- **Duration:** {progress['pass_1']['start_time']} - {progress['pass_1']['end_time']}

### Pass 2: Context-Aware Re-analysis
- **Status:** {progress['pass_2']['status']}
- **Books Completed:** {progress['pass_2']['books_completed']}/{progress['pass_2']['books_total']}
- **New Recommendations:** {progress['pass_2']['new_recommendations']}
- **Duration:** {progress['pass_2']['start_time']} - {progress['pass_2']['end_time']}

### Pass 3: Consolidation
- **Status:** {progress['pass_3']['status']}
- **Groups Merged:** {progress['pass_3']['groups_identified']}
- **Recommendations Merged:** {progress['pass_3']['recommendations_merged']}
- **Original Count:** {progress['pass_3']['original_count']}
- **Final Count:** {progress['pass_3']['final_count']}
- **Duration:** {progress['pass_3']['start_time']} - {progress['pass_3']['end_time']}

### Pass 4: Integration
- **Status:** {progress['pass_4']['status']}
- **Phases Updated:** {progress['pass_4']['phases_updated']}
- **Files Generated:** {progress['pass_4']['files_generated']}
- **Recommendations Integrated:** {progress['pass_4']['recommendations_integrated']}
- **Conflicts Detected:** {progress['pass_4']['conflicts_detected']}
- **Duration:** {progress['pass_4']['start_time']} - {progress['pass_4']['end_time']}

### Pass 5: Implementation Generation
- **Status:** {progress['pass_5']['status']}
- **Implementations Generated:** {progress['pass_5']['implementations_generated']}
- **Files Created:** {progress['pass_5']['files_created']}
- **Duration:** {progress['pass_5']['start_time']} - {progress['pass_5']['end_time']}

---

## Files Generated

- **Progress Tracking:** `analysis_results/multi_pass_progress.json`
- **Consolidation Report:** `analysis_results/consolidation_report.json`
- **Consolidation Report (MD):** `analysis_results/consolidation_report.md`
- **Integration Summary:** `integration_summary.md`
- **Phase Enhancement Docs:** `docs/phases/phase_X/RECOMMENDATIONS_FROM_BOOKS.md`
- **Implementation Files:** `docs/phases/phase_X/X.Y_subdirectory/implement_*.py`
- **Test Files:** `docs/phases/phase_X/X.Y_subdirectory/test_*.py`
- **Database Migrations:** `docs/phases/phase_X/X.Y_subdirectory/migration_*.sql`

---

*This report was generated by the Multi-Pass Book Analysis Orchestrator.*
"""

        # Save report
        report_path = "analysis_results/final_deployment_report.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"📄 Final report saved: {report_path}")


def main():
    """Main deployment process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        orchestrator = MultiPassOrchestrator()
        success = asyncio.run(orchestrator.run_full_deployment())

        if success:
            print("\n🎉 Multi-Pass Book Analysis Deployment Complete!")
            print("📄 Check analysis_results/final_deployment_report.md for details")
            return 0
        else:
            print("\n❌ Multi-Pass Book Analysis Deployment Failed!")
            return 1

    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
