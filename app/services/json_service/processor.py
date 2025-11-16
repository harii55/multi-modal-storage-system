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
        Detect if JSON schema is SQL or NOSQL
        TODO: Implement the custom algorithm here
        For now, return 'nosql' as default
        """
        # Placeholder logic - will be replaced with custom algorithm
        # For now, assume NOSQL unless it looks like tabular data

        if isinstance(data, list) and len(data) > 0:
            # Check if all items have similar structure (tabular-like)
            first_item = data[0]
            if isinstance(first_item, dict):
                # Count common keys across items
                all_keys = set()
                for item in data[:min(10, len(data))]:  # Check first 10 items
                    if isinstance(item, dict):
                        all_keys.update(item.keys())

                # If most items share keys, might be SQL-like
                common_keys = set()
                for item in data[:min(10, len(data))]:
                    if isinstance(item, dict):
                        if not common_keys:
                            common_keys = set(item.keys())
                        else:
                            common_keys = common_keys.intersection(set(item.keys()))

                # If more than 50% of keys are common, treat as SQL
                if len(common_keys) > len(all_keys) * 0.5:
                    return 'sql'

        return 'nosql'