"""
AWS Glue Connector
Handles Glue Data Catalog interactions for schema discovery
"""

import boto3
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GlueConnector:
    """AWS Glue Data Catalog connector for schema and metadata"""

    def __init__(self, database: str, region: str = "us-east-1"):
        """
        Initialize Glue connector

        Args:
            database: Glue database name
            region: AWS region
        """
        self.database = database
        self.region = region
        self.glue_client = boto3.client('glue', region_name=region)
        logger.info(f"Initialized Glue connector for database: {database}")

    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get table schema from Glue Data Catalog

        Args:
            table_name: Name of the table

        Returns:
            Table schema information
        """
        loop = asyncio.get_event_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.glue_client.get_table(
                    DatabaseName=self.database,
                    Name=table_name
                )
            )

            table = response['Table']

            # Extract schema information
            columns = []
            for col in table.get('StorageDescriptor', {}).get('Columns', []):
                columns.append({
                    "name": col['Name'],
                    "type": col['Type'],
                    "comment": col.get('Comment', '')
                })

            # Extract partition keys
            partition_keys = []
            for pk in table.get('PartitionKeys', []):
                partition_keys.append({
                    "name": pk['Name'],
                    "type": pk['Type']
                })

            return {
                "success": True,
                "table_name": table_name,
                "database": self.database,
                "columns": columns,
                "partition_keys": partition_keys,
                "location": table.get('StorageDescriptor', {}).get('Location', ''),
                "input_format": table.get('StorageDescriptor', {}).get('InputFormat', ''),
                "output_format": table.get('StorageDescriptor', {}).get('OutputFormat', ''),
                "compressed": table.get('StorageDescriptor', {}).get('Compressed', False),
                "created_time": str(table.get('CreateTime', '')),
                "updated_time": str(table.get('UpdateTime', '')),
                "table_type": table.get('TableType', ''),
                "parameters": table.get('Parameters', {})
            }

        except self.glue_client.exceptions.EntityNotFoundException:
            logger.warning(f"Table not found in Glue: {table_name}")
            return {
                "success": False,
                "error": f"Table '{table_name}' not found in database '{self.database}'"
            }
        except Exception as e:
            logger.error(f"Failed to get Glue table schema: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def list_tables(self, filter_prefix: Optional[str] = None) -> List[str]:
        """
        List all tables in the Glue database

        Args:
            filter_prefix: Optional prefix to filter table names

        Returns:
            List of table names
        """
        loop = asyncio.get_event_loop()

        try:
            tables = []
            next_token = None

            while True:
                kwargs = {"DatabaseName": self.database}
                if next_token:
                    kwargs["NextToken"] = next_token

                response = await loop.run_in_executor(
                    None,
                    lambda: self.glue_client.get_tables(**kwargs)
                )

                for table in response.get('TableList', []):
                    table_name = table['Name']
                    if not filter_prefix or table_name.startswith(filter_prefix):
                        tables.append(table_name)

                next_token = response.get('NextToken')
                if not next_token:
                    break

            logger.info(f"Found {len(tables)} tables in Glue database")
            return tables

        except Exception as e:
            logger.error(f"Failed to list Glue tables: {e}")
            return []

    async def get_table_partitions(
        self,
        table_name: str,
        max_partitions: int = 100
    ) -> Dict[str, Any]:
        """
        Get partition information for a table

        Args:
            table_name: Name of the table
            max_partitions: Maximum number of partitions to return

        Returns:
            Partition information
        """
        loop = asyncio.get_event_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.glue_client.get_partitions(
                    DatabaseName=self.database,
                    TableName=table_name,
                    MaxResults=max_partitions
                )
            )

            partitions = []
            for partition in response.get('Partitions', []):
                partitions.append({
                    "values": partition.get('Values', []),
                    "location": partition.get('StorageDescriptor', {}).get('Location', ''),
                    "created_time": str(partition.get('CreationTime', '')),
                    "parameters": partition.get('Parameters', {})
                })

            return {
                "success": True,
                "table_name": table_name,
                "partition_count": len(partitions),
                "partitions": partitions,
                "has_more": 'NextToken' in response
            }

        except self.glue_client.exceptions.EntityNotFoundException:
            return {
                "success": False,
                "error": f"Table '{table_name}' not found"
            }
        except Exception as e:
            logger.error(f"Failed to get partitions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the Glue database

        Returns:
            Database information
        """
        loop = asyncio.get_event_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.glue_client.get_database(Name=self.database)
            )

            database = response['Database']

            return {
                "success": True,
                "name": database['Name'],
                "description": database.get('Description', ''),
                "location_uri": database.get('LocationUri', ''),
                "created_time": str(database.get('CreateTime', '')),
                "parameters": database.get('Parameters', {})
            }

        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_tables(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for tables by name or column names

        Args:
            search_term: Term to search for

        Returns:
            List of matching tables with schema info
        """
        try:
            all_tables = await self.list_tables()
            matching_tables = []

            for table_name in all_tables:
                if search_term.lower() in table_name.lower():
                    schema = await self.get_table_schema(table_name)
                    if schema.get('success'):
                        matching_tables.append({
                            "table_name": table_name,
                            "match_type": "name",
                            "columns": schema.get('columns', [])
                        })
                    continue

                # Search in column names
                schema = await self.get_table_schema(table_name)
                if schema.get('success'):
                    matching_columns = [
                        col for col in schema.get('columns', [])
                        if search_term.lower() in col['name'].lower()
                    ]
                    if matching_columns:
                        matching_tables.append({
                            "table_name": table_name,
                            "match_type": "column",
                            "matching_columns": matching_columns,
                            "all_columns": schema.get('columns', [])
                        })

            return matching_tables

        except Exception as e:
            logger.error(f"Failed to search tables: {e}")
            return []

    async def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Get statistics for a table from Glue

        Args:
            table_name: Name of the table

        Returns:
            Table statistics if available
        """
        try:
            schema = await self.get_table_schema(table_name)
            if not schema.get('success'):
                return schema

            # Get partition count
            partitions = await self.get_table_partitions(table_name, max_partitions=1)

            stats = {
                "success": True,
                "table_name": table_name,
                "column_count": len(schema.get('columns', [])),
                "partition_key_count": len(schema.get('partition_keys', [])),
                "has_partitions": partitions.get('partition_count', 0) > 0,
                "location": schema.get('location', ''),
                "table_type": schema.get('table_type', ''),
                "compressed": schema.get('compressed', False)
            }

            # Try to get record count from parameters
            parameters = schema.get('parameters', {})
            if 'numRows' in parameters:
                stats['estimated_rows'] = int(parameters['numRows'])
            if 'totalSize' in parameters:
                stats['estimated_size_bytes'] = int(parameters['totalSize'])

            return stats

        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
