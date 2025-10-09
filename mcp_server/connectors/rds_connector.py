"""
RDS PostgreSQL Connector
Handles database connections and queries for NBA simulator data
"""

import asyncio
import psycopg2
import psycopg2.extras
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class RDSConnector:
    """PostgreSQL connector for NBA simulator database"""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ):
        """Initialize RDS connection parameters"""
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self._connection_pool = []
        self.max_pool_size = 5
        
    def _get_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.username} "
            f"password={self.password}"
        )
    
    def connect(self):
        """Establish database connection"""
        try:
            if not self.connection or self.connection.closed:
                self.connection = psycopg2.connect(
                    self._get_connection_string(),
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                logger.info(f"Connected to RDS database: {self.database}")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise
    
    async def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_all: bool = True,
        max_rows: int = 1000
    ) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        
        # Run synchronous DB operation in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._execute_sync,
            query,
            params,
            fetch_all,
            max_rows
        )
        return result
    
    def _execute_sync(
        self,
        query: str,
        params: Optional[tuple],
        fetch_all: bool,
        max_rows: int
    ) -> Dict[str, Any]:
        """Synchronous query execution"""
        start_time = datetime.now()

        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                # Add row limit if SELECT query (but not for simple metadata queries)
                query_stripped = query.strip().upper()
                if (query_stripped.startswith('SELECT') and
                    'LIMIT' not in query_stripped and
                    'FROM' in query_stripped):  # Only add LIMIT if there's a FROM clause
                    query = f"{query.rstrip().rstrip(';')} LIMIT {max_rows}"

                cursor.execute(query, params)
                
                if fetch_all:
                    rows = cursor.fetchall()
                    row_count = len(rows)
                else:
                    rows = None
                    row_count = cursor.rowcount
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "rows": rows,
                    "row_count": row_count,
                    "columns": columns,
                    "execution_time": execution_time,
                    "query": query[:200] + "..." if len(query) > 200 else query
                }
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query[:200] + "..." if len(query) > 200 else query,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
            AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        result = await self.execute_query(query, (table_name,))
        
        if result["success"]:
            return {
                "success": True,
                "table_name": table_name,
                "columns": result["rows"],
                "column_count": len(result["rows"])
            }
        return result
    
    async def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics (row count, size, indexes)"""
        
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_result = await self.execute_query(count_query)
        
        # Get table size
        size_query = """
        SELECT 
            pg_size_pretty(pg_total_relation_size(%s)) as total_size,
            pg_size_pretty(pg_relation_size(%s)) as table_size,
            pg_size_pretty(pg_indexes_size(%s)) as indexes_size
        """
        size_result = await self.execute_query(
            size_query,
            (table_name, table_name, table_name)
        )
        
        # Get indexes
        index_query = """
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
            AND tablename = %s;
        """
        index_result = await self.execute_query(index_query, (table_name,))
        
        if all([count_result["success"], size_result["success"], index_result["success"]]):
            return {
                "success": True,
                "table_name": table_name,
                "row_count": count_result["rows"][0]["count"],
                "total_size": size_result["rows"][0]["total_size"],
                "table_size": size_result["rows"][0]["table_size"],
                "indexes_size": size_result["rows"][0]["indexes_size"],
                "indexes": index_result["rows"]
            }
        
        return {
            "success": False,
            "error": "Failed to get complete statistics"
        }
    
    async def explain_query(self, query: str) -> Dict[str, Any]:
        """Get EXPLAIN plan for a query"""
        explain_query = f"EXPLAIN (FORMAT JSON) {query}"
        
        result = await self.execute_query(explain_query)
        
        if result["success"] and result["rows"]:
            return {
                "success": True,
                "explain_plan": result["rows"][0]["QUERY PLAN"],
                "query": query
            }
        return result
    
    async def list_tables(self) -> List[str]:
        """List all tables in the database"""
        query = """
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """
        
        result = await self.execute_query(query)
        
        if result["success"]:
            return [row["tablename"] for row in result["rows"]]
        return []
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("RDS connection closed")
