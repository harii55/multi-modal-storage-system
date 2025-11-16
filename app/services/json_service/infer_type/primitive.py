from datetime import datetime
import re
import uuid

ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

def is_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False

def is_iso_datetime(val: str) -> bool:
    try:
        if ISO_DATETIME_RE.match(val):
            datetime.fromisoformat(val)
            return True
    except Exception:
        return False
    return False

def infer_primitive(value):
    """
    Infer the primitive type of a value with semantic analysis
    Returns tuple: (type_name, metadata_dict)
    """
    if value is None:
        return ('null', {})
    if isinstance(value, bool):
        return ('boolean', {})
    if isinstance(value, int) and not isinstance(value, bool):
        return ('integer', {})
    if isinstance(value, float):
        return ('number', {})
    if isinstance(value, str):
        s = value.strip()
        if is_uuid(s):
            return ('uuid', {})
        if is_iso_datetime(s):
            return ('datetime', {})
        if '@' in s and '.' in s and ' ' not in s:
            return ('email', {})
        if s.startswith('http://') or s.startswith('https://'):
            return ('url', {})
        return ('string', {})
    return ('string', {})