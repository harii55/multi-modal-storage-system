def detect_relationships(entities: dict):
    """
    Detect relationships between entities
    Returns list of tuples: (parent_entity, child_entity, relationship_type)
    """
    rels = []
    
    for parent, sample in entities.items():
        if not isinstance(sample, dict):
            continue
        
        for k, v in sample.items():
            if isinstance(v, dict):
                rels.append((parent, k, 'one-to-one'))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                rels.append((parent, k, 'one-to-many'))
    
    return rels