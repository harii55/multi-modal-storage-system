import json
from typing import Dict, Any

class JsonProcessor:
    def process(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Process JSON file and determine if schema is SQL or NOSQL
        Returns processing result
        """
        try:
            data = json.loads(file_bytes.decode('utf-8'))

            # Determine schema type (SQL vs NOSQL)
            schema_type = self._detect_schema_type(data)

            if schema_type == 'sql':
                # TODO: Create services and write to DB
                # This will be implemented later
                return {
                    'schema_type': 'sql',
                    'status': 'pending',
                    'message': 'SQL schema detected - services creation pending'
                }
            else:
                # Handle NOSQL case
                return {
                    'schema_type': 'nosql',
                    'status': 'processed',
                    'data': data
                }

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def _detect_schema_type(self, data: Any) -> str:
        """
        Detect if JSON schema is SQL or NOSQL using custom algorithm
        Returns 'sql' or 'nosql'
        """
        decision = self._classify_json(data)
        return decision.lower()

    def _get_json_depth(self, obj):
        """Calculate the maximum depth of the JSON object"""
        if isinstance(obj, dict):
            if not obj:
                return 1
            return 1 + max(self._get_json_depth(v) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return 1
            return 1 + max(self._get_json_depth(item) for item in obj)
        else:
            return 0

    def _depth_score(self, json_obj, threshold=3, weight=0.4):
        """Score based on JSON depth - deeper structures suggest NoSQL"""
        depth = self._get_json_depth(json_obj)
        return weight if depth > threshold else 0

    def _array_level(self, json_obj):
        """Check if JSON contains arrays of objects (suggests tabular/SQL data)"""
        if isinstance(json_obj, dict):
            for v in json_obj.values():
                if self._array_level(v) == 1:
                    return 1
            return 0
        elif isinstance(json_obj, list):
            if any(isinstance(item, dict) for item in json_obj):
                return 1
            for item in json_obj:
                if self._array_level(item) == 1:
                    return 1
            return 0
        else:
            return 0

    def _array_score(self, json_obj, weight=0.35):
        """Score based on presence of arrays containing objects"""
        return weight if self._array_level(json_obj) == 1 else 0

    def _schema_consistency_score(self, json_obj, weight=0.25):
        """Score based on schema consistency in arrays of objects"""
        def check_inconsistency(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    if check_inconsistency(v):
                        return True
                return False
            elif isinstance(obj, list):
                obj_arrays = [i for i in obj if isinstance(i, dict)]
                if len(obj_arrays) > 1:
                    key_sets = [set(i.keys()) for i in obj_arrays]
                    first_keys = key_sets[0]
                    for k in key_sets[1:]:
                        if k != first_keys:
                            return True
                for item in obj:
                    if check_inconsistency(item):
                        return True
                return False
            else:
                return False

        inconsistent = check_inconsistency(json_obj)
        return weight if inconsistent else 0

    def _classify_json(self, json_obj, threshold=0.5):
        """Classify JSON as SQL or NoSQL based on combined scores"""
        d_score = self._depth_score(json_obj)
        a_score = self._array_score(json_obj)
        s_score = self._schema_consistency_score(json_obj)

        total_score = d_score + a_score + s_score
        decision = "NoSQL" if total_score >= threshold else "SQL"

        return decision