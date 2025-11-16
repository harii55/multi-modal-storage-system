from typing import Dict, Any

def to_mongo_validator(entity_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate MongoDB JSON Schema validator
    """
    props = {}
    
    for k, v in entity_schema.get('properties', {}).items():
        t = v.get('type') if isinstance(v, dict) else v
        bson = 'string'
        
        if t == 'integer':
            bson = 'int'
        elif t == 'number':
            bson = 'double'
        elif t == 'boolean':
            bson = 'bool'
        elif t == 'object' or t == 'array':
            bson = 'object'
        
        props[k] = {'bsonType': bson}
    
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'properties': props
        }
    }
    
    return validator