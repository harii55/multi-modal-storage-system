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
from app.services.json_service.schema_checker.compare_schema import compare_table_schema
from app.services.json_service.schema_checker.alter_generator import generate_alter_statements
from app.services.json_service.schema_checker.versioner import next_version_name
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
        Then generate and apply schemas to databases
        """
        try:
            data = json.loads(file_bytes.decode('utf-8'))

            # Step 1: Use YOUR algorithm to classify SQL vs NOSQL
            schema_type = self._detect_schema_type(data)

            # Step 2: Extract entities and relationships
            entities = detect_entities_from_json(data)
            relationships = detect_relationships(entities)
            normalized = normalize_entities(entities, self.infer_fn)

            results = {
                'schema_type': schema_type,
                'sql': {},
                'nosql': {},
                'actions': []
            }

            if schema_type == 'sql':
                # Step 3a: Generate and apply SQL schemas
                results = self._process_sql_schema(normalized, relationships, results)
            else:
                # Step 3b: Generate and apply NoSQL schemas
                results = self._process_nosql_schema(normalized, results)

            results['status'] = 'success'
            return results

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
    
    def _process_sql_schema(self, normalized, relationships, results):
        """Process SQL schema generation and application"""
        existing_tables = self.pg.list_tables()
        
        for entity_name, schema in normalized.items():
            # Generate CREATE TABLE DDL
            ddl = generate_create_table(entity_name, schema, relationships)
            results['sql'][entity_name] = ddl
            
            if entity_name in existing_tables:
                # Table exists - check for schema changes
                existing_cols = self.pg.fetch_table_columns(entity_name)
                gen_cols = {}
                for k, v in schema.get('properties', {}).items():
                    t = v.get('type')
                    gen_cols[k] = t
                
                cmp = compare_table_schema(existing_cols, gen_cols)
                
                if cmp['compatible'] and cmp['add_columns']:
                    # Add new columns with ALTER
                    stmts = generate_alter_statements(entity_name, {c: 'TEXT' for c in cmp['add_columns']})
                    for s in stmts:
                        self.pg.execute(s)
                    results['actions'].append({
                        'table': entity_name,
                        'action': 'alter',
                        'stmts': stmts
                    })
                elif not cmp['compatible']:
                    # Incompatible changes - create versioned table
                    newname = next_version_name(entity_name, existing_tables)
                    ddl_v = ddl.replace(f'"{entity_name}"', f'"{newname}"')
                    self.pg.execute(ddl_v)
                    results['actions'].append({
                        'table': newname,
                        'action': 'create_version',
                        'ddl': ddl_v
                    })
                else:
                    results['actions'].append({
                        'table': entity_name,
                        'action': 'noop'
                    })
            else:
                # New table - create it
                self.pg.execute(ddl)
                results['actions'].append({
                    'table': entity_name,
                    'action': 'create',
                    'ddl': ddl
                })
        
        return results
    
    def _process_nosql_schema(self, normalized, results):
        """Process NoSQL schema generation and application"""
        for entity_name, schema in normalized.items():
            # Generate MongoDB validator
            validator = to_mongo_validator(schema)
            self.mongo.create_validator(entity_name, validator)
            
            results['nosql'][entity_name] = validator
            results['actions'].append({
                'collection': entity_name,
                'action': 'validator_applied',
                'validator': validator
            })
        
        return results