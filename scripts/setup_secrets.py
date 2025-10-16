"""
Setup AWS Secrets Manager for NBA MCP
Run once to create secrets in AWS Secrets Manager
"""
import boto3
import json
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import env helper
from mcp_server.env_helper import get_hierarchical_env

def create_secrets():
    """Create secrets in AWS Secrets Manager"""

    print("🔐 NBA MCP - AWS Secrets Manager Setup")
    print("=" * 80)
    print()

    # Load current .env
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print(f"❌ Error: .env file not found at {env_path}")
        print("   Please create .env file with your current credentials first")
        sys.exit(1)

    load_dotenv(env_path)

    # Verify required variables
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'S3_BUCKET']
    missing = [var for var in required_vars if not get_hierarchical_env(var, "NBA_MCP_SYNTHESIS", "WORKFLOW")]
    if missing:
        print(f"❌ Error: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)

    # Get region
    region = get_hierarchical_env('AWS_REGION', "NBA_MCP_SYNTHESIS", "WORKFLOW") or 'us-east-1'
    print(f"📍 AWS Region: {region}")
    print()

    # Create Secrets Manager client
    try:
        client = boto3.client('secretsmanager', region_name=region)
        print(f"✅ Connected to AWS Secrets Manager")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        print()
        print("Please ensure:")
        print("  1. AWS CLI is configured: aws configure")
        print("  2. You have secretsmanager:CreateSecret permission")
        sys.exit(1)

    print()

    # Define secrets
    secrets = {
        'nba-mcp/production/database': {
            'host': get_hierarchical_env('DB_HOST', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'user': get_hierarchical_env('DB_USER', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'password': get_hierarchical_env('DB_PASSWORD', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'database': get_hierarchical_env('DB_NAME', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'port': int(get_hierarchical_env('DB_PORT', "NBA_MCP_SYNTHESIS", "WORKFLOW") or 5432)
        },
        'nba-mcp/production/s3': {
            'bucket': get_hierarchical_env('S3_BUCKET', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'region': region
        }
    }

    # Optionally add AWS credentials (if using IAM user instead of role)
    if get_hierarchical_env('AWS_ACCESS_KEY_ID', "NBA_MCP_SYNTHESIS", "WORKFLOW") and get_hierarchical_env('AWS_SECRET_ACCESS_KEY', "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        secrets['nba-mcp/production/aws'] = {
            'access_key_id': get_hierarchical_env('AWS_ACCESS_KEY_ID', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'secret_access_key': get_hierarchical_env('AWS_SECRET_ACCESS_KEY', "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            'region': region
        }

    # Create each secret
    print("🔄 Creating secrets...")
    print()

    for secret_name, secret_value in secrets.items():
        try:
            response = client.create_secret(
                Name=secret_name,
                Description=f'NBA MCP credentials for {secret_name.split("/")[-1]}',
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Project', 'Value': 'NBA-MCP'},
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'ManagedBy', 'Value': 'Script'}
                ]
            )
            print(f"✅ Created: {secret_name}")
            print(f"   ARN: {response['ARN']}")
            print()
        except client.exceptions.ResourceExistsException:
            print(f"⚠️  Already exists: {secret_name}")
            # Update existing secret
            try:
                client.put_secret_value(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                print(f"✅ Updated: {secret_name}")
                print()
            except Exception as e:
                print(f"❌ Error updating: {e}")
                print()
        except Exception as e:
            print(f"❌ Error creating {secret_name}: {e}")
            raise

    print("=" * 80)
    print()
    print("🎉 Secrets setup complete!")
    print()
    print("📋 Next steps:")
    print()
    print("1. Backup your current .env file:")
    print("   cp .env .env.backup")
    print()
    print("2. Update .env file to remove sensitive data:")
    print("   # Remove DB_PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    print("   # Add: USE_LOCAL_CREDENTIALS=false")
    print()
    print("3. Add .env.backup to .gitignore")
    print()
    print("4. Test the setup:")
    print("   python -c 'from mcp_server.secrets_manager import get_database_config; print(get_database_config())'")
    print()
    print("5. Configure IAM permissions (if needed):")
    print("   aws iam put-role-policy --role-name your-role \\")
    print("       --policy-name SecretsManagerAccess \\")
    print("       --policy-document file://infrastructure/iam_secrets_policy.json")
    print()

if __name__ == '__main__':
    try:
        create_secrets()
    except KeyboardInterrupt:
        print("\n\n❌ Aborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)

