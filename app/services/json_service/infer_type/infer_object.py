from app.services.json_service.infer_type.primitive import infer_primitive
from app.services.json_service.infer_type.infer_array import infer_array

def infer_object(obj, infer_fn):
    """
    Infer the schema of an object with all its properties
    Returns dict with object schema information
    """
    schema = {'type': 'object', 'properties': {}, 'required': []}
    
    if not isinstance(obj, dict):
        return {'type': 'object', 'properties': {}, 'required': []}
    
    for k, v in obj.items():
        if v is None:
            t, meta = ('null', {})
        elif isinstance(v, dict):
            t = 'object'
            meta = infer_fn(v)
        elif isinstance(v, list):
            meta = infer_array(v, infer_fn)
            t = 'array'
        else:
            t, m = infer_primitive(v)
            meta = m
        
        schema['properties'][k] = {'type': t, 'meta': meta}
        if v is not None:
            schema['required'].append(k)
    
    return schema