def next_version_name(base_name: str, existing_tables: list) -> str:
    """
    Generate next version name for a table when schema is incompatible
    e.g., users -> users_v2 -> users_v3
    """
    if base_name not in existing_tables:
        return base_name
    
    i = 2
    while f"{base_name}_v{i}" in existing_tables:
        i += 1
    
    return f"{base_name}_v{i}"