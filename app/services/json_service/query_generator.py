"""
Query Generator Module
Handles INSERT query generation for SQL and NoSQL databases
"""
from typing import Dict, Any, Tuple, Optional, List


class QueryGenerator:
    """Generate INSERT queries from schema and data"""
    
    @staticmethod
    def generate_sql_insert(table_name: str, schema: Dict[str, Any], data_row: Dict[str, Any]) -> Tuple[Optional[str], Optional[tuple]]:
        """
        Generate INSERT query for PostgreSQL from schema and data
        
        Args:
            table_name: Name of the target table
            schema: Schema dictionary with properties and types
            data_row: Single row of data to insert
        
        Returns:
            Tuple of (query_string, values_tuple) or (None, None) if no data
        
        Example:
            query, values = generate_sql_insert('users', schema, {'name': 'John', 'age': 30})
            # Returns: ("INSERT INTO "users" ("name", "age") VALUES (%s, %s)", ('John', 30))
        """
        columns = []
        values = []
        placeholders = []
        
        properties = schema.get('properties', {})
        
        # Extract columns and values from data that match schema
        for col_name, col_info in properties.items():
            if col_name in data_row:
                columns.append(f'"{col_name}"')
                placeholders.append('%s')
                values.append(data_row[col_name])
        
        if not columns:
            return None, None
        
        # Build INSERT query
        query = f'INSERT INTO "{table_name}" ({", ".join(columns)}) VALUES ({", ".join(placeholders)})'
        return query, tuple(values)
    
    @staticmethod
    def generate_sql_batch_insert(table_name: str, schema: Dict[str, Any], data_rows: List[Dict[str, Any]]) -> List[Tuple[str, tuple]]:
        """
        Generate multiple INSERT queries for batch insertion
        
        Args:
            table_name: Name of the target table
            schema: Schema dictionary
            data_rows: List of data rows to insert
        
        Returns:
            List of (query, values) tuples
        """
        queries = []
        for row in data_rows:
            if isinstance(row, dict):
                query, values = QueryGenerator.generate_sql_insert(table_name, schema, row)
                if query:
                    queries.append((query, values))
        return queries
    
    @staticmethod
    def generate_update_query(table_name: str, schema: Dict[str, Any], data_row: Dict[str, Any], where_clause: str) -> Tuple[Optional[str], Optional[tuple]]:
        """
        Generate UPDATE query for PostgreSQL
        
        Args:
            table_name: Name of the target table
            schema: Schema dictionary
            data_row: Data to update
            where_clause: WHERE condition (e.g., 'id = %s')
        
        Returns:
            Tuple of (query_string, values_tuple)
        
        Example:
            query, values = generate_update_query('users', schema, {'name': 'Jane'}, 'id = %s')
            # Returns: ("UPDATE "users" SET "name" = %s WHERE id = %s", ('Jane',))
        """
        set_clauses = []
        values = []
        
        properties = schema.get('properties', {})
        
        for col_name, col_info in properties.items():
            if col_name in data_row:
                set_clauses.append(f'"{col_name}" = %s')
                values.append(data_row[col_name])
        
        if not set_clauses:
            return None, None
        
        query = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE {where_clause}'
        return query, tuple(values)
    
    @staticmethod
    def generate_select_query(table_name: str, schema: Dict[str, Any], where_conditions: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> Tuple[str, tuple]:
        """
        Generate SELECT query for PostgreSQL
        
        Args:
            table_name: Name of the target table
            schema: Schema dictionary
            where_conditions: Dictionary of column: value conditions
            limit: Optional row limit
        
        Returns:
            Tuple of (query_string, values_tuple)
        
        Example:
            query, values = generate_select_query('users', schema, {'age': 30}, limit=10)
            # Returns: ('SELECT * FROM "users" WHERE "age" = %s LIMIT 10', (30,))
        """
        query = f'SELECT * FROM "{table_name}"'
        values = []
        
        if where_conditions:
            conditions = []
            for col, val in where_conditions.items():
                conditions.append(f'"{col}" = %s')
                values.append(val)
            query += f' WHERE {" AND ".join(conditions)}'
        
        if limit:
            query += f' LIMIT {limit}'
        
        return query, tuple(values)
    
    @staticmethod
    def generate_delete_query(table_name: str, where_conditions: Dict[str, Any]) -> Tuple[str, tuple]:
        """
        Generate DELETE query for PostgreSQL
        
        Args:
            table_name: Name of the target table
            where_conditions: Dictionary of column: value conditions
        
        Returns:
            Tuple of (query_string, values_tuple)
        
        Example:
            query, values = generate_delete_query('users', {'id': 'usr_123'})
            # Returns: ('DELETE FROM "users" WHERE "id" = %s', ('usr_123',))
        """
        conditions = []
        values = []
        
        for col, val in where_conditions.items():
            conditions.append(f'"{col}" = %s')
            values.append(val)
        
        query = f'DELETE FROM "{table_name}" WHERE {" AND ".join(conditions)}'
        return query, tuple(values)
    
    @staticmethod
    def prepare_mongodb_document(schema: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare document for MongoDB insertion based on schema
        
        Args:
            schema: Schema dictionary
            data: Raw data dictionary
        
        Returns:
            Cleaned document ready for MongoDB insertion
        """
        document = {}
        properties = schema.get('properties', {})
        
        for field_name, field_info in properties.items():
            if field_name in data:
                document[field_name] = data[field_name]
        
        return document
    
    @staticmethod
    def prepare_mongodb_batch(schema: Dict[str, Any], data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare multiple documents for MongoDB batch insertion
        
        Args:
            schema: Schema dictionary
            data_list: List of data dictionaries
        
        Returns:
            List of cleaned documents
        """
        documents = []
        for data in data_list:
            if isinstance(data, dict):
                doc = QueryGenerator.prepare_mongodb_document(schema, data)
                if doc:
                    documents.append(doc)
        return documents
    
    @staticmethod
    def generate_mongodb_query(collection_name: str, operation: str, filters: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate MongoDB query dictionary
        
        Args:
            collection_name: Name of the collection
            operation: Operation type ('find', 'insert_one', 'update_one', 'delete_one')
            filters: Query filters
            data: Data for insert/update operations
        
        Returns:
            Query dictionary with operation details
        
        Example:
            query = generate_mongodb_query('users', 'find', {'age': {'$gte': 18}})
            # Returns: {'collection': 'users', 'operation': 'find', 'filter': {'age': {'$gte': 18}}}
        """
        query = {
            'collection': collection_name,
            'operation': operation
        }
        
        if filters:
            query['filter'] = filters
        
        if data:
            if operation == 'update_one':
                query['update'] = {'$set': data}
            else:
                query['data'] = data
        
        return query
