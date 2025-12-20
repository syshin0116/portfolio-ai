"""Supabase database connection and utilities.

This module provides:
1. AsyncPostgresSaver for LangGraph checkpointing
2. Direct database connections for custom queries
3. Conversation history management
4. Vector storage utilities (pgvector)
"""

from __future__ import annotations

import os
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from src.core.logger import get_logger


logger = get_logger(__name__)


class SupabaseClient:
    """Supabase database client with connection pooling."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize Supabase client.

        Args:
            connection_string: PostgreSQL connection string.
                Defaults to SUPABASE_CONNECTION_STRING env var.
        """
        self.connection_string = connection_string or os.getenv(
            "SUPABASE_CONNECTION_STRING"
        )
        if not self.connection_string:
            raise ValueError(
                "SUPABASE_CONNECTION_STRING environment variable is required"
            )

        self._pool: Optional[AsyncConnectionPool] = None
        self._checkpointer: Optional[AsyncPostgresSaver] = None

    async def initialize(self):
        """Initialize connection pool and checkpointer."""
        if self._pool is None:
            logger.info("Initializing Supabase connection pool")
            self._pool = AsyncConnectionPool(
                conninfo=self.connection_string,
                min_size=2,
                max_size=10,
                timeout=30,
            )
            await self._pool.wait()
            logger.info("Supabase connection pool initialized")

        if self._checkpointer is None:
            logger.info("Initializing AsyncPostgresSaver for checkpointing")
            self._checkpointer = AsyncPostgresSaver.from_conn_string(
                self.connection_string
            )
            await self._checkpointer.setup()
            logger.info("AsyncPostgresSaver initialized")

    async def close(self):
        """Close connection pool and cleanup resources."""
        if self._pool:
            logger.info("Closing Supabase connection pool")
            await self._pool.close()
            self._pool = None

        # Note: AsyncPostgresSaver doesn't have a close method
        self._checkpointer = None

    @property
    def pool(self) -> AsyncConnectionPool:
        """Get connection pool.

        Returns:
            AsyncConnectionPool instance

        Raises:
            RuntimeError: If pool is not initialized
        """
        if self._pool is None:
            raise RuntimeError(
                "Connection pool not initialized. Call initialize() first."
            )
        return self._pool

    @property
    def checkpointer(self) -> AsyncPostgresSaver:
        """Get LangGraph checkpointer.

        Returns:
            AsyncPostgresSaver instance for LangGraph persistence

        Raises:
            RuntimeError: If checkpointer is not initialized
        """
        if self._checkpointer is None:
            raise RuntimeError(
                "Checkpointer not initialized. Call initialize() first."
            )
        return self._checkpointer

    async def get_connection(self) -> AsyncConnection:
        """Get a database connection from the pool.

        Returns:
            AsyncConnection instance

        Example:
            ```python
            async with client.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM users")
                    results = await cur.fetchall()
            ```
        """
        return await self.pool.getconn()

    async def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            Query results

        Example:
            ```python
            results = await client.execute_query(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            ```
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def execute_command(self, command: str, params: tuple = ()):
        """Execute a command without returning results.

        Args:
            command: SQL command string
            params: Command parameters tuple

        Example:
            ```python
            await client.execute_command(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                (name, email)
            )
            ```
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(command, params)
                await conn.commit()


# Global client instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance.

    Returns:
        SupabaseClient instance

    Raises:
        RuntimeError: If client is not initialized
    """
    global _supabase_client
    if _supabase_client is None:
        raise RuntimeError(
            "Supabase client not initialized. Call init_supabase() first."
        )
    return _supabase_client


async def init_supabase(connection_string: Optional[str] = None):
    """Initialize global Supabase client.

    Args:
        connection_string: PostgreSQL connection string.
            Defaults to SUPABASE_CONNECTION_STRING env var.
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient(connection_string)
        await _supabase_client.initialize()


async def close_supabase():
    """Close global Supabase client and cleanup resources."""
    global _supabase_client
    if _supabase_client:
        await _supabase_client.close()
        _supabase_client = None
