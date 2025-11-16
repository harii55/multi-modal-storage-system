import os
from minio import Minio
from minio.error import S3Error
from io import BytesIO

class MinioClient:
    def __init__(self):
        minio_host = os.getenv("MINIO_HOST", "localhost")
        minio_port = os.getenv("MINIO_PORT", "9000")
        minio_user = os.getenv("MINIO_ROOT_USER", "minioadmin")
        minio_password = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        
        # Create MinIO client
        self.client = Minio(
            f"{minio_host}:{minio_port}",
            access_key=minio_user,
            secret_key=minio_password,
            secure=False  # Set to True if using HTTPS
        )
        
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "multimodal-storage")
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created successfully")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def ensure_bucket(self, bucket_name: str):
        """Ensure a specific bucket exists"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
    
    def put_object(self, bucket_name: str, object_name: str, data: bytes, content_type: str):
        """Upload bytes data to MinIO with specified content type"""
        self.ensure_bucket(bucket_name)
        bio = BytesIO(data)
        result = self.client.put_object(
            bucket_name, 
            object_name, 
            bio, 
            length=len(data), 
            content_type=content_type
        )
        return result
    
    def presigned_get(self, bucket_name: str, object_name: str, expiry=3600):
        """Generate presigned URL for object download"""
        return self.client.presigned_get_object(bucket_name, object_name, expires=expiry)
    
    def upload_file(self, file_path, object_name=None):
        """Upload a file to MinIO"""
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
            return object_name
        except S3Error as e:
            print(f"Error uploading file: {e}")
            raise
    
    def upload_data(self, data, object_name, length, content_type="application/octet-stream"):
        """Upload data (bytes or stream) to MinIO"""
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                data,
                length,
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            print(f"Error uploading data: {e}")
            raise
    
    def download_file(self, object_name, file_path):
        """Download a file from MinIO"""
        try:
            self.client.fget_object(
                self.bucket_name,
                object_name,
                file_path
            )
            return file_path
        except S3Error as e:
            print(f"Error downloading file: {e}")
            raise
    
    def get_object(self, object_name):
        """Get object data from MinIO"""
        try:
            response = self.client.get_object(
                self.bucket_name,
                object_name
            )
            return response.read()
        except S3Error as e:
            print(f"Error getting object: {e}")
            raise
        finally:
            response.close()
            response.release_conn()
    
    def delete_object(self, object_name):
        """Delete an object from MinIO"""
        try:
            self.client.remove_object(
                self.bucket_name,
                object_name
            )
            return True
        except S3Error as e:
            print(f"Error deleting object: {e}")
            raise
    
    def list_objects(self, prefix=None):
        """List objects in the bucket"""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            raise
    
    def get_presigned_url(self, object_name, expires=3600):
        """Get a presigned URL for an object"""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            raise
