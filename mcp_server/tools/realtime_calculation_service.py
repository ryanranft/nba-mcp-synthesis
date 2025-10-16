#!/usr/bin/env python3
"""
Phase 8.3: Real-Time Calculation Service

This module provides real-time NBA data integration and batch processing capabilities including:
- Live NBA data streaming and integration
- Real-time formula calculations with live data
- Batch processing for large datasets
- Data synchronization and caching
- Performance monitoring and optimization
- Error handling and recovery
- WebSocket connections for real-time updates
"""

import asyncio
import logging
import uuid
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
import aiohttp
import websockets
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes and Enums
# =============================================================================

class DataSourceType(str, Enum):
    """Types of data sources"""
    NBA_API = "nba_api"
    LIVE_STREAM = "live_stream"
    DATABASE = "database"
    CACHE = "cache"
    FILE = "file"


class CalculationStatus(str, Enum):
    """Status of calculations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchStatus(str, Enum):
    """Status of batch operations"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncFrequency(str, Enum):
    """Data synchronization frequencies"""
    REAL_TIME = "real_time"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class LiveDataPoint:
    """Represents a single live data point"""
    data_id: str
    source: str
    timestamp: datetime
    data_type: str
    value: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CalculationTask:
    """Represents a calculation task"""
    task_id: str
    formula_id: str
    input_data: Dict[str, Any]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BatchJob:
    """Represents a batch processing job"""
    job_id: str
    job_type: str
    data_source: str
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[List[Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DataSyncConfig:
    """Configuration for data synchronization"""
    sync_id: str
    source: str
    target: str
    frequency: str
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Core Real-Time Calculation Service
# =============================================================================

class RealTimeCalculationService:
    """Main service for real-time calculations and data processing"""

    def __init__(self):
        """Initialize the real-time calculation service"""
        self.live_data_cache: Dict[str, LiveDataPoint] = {}
        self.calculation_queue: queue.Queue = queue.Queue()
        self.batch_jobs: Dict[str, BatchJob] = {}
        self.data_sync_configs: Dict[str, DataSyncConfig] = {}
        self.active_connections: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.is_running = False
        self.websocket_server = None

        # Performance metrics
        self.performance_metrics = {
            "calculations_performed": 0,
            "average_calculation_time": 0.0,
            "data_points_processed": 0,
            "batch_jobs_completed": 0,
            "sync_operations": 0
        }

        # Initialize service configurations
        self._initialize_service_configs()

        logger.info("Real-Time Calculation Service initialized")

    def _generate_task_id(self) -> str:
        """Generate a unique task ID"""
        return f"task_{uuid.uuid4().hex[:8]}"

    def _generate_job_id(self) -> str:
        """Generate a unique job ID"""
        return f"job_{uuid.uuid4().hex[:8]}"

    def _generate_sync_id(self) -> str:
        """Generate a unique sync ID"""
        return f"sync_{uuid.uuid4().hex[:8]}"

    def _initialize_service_configs(self):
        """Initialize service configurations"""
        self.service_configs = {
            "max_concurrent_calculations": 50,
            "batch_size": 1000,
            "cache_ttl_seconds": 300,
            "websocket_port": 8765,
            "sync_intervals": {
                "real_time": 1,
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400
            }
        }

    async def start_service(self) -> Dict[str, Any]:
        """
        Start the real-time calculation service.

        Returns:
            Dictionary with service startup results
        """
        try:
            logger.info("Starting Real-Time Calculation Service")

            self.is_running = True

            # Start background tasks
            asyncio.create_task(self._data_sync_worker())
            asyncio.create_task(self._calculation_worker())
            asyncio.create_task(self._batch_processing_worker())

            # Start WebSocket server for real-time updates
            await self._start_websocket_server()

            result = {
                "status": "success",
                "service_started": True,
                "startup_timestamp": datetime.now().isoformat(),
                "active_workers": 3,
                "websocket_port": self.service_configs["websocket_port"],
                "metadata": {
                    "max_concurrent_calculations": self.service_configs["max_concurrent_calculations"],
                    "batch_size": self.service_configs["batch_size"],
                    "cache_ttl": self.service_configs["cache_ttl_seconds"]
                }
            }

            logger.info("✓ Real-Time Calculation Service started successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return {
                "status": "error",
                "error": str(e),
                "service_started": False
            }

    async def stop_service(self) -> Dict[str, Any]:
        """
        Stop the real-time calculation service.

        Returns:
            Dictionary with service shutdown results
        """
        try:
            logger.info("Stopping Real-Time Calculation Service")

            self.is_running = False

            # Stop WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()

            # Shutdown executor
            self.executor.shutdown(wait=True)

            result = {
                "status": "success",
                "service_stopped": True,
                "shutdown_timestamp": datetime.now().isoformat(),
                "final_metrics": self.performance_metrics
            }

            logger.info("✓ Real-Time Calculation Service stopped successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return {
                "status": "error",
                "error": str(e),
                "service_stopped": False
            }

    async def calculate_formula_realtime(
        self,
        formula_id: str,
        input_data: Dict[str, Any],
        use_live_data: bool = True,
        cache_result: bool = True,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate a formula with real-time data.

        Args:
            formula_id: ID of the formula to calculate
            input_data: Input data for the calculation
            use_live_data: Whether to use live data
            cache_result: Whether to cache the result
            timeout_seconds: Timeout for the calculation

        Returns:
            Dictionary with calculation results
        """
        try:
            task_id = self._generate_task_id()
            start_time = time.time()

            logger.info(f"Starting real-time calculation: {formula_id}")

            # Create calculation task
            task = CalculationTask(
                task_id=task_id,
                formula_id=formula_id,
                input_data=input_data,
                status=CalculationStatus.PENDING,
                created_at=datetime.now(),
                metadata={"use_live_data": use_live_data, "cache_result": cache_result}
            )

            # Get live data if requested
            if use_live_data:
                live_data = await self._get_live_data_for_formula(formula_id)
                input_data.update(live_data)

            # Perform calculation
            task.status = CalculationStatus.RUNNING
            task.started_at = datetime.now()

            result = await self._perform_calculation(formula_id, input_data, timeout_seconds)

            task.status = CalculationStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Cache result if requested
            if cache_result:
                await self._cache_calculation_result(task_id, result)

            # Update performance metrics
            calculation_time = time.time() - start_time
            self._update_performance_metrics(calculation_time)

            result_dict = {
                "status": "success",
                "task_id": task_id,
                "formula_id": formula_id,
                "result": result,
                "calculation_time": calculation_time,
                "used_live_data": use_live_data,
                "cached": cache_result,
                "metadata": {
                    "calculation_timestamp": datetime.now().isoformat(),
                    "input_data_keys": list(input_data.keys())
                }
            }

            logger.info(f"✓ Real-time calculation completed: {formula_id} in {calculation_time:.3f}s")
            return result_dict

        except Exception as e:
            logger.error(f"Real-time calculation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "formula_id": formula_id,
                "task_id": task_id if 'task_id' in locals() else None
            }

    async def process_batch_calculations(
        self,
        formula_id: str,
        batch_data: List[Dict[str, Any]],
        batch_size: int = 1000,
        use_parallel_processing: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process batch calculations for large datasets.

        Args:
            formula_id: ID of the formula to calculate
            batch_data: List of input data for batch processing
            batch_size: Size of each batch
            use_parallel_processing: Whether to use parallel processing
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with batch processing results
        """
        try:
            job_id = self._generate_job_id()
            start_time = time.time()

            logger.info(f"Starting batch processing: {formula_id} with {len(batch_data)} items")

            # Create batch job
            job = BatchJob(
                job_id=job_id,
                job_type="formula_calculation",
                data_source="batch_input",
                status=BatchStatus.QUEUED,
                total_items=len(batch_data),
                processed_items=0,
                failed_items=0,
                created_at=datetime.now(),
                metadata={"formula_id": formula_id, "batch_size": batch_size}
            )

            self.batch_jobs[job_id] = job

            # Process batches
            results = []
            job.status = BatchStatus.PROCESSING
            job.started_at = datetime.now()

            for i in range(0, len(batch_data), batch_size):
                batch_chunk = batch_data[i:i + batch_size]

                if use_parallel_processing:
                    batch_results = await self._process_batch_parallel(formula_id, batch_chunk)
                else:
                    batch_results = await self._process_batch_sequential(formula_id, batch_chunk)

                results.extend(batch_results)
                job.processed_items += len(batch_chunk)

                # Update progress
                if progress_callback:
                    progress = (job.processed_items / job.total_items) * 100
                    progress_callback(progress, job.processed_items, job.total_items)

            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now()
            job.results = results

            # Update performance metrics
            processing_time = time.time() - start_time
            self.performance_metrics["batch_jobs_completed"] += 1

            result_dict = {
                "status": "success",
                "job_id": job_id,
                "formula_id": formula_id,
                "total_items": job.total_items,
                "processed_items": job.processed_items,
                "failed_items": job.failed_items,
                "processing_time": processing_time,
                "results": results,
                "metadata": {
                    "batch_size": batch_size,
                    "parallel_processing": use_parallel_processing,
                    "completion_timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"✓ Batch processing completed: {job_id} in {processing_time:.3f}s")
            return result_dict

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "formula_id": formula_id,
                "job_id": job_id if 'job_id' in locals() else None
            }

    async def sync_live_data(
        self,
        data_source: str,
        sync_frequency: str = "minute",
        data_types: List[str] = None,
        auto_start: bool = True
    ) -> Dict[str, Any]:
        """
        Set up live data synchronization.

        Args:
            data_source: Source of the data
            sync_frequency: How often to sync
            data_types: Types of data to sync
            auto_start: Whether to start syncing immediately

        Returns:
            Dictionary with sync configuration
        """
        try:
            sync_id = self._generate_sync_id()

            logger.info(f"Setting up live data sync: {data_source} ({sync_frequency})")

            # Create sync configuration
            sync_config = DataSyncConfig(
                sync_id=sync_id,
                source=data_source,
                target="live_cache",
                frequency=sync_frequency,
                last_sync=None,
                next_sync=datetime.now() + timedelta(seconds=self.service_configs["sync_intervals"].get(sync_frequency, 60)),
                is_active=auto_start,
                metadata={"data_types": data_types or []}
            )

            self.data_sync_configs[sync_id] = sync_config

            # Start sync if auto_start is enabled
            if auto_start:
                await self._start_data_sync(sync_id)

            result = {
                "status": "success",
                "sync_id": sync_id,
                "data_source": data_source,
                "sync_frequency": sync_frequency,
                "data_types": data_types or [],
                "auto_started": auto_start,
                "next_sync": sync_config.next_sync.isoformat() if sync_config.next_sync else None,
                "metadata": {
                    "sync_timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"✓ Live data sync configured: {sync_id}")
            return result

        except Exception as e:
            logger.error(f"Live data sync setup failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data_source": data_source
            }

    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of the service.

        Returns:
            Dictionary with service status information
        """
        try:
            active_calculations = len([task for task in self.calculation_queue.queue if hasattr(task, 'status') and task.status == CalculationStatus.RUNNING])
            active_batch_jobs = len([job for job in self.batch_jobs.values() if job.status == BatchStatus.PROCESSING])
            active_syncs = len([sync for sync in self.data_sync_configs.values() if sync.is_active])

            status = {
                "status": "success",
                "service_running": self.is_running,
                "active_calculations": active_calculations,
                "active_batch_jobs": active_batch_jobs,
                "active_syncs": active_syncs,
                "live_data_points": len(self.live_data_cache),
                "performance_metrics": self.performance_metrics,
                "websocket_connections": len(self.active_connections),
                "metadata": {
                    "status_timestamp": datetime.now().isoformat(),
                    "uptime": time.time() - getattr(self, 'start_time', time.time())
                }
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "service_running": False
            }

    async def optimize_performance(self) -> Dict[str, Any]:
        """
        Optimize service performance based on current metrics.

        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info("Optimizing service performance")

            optimizations = []

            # Optimize cache
            cache_optimization = await self._optimize_cache()
            optimizations.append(cache_optimization)

            # Optimize batch processing
            batch_optimization = await self._optimize_batch_processing()
            optimizations.append(batch_optimization)

            # Optimize data sync
            sync_optimization = await self._optimize_data_sync()
            optimizations.append(sync_optimization)

            result = {
                "status": "success",
                "optimizations_applied": len(optimizations),
                "optimizations": optimizations,
                "performance_improvement": self._calculate_performance_improvement(),
                "metadata": {
                    "optimization_timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"✓ Performance optimization completed: {len(optimizations)} optimizations applied")
            return result

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "optimizations_applied": 0
            }

    # Helper methods
    async def _get_live_data_for_formula(self, formula_id: str) -> Dict[str, Any]:
        """Get live data relevant to a formula"""
        try:
            # This would integrate with actual NBA API or live data sources
            # For now, return mock live data
            live_data = {}

            # Get cached live data points
            for data_point in self.live_data_cache.values():
                if data_point.data_type in ["player_stats", "team_stats", "game_stats"]:
                    live_data[data_point.data_id] = data_point.value

            return live_data

        except Exception as e:
            logger.error(f"Failed to get live data: {e}")
            return {}

    async def _perform_calculation(self, formula_id: str, input_data: Dict[str, Any], timeout: int) -> Any:
        """Perform the actual formula calculation"""
        try:
            # This would integrate with the actual formula calculation engine
            # For now, return mock calculation result

            # Simulate calculation time
            await asyncio.sleep(0.01)

            # Mock calculation based on formula type
            if formula_id == "per":
                points = input_data.get("points", 0)
                rebounds = input_data.get("rebounds", 0)
                assists = input_data.get("assists", 0)
                return points + rebounds + assists  # Simplified PER calculation

            elif formula_id == "true_shooting":
                points = input_data.get("points", 0)
                fga = input_data.get("fga", 1)
                fta = input_data.get("fta", 0)
                return points / (2 * (fga + 0.44 * fta)) if (fga + 0.44 * fta) > 0 else 0

            else:
                # Generic calculation
                return sum(input_data.values()) if input_data else 0

        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            raise

    async def _cache_calculation_result(self, task_id: str, result: Any):
        """Cache calculation result"""
        try:
            cache_key = f"calc_{task_id}"
            self.live_data_cache[cache_key] = LiveDataPoint(
                data_id=cache_key,
                source="calculation",
                timestamp=datetime.now(),
                data_type="calculation_result",
                value=result,
                metadata={"task_id": task_id}
            )
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    async def _process_batch_parallel(self, formula_id: str, batch_chunk: List[Dict[str, Any]]) -> List[Any]:
        """Process batch chunk in parallel"""
        try:
            tasks = []
            for data_item in batch_chunk:
                task = asyncio.create_task(self._perform_calculation(formula_id, data_item, 30))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = [r for r in results if not isinstance(r, Exception)]
            return valid_results

        except Exception as e:
            logger.error(f"Parallel batch processing failed: {e}")
            return []

    async def _process_batch_sequential(self, formula_id: str, batch_chunk: List[Dict[str, Any]]) -> List[Any]:
        """Process batch chunk sequentially"""
        try:
            results = []
            for data_item in batch_chunk:
                try:
                    result = await self._perform_calculation(formula_id, data_item, 30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Sequential batch item failed: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Sequential batch processing failed: {e}")
            return []

    async def _start_data_sync(self, sync_id: str):
        """Start data synchronization"""
        try:
            sync_config = self.data_sync_configs.get(sync_id)
            if not sync_config:
                return

            # Simulate data sync
            await asyncio.sleep(0.1)

            # Update sync timestamps
            sync_config.last_sync = datetime.now()
            sync_config.next_sync = datetime.now() + timedelta(
                seconds=self.service_configs["sync_intervals"].get(sync_config.frequency, 60)
            )

            self.performance_metrics["sync_operations"] += 1

        except Exception as e:
            logger.error(f"Data sync failed: {e}")

    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        try:
            async def websocket_handler(websocket, path):
                connection_id = str(uuid.uuid4())
                self.active_connections[connection_id] = websocket

                try:
                    async for message in websocket:
                        # Handle incoming messages
                        data = json.loads(message)
                        await self._handle_websocket_message(connection_id, data)
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    if connection_id in self.active_connections:
                        del self.active_connections[connection_id]

            self.websocket_server = await websockets.serve(
                websocket_handler,
                "localhost",
                self.service_configs["websocket_port"]
            )

        except Exception as e:
            logger.error(f"WebSocket server failed: {e}")

    async def _handle_websocket_message(self, connection_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        try:
            message_type = data.get("type")

            if message_type == "subscribe":
                # Subscribe to real-time updates
                await self._subscribe_to_updates(connection_id, data.get("topics", []))

            elif message_type == "unsubscribe":
                # Unsubscribe from updates
                await self._unsubscribe_from_updates(connection_id, data.get("topics", []))

        except Exception as e:
            logger.error(f"WebSocket message handling failed: {e}")

    async def _subscribe_to_updates(self, connection_id: str, topics: List[str]):
        """Subscribe connection to specific topics"""
        # Implementation for topic subscription
        pass

    async def _unsubscribe_from_updates(self, connection_id: str, topics: List[str]):
        """Unsubscribe connection from specific topics"""
        # Implementation for topic unsubscription
        pass

    async def _data_sync_worker(self):
        """Background worker for data synchronization"""
        while self.is_running:
            try:
                for sync_id, sync_config in self.data_sync_configs.items():
                    if sync_config.is_active and sync_config.next_sync and sync_config.next_sync <= datetime.now():
                        await self._start_data_sync(sync_id)

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Data sync worker error: {e}")
                await asyncio.sleep(5)

    async def _calculation_worker(self):
        """Background worker for calculations"""
        while self.is_running:
            try:
                if not self.calculation_queue.empty():
                    task = self.calculation_queue.get()
                    # Process task
                    self.calculation_queue.task_done()

                await asyncio.sleep(0.1)  # Check frequently

            except Exception as e:
                logger.error(f"Calculation worker error: {e}")
                await asyncio.sleep(1)

    async def _batch_processing_worker(self):
        """Background worker for batch processing"""
        while self.is_running:
            try:
                # Process any pending batch jobs
                for job_id, job in self.batch_jobs.items():
                    if job.status == BatchStatus.QUEUED:
                        # Start processing the job
                        pass

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Batch processing worker error: {e}")
                await asyncio.sleep(5)

    def _update_performance_metrics(self, calculation_time: float):
        """Update performance metrics"""
        self.performance_metrics["calculations_performed"] += 1

        # Update average calculation time
        total_calculations = self.performance_metrics["calculations_performed"]
        current_avg = self.performance_metrics["average_calculation_time"]
        self.performance_metrics["average_calculation_time"] = (
            (current_avg * (total_calculations - 1) + calculation_time) / total_calculations
        )

    async def _optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        try:
            # Remove expired cache entries
            expired_keys = []
            for key, data_point in self.live_data_cache.items():
                if datetime.now() - data_point.timestamp > timedelta(seconds=self.service_configs["cache_ttl_seconds"]):
                    expired_keys.append(key)

            for key in expired_keys:
                del self.live_data_cache[key]

            return {
                "type": "cache_optimization",
                "expired_entries_removed": len(expired_keys),
                "cache_size": len(self.live_data_cache)
            }

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"type": "cache_optimization", "error": str(e)}

    async def _optimize_batch_processing(self) -> Dict[str, Any]:
        """Optimize batch processing performance"""
        try:
            # Adjust batch size based on performance
            current_batch_size = self.service_configs["batch_size"]

            # Simple optimization: increase batch size if performance is good
            if self.performance_metrics["average_calculation_time"] < 0.1:
                new_batch_size = min(current_batch_size * 2, 5000)
                self.service_configs["batch_size"] = new_batch_size

                return {
                    "type": "batch_optimization",
                    "batch_size_increased": True,
                    "new_batch_size": new_batch_size
                }

            return {
                "type": "batch_optimization",
                "batch_size_increased": False,
                "current_batch_size": current_batch_size
            }

        except Exception as e:
            logger.error(f"Batch optimization failed: {e}")
            return {"type": "batch_optimization", "error": str(e)}

    async def _optimize_data_sync(self) -> Dict[str, Any]:
        """Optimize data synchronization performance"""
        try:
            # Optimize sync frequencies based on usage
            optimizations = []

            for sync_id, sync_config in self.data_sync_configs.items():
                if sync_config.frequency == "real_time" and self.performance_metrics["sync_operations"] > 1000:
                    # Reduce frequency if too many sync operations
                    sync_config.frequency = "second"
                    optimizations.append(f"Reduced sync frequency for {sync_id}")

            return {
                "type": "sync_optimization",
                "optimizations_applied": len(optimizations),
                "details": optimizations
            }

        except Exception as e:
            logger.error(f"Sync optimization failed: {e}")
            return {"type": "sync_optimization", "error": str(e)}

    def _calculate_performance_improvement(self) -> float:
        """Calculate overall performance improvement"""
        try:
            # Simple performance improvement calculation
            base_performance = 1.0
            improvement_factor = 1.0

            # Factor in calculation time improvement
            if self.performance_metrics["average_calculation_time"] < 0.1:
                improvement_factor *= 1.2

            # Factor in cache efficiency
            cache_efficiency = len(self.live_data_cache) / max(1, self.performance_metrics["calculations_performed"])
            if cache_efficiency > 0.5:
                improvement_factor *= 1.1

            return base_performance * improvement_factor

        except Exception as e:
            logger.error(f"Performance improvement calculation failed: {e}")
            return 1.0


# =============================================================================
# Standalone Functions
# =============================================================================

# Global service instance for standalone functions
_global_realtime_service = RealTimeCalculationService()


async def start_realtime_service() -> Dict[str, Any]:
    """
    Start the real-time calculation service (standalone function).

    Returns:
        Dictionary with service startup results
    """
    return await _global_realtime_service.start_service()


async def stop_realtime_service() -> Dict[str, Any]:
    """
    Stop the real-time calculation service (standalone function).

    Returns:
        Dictionary with service shutdown results
    """
    return await _global_realtime_service.stop_service()


async def calculate_formula_realtime(
    formula_id: str,
    input_data: Dict[str, Any],
    use_live_data: bool = True,
    cache_result: bool = True,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Calculate a formula with real-time data (standalone function).

    Args:
        formula_id: ID of the formula to calculate
        input_data: Input data for the calculation
        use_live_data: Whether to use live data
        cache_result: Whether to cache the result
        timeout_seconds: Timeout for the calculation

    Returns:
        Dictionary with calculation results
    """
    return await _global_realtime_service.calculate_formula_realtime(
        formula_id=formula_id,
        input_data=input_data,
        use_live_data=use_live_data,
        cache_result=cache_result,
        timeout_seconds=timeout_seconds
    )


async def process_batch_calculations(
    formula_id: str,
    batch_data: List[Dict[str, Any]],
    batch_size: int = 1000,
    use_parallel_processing: bool = True,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Process batch calculations for large datasets (standalone function).

    Args:
        formula_id: ID of the formula to calculate
        batch_data: List of input data for batch processing
        batch_size: Size of each batch
        use_parallel_processing: Whether to use parallel processing
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with batch processing results
    """
    return await _global_realtime_service.process_batch_calculations(
        formula_id=formula_id,
        batch_data=batch_data,
        batch_size=batch_size,
        use_parallel_processing=use_parallel_processing,
        progress_callback=progress_callback
    )


async def sync_live_data(
    data_source: str,
    sync_frequency: str = "minute",
    data_types: List[str] = None,
    auto_start: bool = True
) -> Dict[str, Any]:
    """
    Set up live data synchronization (standalone function).

    Args:
        data_source: Source of the data
        sync_frequency: How often to sync
        data_types: Types of data to sync
        auto_start: Whether to start syncing immediately

    Returns:
        Dictionary with sync configuration
    """
    return await _global_realtime_service.sync_live_data(
        data_source=data_source,
        sync_frequency=sync_frequency,
        data_types=data_types,
        auto_start=auto_start
    )


async def get_realtime_service_status() -> Dict[str, Any]:
    """
    Get the current status of the service (standalone function).

    Returns:
        Dictionary with service status information
    """
    return await _global_realtime_service.get_service_status()


async def optimize_realtime_performance() -> Dict[str, Any]:
    """
    Optimize service performance based on current metrics (standalone function).

    Returns:
        Dictionary with optimization results
    """
    return await _global_realtime_service.optimize_performance()



