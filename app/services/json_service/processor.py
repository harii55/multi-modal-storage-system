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
    
    def process(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Process JSON file using YOUR SQL/NoSQL classification algorithm
        Then generate schemas, insert data, and return DB credentials
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
                # Step 3b: Process NoSQL - create collections and insert data
                return self._process_nosql_complete(data, entities, normalized)

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
        Complete SQL processing: create tables, insert data, return table info (NO credentials)
        """
        existing_tables = self.pg.list_tables()
        tables_info = []
        
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
            
            tables_info.append({
                'table_name': table_used,
                'fields': fields,
                'rows_inserted': rows_inserted
            })
        
        # Return only table info (NO database credentials)
        return {
            'schema_type': 'sql',
            'tables': tables_info,
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
    
    def _process_nosql_complete(self, original_data: Any, entities: Dict, normalized: Dict) -> Dict[str, Any]:
        """
        Complete NoSQL processing: create collections, insert data, return collection info
        """
        collections_info = []
        
        for entity_name, schema in normalized.items():
            # Generate and apply MongoDB validator
            validator = to_mongo_validator(schema)
            self.mongo.create_validator(entity_name, validator)
            
            # Insert data into collection
            entity_data = entities.get(entity_name, {})
            docs_inserted = self._insert_data_to_collection(entity_name, schema, entity_data)
            
            # Extract field information
            fields = []
            for field_name, field_info in schema.get('properties', {}).items():
                field_type = field_info.get('type', 'string')
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': field_name in schema.get('required', [])
                })
            
            collections_info.append({
                'collection_name': entity_name,
                'fields': fields,
                'documents_inserted': docs_inserted
            })
        
        # Return only collection info (no credentials)
        return {
            'schema_type': 'nosql',
            'collections': collections_info,
            'status': 'success'
        }