"""
S3 Connector
Handles S3 bucket operations for NBA data lake access
"""

import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import io
from pathlib import Path

logger = logging.getLogger(__name__)


class S3Connector:
    """S3 connector for NBA data lake"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """Initialize S3 client"""
        self.bucket_name = bucket_name
        self.region = region
        
        try:
            self.s3_client = boto3.client('s3', region_name=region)
            self.s3_resource = boto3.resource('s3', region_name=region)
            self.bucket = self.s3_resource.Bucket(bucket_name)
            logger.info(f"S3 connector initialized for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 connector: {e}")
            raise
    
    async def fetch_file_sample(
        self,
        file_path: str,
        sample_size: int = 100,
        sample_type: str = "lines"
    ) -> Dict[str, Any]:
        """Fetch sample content from S3 file"""
        
        try:
            # Get object
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            # Get metadata
            file_size = response['ContentLength']
            last_modified = response['LastModified']
            content_type = response.get('ContentType', 'unknown')
            
            # Read content based on sample type
            if sample_type == "full":
                content = response['Body'].read()
                sample_content = content.decode('utf-8')
            elif sample_type == "bytes":
                content = response['Body'].read(sample_size)
                sample_content = content.decode('utf-8', errors='ignore')
            else:  # lines
                content = response['Body'].read()
                lines = content.decode('utf-8').split('\n')
                sample_content = '\n'.join(lines[:sample_size])
            
            # Parse JSON if applicable
            parsed_content = None
            if file_path.endswith('.json'):
                try:
                    if sample_type == "full":
                        parsed_content = json.loads(sample_content)
                    else:
                        # Try to parse the sample (may fail for partial JSON)
                        parsed_content = {"sample": "Partial JSON - see raw content"}
                except:
                    parsed_content = None
            
            return {
                "success": True,
                "file_path": file_path,
                "bucket": self.bucket_name,
                "sample_content": sample_content,
                "parsed_content": parsed_content,
                "file_size": file_size,
                "file_type": Path(file_path).suffix,
                "last_modified": last_modified.isoformat(),
                "content_type": content_type
            }
            
        except self.s3_client.exceptions.NoSuchKey:
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        except Exception as e:
            logger.error(f"Failed to fetch S3 file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 100
    ) -> Dict[str, Any]:
        """List files in S3 bucket with prefix"""
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "storage_class": obj.get('StorageClass', 'STANDARD')
                    })
            
            return {
                "success": True,
                "bucket": self.bucket_name,
                "prefix": prefix,
                "file_count": len(files),
                "files": files,
                "truncated": response.get('IsTruncated', False)
            }
            
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for a specific S3 file"""
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "size": response['ContentLength'],
                "content_type": response.get('ContentType', 'unknown'),
                "last_modified": response['LastModified'].isoformat(),
                "etag": response.get('ETag', ''),
                "metadata": response.get('Metadata', {})
            }
            
        except self.s3_client.exceptions.NoSuchKey:
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        except Exception as e:
            logger.error(f"Failed to get S3 metadata: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_to_s3(
        self,
        file_path: str,
        content: str,
        content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """Save content to S3"""
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "bucket": self.bucket_name,
                "size": len(content.encode('utf-8')),
                "s3_uri": f"s3://{self.bucket_name}/{file_path}"
            }
            
        except Exception as e:
            logger.error(f"Failed to save to S3: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_connection(self) -> bool:
        """Test S3 connection"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except:
            return False

    def get_object(self, key: str) -> str:
        """
        Get object content from S3 (synchronous for fastmcp_server compatibility).

        Args:
            key: S3 object key

        Returns:
            String content of the object
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            content = response['Body'].read()
            return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to get S3 object {key}: {e}")
            raise

    def list_objects(self, prefix: str = "", max_keys: int = 100) -> List[str]:
        """
        List objects in S3 bucket (synchronous for fastmcp_server compatibility).

        Args:
            prefix: Filter objects by prefix
            max_keys: Maximum number of keys to return

        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            logger.error(f"Failed to list S3 objects with prefix {prefix}: {e}")
            raise
