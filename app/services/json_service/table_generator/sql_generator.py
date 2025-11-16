from typing import Dict, Any

TYPE_MAP = {
    'integer': 'BIGINT',
    'number': 'DOUBLE PRECISION',
    'boolean': 'BOOLEAN',
    'string': 'TEXT',
    'datetime': 'TIMESTAMPTZ',
    'date': 'DATE',
    'uuid': 'UUID',
    'email': 'TEXT',
    'url': 'TEXT',
    'null': 'TEXT',
}

def map_type(t: str) -> str:
    """Map inferred type to PostgreSQL type"""
    return TYPE_MAP.get(t, 'JSONB')

def generate_create_table(entity_name: str, schema: Dict[str, Any], relationships: list = None) -> str:
    """
    Generate CREATE TABLE DDL for PostgreSQL
    """
    cols = []
    cols.append('id UUID PRIMARY KEY DEFAULT gen_random_uuid()')
    
    props = schema.get('properties', {})
    required = set(schema.get('required', []))
    
    for k, v in props.items():
        t = v.get('type') if isinstance(v, dict) else v
        
        if t == 'object':
            sqltype = 'JSONB'
        elif t == 'array':
            sqltype = 'JSONB'
        else:
            sqltype = map_type(t)
        
        nullable = 'NOT NULL' if k in required else ''
        cols.append(f'"{k}" {sqltype} {nullable}')
    
    if relationships:
        for parent, child, rtype in relationships:
            if parent == entity_name and rtype == 'one-to-one':
                cols.append(f'"{child}_id" UUID')
    
    cols_sql = ',\n    '.join(cols)
    ddl = f'CREATE TABLE IF NOT EXISTS "{entity_name}" (\n    {cols_sql}\n);'
    
    return ddl