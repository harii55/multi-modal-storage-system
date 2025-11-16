import json
from typing import Dict, Any
from app.services.json_service.infer_type.primitive import infer_primitive
from app.services.json_service.infer_type.infer_object import infer_object
from app.services.json_service.infer_type.infer_array import infer_array
from app.services.json_service.entity_extractor.detect_entities import detect_entities_from_json
from app.services.json_service.entity_extractor.detect_relationships import detect_relationships
from app.services.json_service.normalizer.normalize_schema import normalize_entities
from app.services.json_service.table_generator.sql_generator import generate_create_table
from app.services.json_service.table_generator.nosql_generator import to_mongo_validator
from app.services.json_service.query_generator import QueryGenerator
from app.db.postgres.client import PostgresClient
from app.db.mongo.client import MongoClient

class JsonProcessor:
    def __init__(self):
        self.pg = PostgresClient()
        self.mongo = MongoClient()
    
    def infer_fn(self, value):
        """Type inference function for recursive schema detection"""
        if isinstance(value, dict):
            return ('object', infer_object(value, self.infer_fn))
        if isinstance(value, list):
            return ('array', infer_array(value, self.infer_fn))
        t, m = infer_primitive(value)
        return (t, m)
    
    def process(self, file_bytes: bytes, user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        Process JSON file using YOUR SQL/NoSQL classification algorithm
        Then generate schemas, insert data, and return DB credentials
        
        Args:
            file_bytes: JSON file content
            user_id: User identifier (used as collection name for NoSQL)
        """
        try:
            data = json.loads(file_bytes.decode('utf-8'))

            # Step 1: Use YOUR algorithm to classify SQL vs NOSQL
            schema_type = self._detect_schema_type(data)

            # Step 2: Extract entities and relationships
            entities = detect_entities_from_json(data)
            relationships = detect_relationships(entities)
            normalized = normalize_entities(entities, self.infer_fn)

            if schema_type == 'sql':
                # Step 3a: Process SQL - create tables and insert data
                return self._process_sql_complete(data, entities, normalized, relationships)
            else:
                # Step 3b: Process NoSQL - create collections and insert data (use user_id as collection name)
                return self._process_nosql_complete(data, entities, normalized, user_id)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def _detect_schema_type(self, data: Any) -> str:
        """
        Detect if JSON schema is SQL or NOSQL using custom algorithm
        Returns 'sql' or 'nosql'
        """
        decision = self._classify_json(data)
        return decision.lower()

    def _get_json_depth(self, obj):
        """Calculate the maximum depth of the JSON object"""
        if isinstance(obj, dict):
            if not obj:
                return 1
            return 1 + max(self._get_json_depth(v) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return 1
            return 1 + max(self._get_json_depth(item) for item in obj)
        else:
            return 0

    def _depth_score(self, json_obj, threshold=3, weight=0.4):
        """Score based on JSON depth - deeper structures suggest NoSQL"""
        depth = self._get_json_depth(json_obj)
        return weight if depth > threshold else 0

    def _array_level(self, json_obj):
        """Check if JSON contains arrays of objects (suggests tabular/SQL data)"""
        if isinstance(json_obj, dict):
            for v in json_obj.values():
                if self._array_level(v) == 1:
                    return 1
            return 0
        elif isinstance(json_obj, list):
            if any(isinstance(item, dict) for item in json_obj):
                return 1
            for item in json_obj:
                if self._array_level(item) == 1:
                    return 1
            return 0
        else:
            return 0

    def _array_score(self, json_obj, weight=0.35):
        """Score based on presence of arrays containing objects"""
        return weight if self._array_level(json_obj) == 1 else 0

    def _schema_consistency_score(self, json_obj, weight=0.25):
        """Score based on schema consistency in arrays of objects"""
        def check_inconsistency(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    if check_inconsistency(v):
                        return True
                return False
            elif isinstance(obj, list):
                obj_arrays = [i for i in obj if isinstance(i, dict)]
                if len(obj_arrays) > 1:
                    key_sets = [set(i.keys()) for i in obj_arrays]
                    first_keys = key_sets[0]
                    for k in key_sets[1:]:
                        if k != first_keys:
                            return True
                for item in obj:
                    if check_inconsistency(item):
                        return True
                return False
            else:
                return False

        inconsistent = check_inconsistency(json_obj)
        return weight if inconsistent else 0

    def _classify_json(self, json_obj, threshold=0.5):
        """Classify JSON as SQL or NoSQL based on combined scores"""
        d_score = self._depth_score(json_obj)
        a_score = self._array_score(json_obj)
        s_score = self._schema_consistency_score(json_obj)

        total_score = d_score + a_score + s_score
        decision = "NoSQL" if total_score >= threshold else "SQL"

        return decision
    

    
    def _insert_data_to_table(self, table_name: str, schema: Dict[str, Any], data: Any) -> int:
        """
        Insert data into PostgreSQL table using QueryGenerator
        Returns: number of rows inserted
        """
        rows_inserted = 0
        
        if isinstance(data, list):
            # Array of objects - insert each
            for row in data:
                if isinstance(row, dict):
                    query, values = QueryGenerator.generate_sql_insert(table_name, schema, row)
                    if query:
                        try:
                            self.pg.execute(query, values)
                            rows_inserted += 1
                        except Exception as e:
                            print(f"Insert error for {table_name}: {e}")
        elif isinstance(data, dict):
            # Single object - insert once
            query, values = QueryGenerator.generate_sql_insert(table_name, schema, data)
            if query:
                try:
                    self.pg.execute(query, values)
                    rows_inserted = 1
                except Exception as e:
                    print(f"Insert error for {table_name}: {e}")
        
        return rows_inserted
    

    
    def _process_sql_complete(self, original_data: Any, entities: Dict, normalized: Dict, relationships: list) -> Dict[str, Any]:
        """
        Complete SQL processing: create tables, insert data, return table info with sample queries
        """
        existing_tables = self.pg.list_tables()
        tables_info = []
        all_queries = []
        
        for entity_name, schema in normalized.items():
            # Generate and execute CREATE TABLE
            ddl = generate_create_table(entity_name, schema, relationships)
            
            table_used = entity_name
            if entity_name not in existing_tables:
                self.pg.execute(ddl)
            
            # Insert data into table
            entity_data = entities.get(entity_name, {})
            rows_inserted = self._insert_data_to_table(table_used, schema, entity_data)
            
            # Extract field information
            fields = []
            for field_name, field_info in schema.get('properties', {}).items():
                field_type = field_info.get('type', 'string')
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': field_name in schema.get('required', [])
                })
            
            # Generate sample queries (1-3 queries per table)
            sample_data = entity_data if isinstance(entity_data, dict) else (entity_data[0] if isinstance(entity_data, list) and entity_data else {})
            
            if sample_data:
                # 1. INSERT query
                insert_query, insert_values = QueryGenerator.generate_sql_insert(table_used, schema, sample_data)
                if insert_query:
                    all_queries.append({
                        'type': 'INSERT',
                        'table': table_used,
                        'query': insert_query,
                        'sample_values': list(insert_values)
                    })
                
                # 2. SELECT query
                columns = list(schema.get('properties', {}).keys())[:5]  # First 5 columns
                select_query, _ = QueryGenerator.generate_select_query(table_used, columns, limit=10)
                if select_query:
                    all_queries.append({
                        'type': 'SELECT',
                        'table': table_used,
                        'query': select_query
                    })
                
                # 3. UPDATE query (if there's a primary key or id field)
                pk_field = None
                for field in ['id', 'uuid', list(schema.get('properties', {}).keys())[0] if schema.get('properties', {}) else None]:
                    if field and field in schema.get('properties', {}):
                        pk_field = field
                        break
                
                if pk_field and pk_field in sample_data:
                    update_data = {k: v for k, v in list(sample_data.items())[:2] if k != pk_field}
                    if update_data:
                        update_query, update_values = QueryGenerator.generate_update_query(
                            table_used, schema, update_data, {pk_field: sample_data[pk_field]}
                        )
                        if update_query:
                            all_queries.append({
                                'type': 'UPDATE',
                                'table': table_used,
                                'query': update_query,
                                'sample_values': list(update_values)
                            })
            
            tables_info.append({
                'table_name': table_used,
                'fields': fields,
                'rows_inserted': rows_inserted
            })
        
        # Return table info with sample queries (limit to first 3 queries)
        return {
            'schema_type': 'sql',
            'tables': tables_info,
            'queries': all_queries[:3],
            'status': 'success'
        }
    

    
    def _insert_data_to_collection(self, collection_name: str, schema: Dict[str, Any], data: Any) -> int:
        """
        Insert data into MongoDB collection using QueryGenerator
        Returns: number of documents inserted
        """
        docs_inserted = 0
        collection = self.mongo.get_collection(collection_name)
        
        try:
            if isinstance(data, list):
                # Array of documents - prepare and insert
                documents = QueryGenerator.prepare_mongodb_batch(schema, data)
                if documents:
                    result = collection.insert_many(documents)
                    docs_inserted = len(result.inserted_ids)
            elif isinstance(data, dict):
                # Single document - prepare and insert
                document = QueryGenerator.prepare_mongodb_document(schema, data)
                if document:
                    result = collection.insert_one(document)
                    docs_inserted = 1
        except Exception as e:
            print(f"MongoDB insert error for {collection_name}: {e}")
        
        return docs_inserted
    
    def _process_nosql_complete(self, original_data: Any, entities: Dict, normalized: Dict, user_id: str) -> Dict[str, Any]:
        """
        Complete NoSQL processing: create user-specific collection, insert data, return collection info with sample queries
        
        Args:
            original_data: Original JSON data
            entities: Detected entities
            normalized: Normalized schemas
            user_id: User identifier to use as collection name
        """
        # Use user_id as collection name (one collection per user)
        collection_name = user_id
        
        # Get the root entity schema (the main document structure)
        root_schema = normalized.get('root', {})
        
        # Generate and apply MongoDB validator
        validator = to_mongo_validator(root_schema)
        self.mongo.create_validator(collection_name, validator)
        
        # Insert the complete original data as a single document
        docs_inserted = self._insert_data_to_collection(collection_name, root_schema, original_data)
        
        # Extract field information from root schema
        fields = []
        for field_name, field_info in root_schema.get('properties', {}).items():
            field_type = field_info.get('type', 'string')
            fields.append({
                'name': field_name,
                'type': field_type,
                'required': field_name in root_schema.get('required', [])
            })
        
        # Generate sample MongoDB queries using original data
        all_queries = []
        
        if original_data:
            # 1. insertOne query - show the complete document that was inserted
            insert_doc = QueryGenerator.prepare_mongodb_document(root_schema, original_data)
            if insert_doc:
                all_queries.append({
                    'type': 'insertOne',
                    'collection': collection_name,
                    'operation': f'db.{collection_name}.insertOne(...)',
                    'document': insert_doc
                })
            
            # 2. find query - use first available field for filter
            if isinstance(original_data, dict) and original_data:
                first_key = list(original_data.keys())[0]
                first_value = original_data[first_key]
                
                # Create a simple filter based on first nested field
                if isinstance(first_value, dict) and first_value:
                    nested_key = list(first_value.keys())[0]
                    nested_value = first_value[nested_key]
                    filter_obj = {first_key: {nested_key: nested_value}} if not isinstance(nested_value, (dict, list)) else {first_key: first_value}
                else:
                    filter_obj = {first_key: first_value}
                
                all_queries.append({
                    'type': 'find',
                    'collection': collection_name,
                    'operation': f'db.{collection_name}.find(...)',
                    'filter': filter_obj
                })
            
            # 3. updateOne query
            if isinstance(original_data, dict) and len(original_data) >= 2:
                first_key = list(original_data.keys())[0]
                second_key = list(original_data.keys())[1]
                
                all_queries.append({
                    'type': 'updateOne',
                    'collection': collection_name,
                    'operation': f'db.{collection_name}.updateOne(...)',
                    'filter': {first_key: original_data[first_key]},
                    'update': {'$set': {second_key: original_data[second_key]}}
                })
        
        collections_info = [{
            'collection_name': collection_name,
            'fields': fields,
            'documents_inserted': docs_inserted
        }]
        
        # Return collection info with sample queries (limit to first 3 queries)
        return {
            'schema_type': 'nosql',
            'collections': collections_info,
            'queries': all_queries[:3],
            'status': 'success'
        }