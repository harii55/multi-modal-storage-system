from typing import Dict, Any
from app.services.json_service.infer_type.infer_object import infer_object

def normalize_entities(entities: Dict[str, Any], infer_fn) -> Dict[str, Any]:
    """
    Normalize entities into structured schemas
    Returns dict of entity_name -> schema
    """
    normalized = {}
    
    for name, sample in entities.items():
        if isinstance(sample, dict):
            obj_schema = infer_object(sample, infer_fn)
            normalized[name] = obj_schema
        else:
            normalized[name] = {'type': 'object', 'properties': {}, 'required': []}
    
    return normalized