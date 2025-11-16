from typing import Dict, Any

class MediaProcessor:
    def process(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Process non-JSON files (media, documents, etc.)
        For now, just return basic info - can be expanded later
        """
        file_size = len(file_bytes)

        return {
            'filename': filename,
            'file_size': file_size,
            'status': 'processed',
            'message': 'Media file processed successfully'
        }