from typing import Dict, Any

def compare_table_schema(existing: Dict[str, Any], generated: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare existing table schema with generated schema
    Returns dict with compatibility info and differences
    """
    res = {'compatible': True, 'add_columns': {}, 'change_columns': {}}
    
    for col, gtype in generated.items():
        if col not in existing:
            res['add_columns'][col] = gtype
        else:
            etype = existing[col]
            # Basic mapping: do not attempt deep match here
            if etype != gtype:
                res['compatible'] = False
                res['change_columns'][col] = (etype, gtype)
    
    return res