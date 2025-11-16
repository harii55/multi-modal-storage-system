def generate_alter_statements(table_name: str, add_columns: dict) -> list:
    """
    Generate ALTER TABLE statements for adding new columns
    """
    stmts = []
    for col, typ in add_columns.items():
        stmts.append(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {typ};')
    return stmts