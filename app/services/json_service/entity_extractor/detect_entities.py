from typing import Dict, Any

def detect_entities_from_json(payload: Dict[str, Any]):
    """
    Detect entities from JSON payload
    Returns dict of entity_name -> sample_object
    """
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return {'root': payload[0]}
    
    if isinstance(payload, dict):
        num_obj_vals = sum(1 for v in payload.values() if isinstance(v, dict) or isinstance(v, list))
        
        if num_obj_vals >= len(payload) / 2 and num_obj_vals > 0:
            entities = {}
            entities['root'] = payload
            
            for k, v in payload.items():
                if isinstance(v, dict):
                    entities[k] = v
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    entities[k] = v[0]
            
            return entities
        
        return {'root': payload}
    
    return {'root': {}}