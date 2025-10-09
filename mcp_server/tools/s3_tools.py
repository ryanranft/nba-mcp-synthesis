"""
S3 Tools for MCP Server
Provides tools for interacting with S3 data lake
"""

import logging
import io
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
from mcp_server.connectors.s3_connector import S3Connector

logger = logging.getLogger(__name__)


class S3Tools:
    """Tools for S3 operations"""

    def __init__(self, s3_connector: S3Connector):
        """Initialize S3 tools with S3 connector"""
        self.s3 = s3_connector
        self.supported_formats = ['.parquet', '.csv', '.json', '.txt', '.log']

    async def fetch_s3_sample(
        self,
        file_path: str,
        sample_size: int = 1000,
        max_file_size_mb: int = 1
    ) -> Dict[str, Any]:
        """
        Fetch sample data from S3 file with size limits.

        Args:
            file_path: Path to file in S3 bucket
            sample_size: Number of rows/lines to sample (default: 1000)
            max_file_size_mb: Maximum file size in MB to process (default: 1)

        Returns:
            Dict with sample data or error information
        """
        try:
            # Get file metadata first to check size
            logger.info(f"Checking file metadata for: {file_path}")
            metadata = await self.s3.get_file_metadata(file_path)

            if not metadata["success"]:
                return metadata

            # Check file size limit
            file_size_mb = metadata["size"] / (1024 * 1024)
            if file_size_mb > max_file_size_mb:
                logger.warning(f"File too large: {file_size_mb:.2f}MB > {max_file_size_mb}MB")
                return {
                    "success": False,
                    "error": f"File size ({file_size_mb:.2f}MB) exceeds maximum ({max_file_size_mb}MB)",
                    "file_path": file_path,
                    "file_size_mb": file_size_mb
                }

            # Get file extension
            file_ext = Path(file_path).suffix.lower()

            # Check if file type is supported
            if file_ext not in self.supported_formats:
                logger.warning(f"Unsupported file type: {file_ext}")
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}. Supported: {', '.join(self.supported_formats)}",
                    "file_path": file_path
                }

            # Handle different file types
            if file_ext == '.parquet':
                return await self._fetch_parquet_sample(file_path, sample_size)
            elif file_ext == '.csv':
                return await self._fetch_csv_sample(file_path, sample_size)
            elif file_ext == '.json':
                return await self._fetch_json_sample(file_path, sample_size)
            else:
                # Text files (txt, log, etc.)
                return await self.s3.fetch_file_sample(
                    file_path=file_path,
                    sample_size=sample_size,
                    sample_type="lines"
                )

        except Exception as e:
            logger.error(f"Error fetching S3 sample: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    async def _fetch_parquet_sample(
        self,
        file_path: str,
        sample_size: int
    ) -> Dict[str, Any]:
        """Fetch sample from parquet file"""
        try:
            # Get full file content
            result = await self.s3.fetch_file_sample(
                file_path=file_path,
                sample_type="full"
            )

            if not result["success"]:
                return result

            # Read parquet with pandas
            import pyarrow.parquet as pq
            table = pq.read_table(io.BytesIO(result["sample_content"].encode('latin-1')))
            df = table.to_pandas()

            # Sample rows
            sample_df = df.head(sample_size)

            return {
                "success": True,
                "file_path": file_path,
                "format": "parquet",
                "total_rows": len(df),
                "sample_rows": len(sample_df),
                "columns": list(df.columns),
                "sample_data": sample_df.to_dict(orient='records'),
                "file_size": result["file_size"],
                "last_modified": result["last_modified"]
            }

        except Exception as e:
            logger.error(f"Error reading parquet file: {e}")
            return {
                "success": False,
                "error": f"Failed to read parquet file: {str(e)}",
                "file_path": file_path
            }

    async def _fetch_csv_sample(
        self,
        file_path: str,
        sample_size: int
    ) -> Dict[str, Any]:
        """Fetch sample from CSV file"""
        try:
            # Get full file content
            result = await self.s3.fetch_file_sample(
                file_path=file_path,
                sample_type="full"
            )

            if not result["success"]:
                return result

            # Read CSV with pandas
            df = pd.read_csv(io.StringIO(result["sample_content"]))

            # Sample rows
            sample_df = df.head(sample_size)

            return {
                "success": True,
                "file_path": file_path,
                "format": "csv",
                "total_rows": len(df),
                "sample_rows": len(sample_df),
                "columns": list(df.columns),
                "sample_data": sample_df.to_dict(orient='records'),
                "file_size": result["file_size"],
                "last_modified": result["last_modified"]
            }

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return {
                "success": False,
                "error": f"Failed to read CSV file: {str(e)}",
                "file_path": file_path
            }

    async def _fetch_json_sample(
        self,
        file_path: str,
        sample_size: int
    ) -> Dict[str, Any]:
        """Fetch sample from JSON file"""
        try:
            # Get full file content
            result = await self.s3.fetch_file_sample(
                file_path=file_path,
                sample_type="full"
            )

            if not result["success"]:
                return result

            # Parse JSON
            import json
            data = json.loads(result["sample_content"])

            # Handle different JSON structures
            if isinstance(data, list):
                sample_data = data[:sample_size]
                total_items = len(data)
            elif isinstance(data, dict):
                sample_data = data
                total_items = 1
            else:
                sample_data = data
                total_items = 1

            return {
                "success": True,
                "file_path": file_path,
                "format": "json",
                "total_items": total_items,
                "sample_items": len(sample_data) if isinstance(sample_data, list) else 1,
                "sample_data": sample_data,
                "file_size": result["file_size"],
                "last_modified": result["last_modified"]
            }

        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return {
                "success": False,
                "error": f"Failed to read JSON file: {str(e)}",
                "file_path": file_path
            }

    async def list_s3_files(
        self,
        prefix: str = "",
        max_keys: int = 100
    ) -> Dict[str, Any]:
        """
        List files in S3 bucket with optional prefix filter.

        Args:
            prefix: Prefix filter for file paths (default: "")
            max_keys: Maximum number of files to return (default: 100)

        Returns:
            Dict with file listing or error
        """
        try:
            logger.info(f"Listing S3 files with prefix: '{prefix}'")
            result = await self.s3.list_files(prefix=prefix, max_keys=max_keys)

            if result["success"]:
                logger.info(f"Found {result['file_count']} files")

            return result

        except Exception as e:
            logger.error(f"Error listing S3 files: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "prefix": prefix
            }

    async def get_s3_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata about an S3 file.

        Args:
            file_path: Path to file in S3 bucket

        Returns:
            Dict with file metadata or error
        """
        try:
            logger.info(f"Getting file info for: {file_path}")
            result = await self.s3.get_file_metadata(file_path)

            if result["success"]:
                # Add computed fields
                file_size_mb = result["size"] / (1024 * 1024)
                result["size_mb"] = round(file_size_mb, 2)
                result["extension"] = Path(file_path).suffix
                result["filename"] = Path(file_path).name

                logger.info(f"File info retrieved: {result['size_mb']}MB, {result['extension']}")

            return result

        except Exception as e:
            logger.error(f"Error getting S3 file info: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    async def search_s3_files(
        self,
        prefix: str = "",
        extension: Optional[str] = None,
        max_keys: int = 100
    ) -> Dict[str, Any]:
        """
        Search for files in S3 with filters.

        Args:
            prefix: Prefix filter for file paths
            extension: File extension filter (e.g., ".parquet")
            max_keys: Maximum number of files to return

        Returns:
            Dict with filtered file listing
        """
        try:
            logger.info(f"Searching S3 files: prefix='{prefix}', ext={extension}")

            # Get file listing
            result = await self.s3.list_files(prefix=prefix, max_keys=max_keys)

            if not result["success"]:
                return result

            # Filter by extension if provided
            files = result["files"]
            if extension:
                files = [f for f in files if f["key"].endswith(extension)]

            return {
                "success": True,
                "bucket": result["bucket"],
                "prefix": prefix,
                "extension_filter": extension,
                "file_count": len(files),
                "files": files,
                "truncated": result.get("truncated", False)
            }

        except Exception as e:
            logger.error(f"Error searching S3 files: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "prefix": prefix,
                "extension": extension
            }
