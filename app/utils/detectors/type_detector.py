import json
import mimetypes
from typing import Union

class TypeDetector:
    def detect(self, filename: str, file_bytes: bytes) -> str:
        """
        Detect if the file is JSON or non-JSON (media/other)
        Returns: 'json' or 'media'
        """
        # First check file extension
        mime_type, _ = mimetypes.guess_type(filename)

        # If mime type suggests JSON or if filename ends with .json
        if mime_type == 'application/json' or filename.lower().endswith('.json'):
            # Verify it's actually valid JSON
            try:
                json.loads(file_bytes.decode('utf-8'))
                return 'json'
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # For now, treat everything else as media
        # Later this can be expanded to detect other types
        return 'media'