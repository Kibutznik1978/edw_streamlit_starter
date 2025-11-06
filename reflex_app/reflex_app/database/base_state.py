"""Base database state class with CRUD operations."""

import reflex as rx
from typing import Optional, List, Dict, Any
from supabase import Client
from ..auth.auth_state import AuthState


class DatabaseState(AuthState):
    """Base state class with database access.

    Extends AuthState to provide authenticated database operations.
    All queries automatically enforce RLS policies.
    """

    def get_db_client(self) -> Optional[Client]:
        """Get authenticated database client.

        Returns:
            Authenticated Supabase client or None if not authenticated
        """
        return self.get_authenticated_client()

    async def query_table(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query database table with RLS enforcement.

        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of column: value filters
            order_by: Column to order by
            limit: Maximum number of rows to return

        Returns:
            List of rows as dictionaries
        """
        client = self.get_db_client()
        if not client:
            return []

        try:
            query = client.table(table).select(columns)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # Apply ordering
            if order_by:
                query = query.order(order_by)

            # Apply limit
            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            print(f"Query error: {e}")
            self.error_message = f"Database query failed: {str(e)}"
            return []

    async def insert_row(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Insert row into table.

        Args:
            table: Table name
            data: Row data as dictionary

        Returns:
            Inserted row or None if failed
        """
        client = self.get_db_client()
        if not client:
            self.error_message = "Not authenticated"
            return None

        try:
            response = client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Insert error: {e}")
            self.error_message = f"Failed to insert row: {str(e)}"
            return None

    async def update_row(
        self,
        table: str,
        row_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Update row in table.

        Args:
            table: Table name
            row_id: Row ID to update
            data: Updated data as dictionary

        Returns:
            True if successful, False otherwise
        """
        client = self.get_db_client()
        if not client:
            self.error_message = "Not authenticated"
            return False

        try:
            response = client.table(table).update(data).eq("id", row_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Update error: {e}")
            self.error_message = f"Failed to update row: {str(e)}"
            return False

    async def delete_row(
        self,
        table: str,
        row_id: str
    ) -> bool:
        """Delete row from table.

        Args:
            table: Table name
            row_id: Row ID to delete

        Returns:
            True if successful, False otherwise
        """
        client = self.get_db_client()
        if not client:
            self.error_message = "Not authenticated"
            return False

        try:
            response = client.table(table).delete().eq("id", row_id).execute()
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            self.error_message = f"Failed to delete row: {str(e)}"
            return False
