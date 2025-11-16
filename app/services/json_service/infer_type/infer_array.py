from collections import Counter

def infer_array(arr, infer_fn):
    """
    Infer the type of array elements
    Returns dict with array type information
    """
    if not isinstance(arr, list):
        return {'type': 'array', 'items': {'type': 'unknown'}, 'mixed': True}
    
    stats = Counter()
    item_types = []
    
    for item in arr:
        t, meta = infer_fn(item)
        stats[t] += 1
        item_types.append((t, meta))
    
    if not item_types:
        return {'type': 'array', 'items': {'type': 'null'}, 'mixed': False}
    
    most_common_type, _ = stats.most_common(1)[0]
    mixed = len(stats) > 1
    
    return {
        'type': 'array',
        'items': {'type': most_common_type},
        'mixed': mixed
    }