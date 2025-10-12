# 🔐 CRITICAL 1: AWS Secrets Manager Implementation

**Priority:** 🔴 CRITICAL - IMMEDIATE
**Time:** 2 days
**Impact:** 🔥🔥🔥 HIGH - Eliminates credential exposure risk
**Status:** 🔄 In Progress

---

## 🎯 GOAL

Move all sensitive credentials from plain text `.env` file to AWS Secrets Manager for secure credential management.

---

## 📋 SUCCESS CRITERIA

✅ All database credentials stored in AWS Secrets Manager
✅ All AWS credentials stored in Secrets Manager
✅ `.env` file contains no sensitive data
✅ Code uses boto3 to fetch secrets at runtime
✅ Secrets rotation enabled
✅ IAM permissions configured correctly
✅ Local development still works
✅ Documentation updated

---

## 📚 BOOK REFERENCE

**"Designing Machine Learning Systems" - Chapter 11: The Human Side of Machine Learning**
- Security & Privacy section
- Secrets Management best practices
- Pages 380-385

---

## 🏗️ ARCHITECTURE

### **Current State:**
```
.env (plain text):
├── DB_HOST=nba-stats.xxx.rds.amazonaws.com
├── DB_USER=postgres
├── DB_PASSWORD=mysecretpassword123  ← EXPOSED!
├── DB_NAME=nba_stats
├── AWS_ACCESS_KEY_ID=AKIAXXXXXXX  ← EXPOSED!
└── AWS_SECRET_ACCESS_KEY=xxxxx  ← EXPOSED!
```

### **Target State:**
```
AWS Secrets Manager:
└── nba-mcp/production
    ├── db_host
    ├── db_user
    ├── db_password  ← SECURE!
    ├── db_name
    └── aws_credentials  ← SECURE!

.env (public):
├── NBA_MCP_ENV=production
├── AWS_REGION=us-east-1
└── SECRETS_NAME=nba-mcp/production
```

---

## 🛠️ IMPLEMENTATION

### **Step 1: Install Dependencies**

```bash
# Already have boto3, ensure it's latest
pip install --upgrade boto3
```

### **Step 2: Create Secrets in AWS**

**File:** `scripts/setup_secrets.py`

```python
"""
Setup AWS Secrets Manager for NBA MCP
Run once to create secrets
"""
import boto3
import json
import os
from dotenv import load_dotenv

def create_secrets():
    """Create secrets in AWS Secrets Manager"""

    # Load current .env
    load_dotenv()

    # Create Secrets Manager client
    client = boto3.client('secretsmanager', region_name='us-east-1')

    # Define secrets
    secrets = {
        'nba-mcp/production/database': {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 5432))
        },
        'nba-mcp/production/aws': {
            'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'region': os.getenv('AWS_REGION', 'us-east-1')
        },
        'nba-mcp/production/s3': {
            'bucket': os.getenv('S3_BUCKET')
        }
    }

    # Create each secret
    for secret_name, secret_value in secrets.items():
        try:
            response = client.create_secret(
                Name=secret_name,
                Description=f'NBA MCP credentials for {secret_name.split("/")[-1]}',
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Project', 'Value': 'NBA-MCP'},
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'ManagedBy', 'Value': 'Terraform'}
                ]
            )
            print(f"✅ Created secret: {secret_name}")
            print(f"   ARN: {response['ARN']}")
        except client.exceptions.ResourceExistsException:
            print(f"⚠️  Secret already exists: {secret_name}")
            # Update existing secret
            client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            print(f"✅ Updated secret: {secret_name}")
        except Exception as e:
            print(f"❌ Error creating {secret_name}: {e}")
            raise

    print()
    print("🎉 All secrets created successfully!")
    print()
    print("Next steps:")
    print("1. Update .env file (remove sensitive data)")
    print("2. Enable automatic rotation")
    print("3. Update IAM policies")

if __name__ == '__main__':
    create_secrets()
```

### **Step 3: Create Secrets Helper Module**

**File:** `mcp_server/secrets_manager.py`

```python
"""
AWS Secrets Manager integration for NBA MCP
Provides secure credential retrieval
"""
import boto3
import json
import os
from functools import lru_cache
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """Manages secure credential retrieval from AWS Secrets Manager"""

    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize Secrets Manager client

        Args:
            region_name: AWS region for Secrets Manager
        """
        self.region_name = region_name
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize boto3 Secrets Manager client"""
        try:
            self.client = boto3.client('secretsmanager', region_name=self.region_name)
            logger.info(f"✅ Secrets Manager client initialized (region: {self.region_name})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Secrets Manager client: {e}")
            raise

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager

        Args:
            secret_name: Name of the secret in Secrets Manager

        Returns:
            Dictionary containing secret values

        Raises:
            Exception if secret cannot be retrieved
        """
        try:
            logger.debug(f"Fetching secret: {secret_name}")

            response = self.client.get_secret_value(SecretId=secret_name)

            # Parse secret string
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
                logger.debug(f"✅ Secret retrieved: {secret_name}")
                return secret
            else:
                # Binary secrets (not used for this project)
                raise ValueError(f"Secret {secret_name} is binary, expected JSON")

        except self.client.exceptions.ResourceNotFoundException:
            logger.error(f"❌ Secret not found: {secret_name}")
            raise ValueError(f"Secret '{secret_name}' not found in Secrets Manager")
        except Exception as e:
            logger.error(f"❌ Error retrieving secret {secret_name}: {e}")
            raise

    def get_database_credentials(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get database credentials

        Args:
            environment: Environment name (production, staging, dev)

        Returns:
            Database connection parameters
        """
        secret_name = f'nba-mcp/{environment}/database'
        return self.get_secret(secret_name)

    def get_aws_credentials(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get AWS credentials

        Args:
            environment: Environment name

        Returns:
            AWS credentials
        """
        secret_name = f'nba-mcp/{environment}/aws'
        return self.get_secret(secret_name)

    def get_s3_config(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get S3 configuration

        Args:
            environment: Environment name

        Returns:
            S3 configuration
        """
        secret_name = f'nba-mcp/{environment}/s3'
        return self.get_secret(secret_name)

    def rotate_secret(self, secret_name: str) -> bool:
        """
        Trigger secret rotation

        Args:
            secret_name: Name of secret to rotate

        Returns:
            True if rotation triggered successfully
        """
        try:
            self.client.rotate_secret(SecretId=secret_name)
            logger.info(f"✅ Secret rotation triggered: {secret_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to rotate secret {secret_name}: {e}")
            return False

    def clear_cache(self):
        """Clear the secret cache (useful for testing or after rotation)"""
        self.get_secret.cache_clear()
        logger.info("🔄 Secret cache cleared")


# Global instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    """Get or create global SecretsManager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        region = os.getenv('AWS_REGION', 'us-east-1')
        _secrets_manager = SecretsManager(region_name=region)
    return _secrets_manager


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from Secrets Manager

    Returns:
        Database connection parameters
    """
    env = os.getenv('NBA_MCP_ENV', 'production')
    sm = get_secrets_manager()
    return sm.get_database_credentials(environment=env)


def get_s3_bucket() -> str:
    """
    Get S3 bucket name from Secrets Manager

    Returns:
        S3 bucket name
    """
    env = os.getenv('NBA_MCP_ENV', 'production')
    sm = get_secrets_manager()
    config = sm.get_s3_config(environment=env)
    return config['bucket']
```

### **Step 4: Update Database Connection**

**File:** `mcp_server/database.py` (update)

```python
"""
Database connection management with Secrets Manager
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from .secrets_manager import get_database_config
import logging

logger = logging.getLogger(__name__)

def get_database_engine() -> Engine:
    """
    Create database engine using credentials from Secrets Manager

    Returns:
        SQLAlchemy Engine
    """
    try:
        # Get credentials from Secrets Manager
        db_config = get_database_config()

        # Build connection string
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        # Create engine
        engine = create_engine(
            connection_string,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )

        logger.info("✅ Database engine created")
        return engine

    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        raise
```

### **Step 5: Update .env File**

**File:** `.env` (updated - safe to commit)

```bash
# NBA MCP Configuration
# =====================

# Environment
NBA_MCP_ENV=production
AWS_REGION=us-east-1

# Secrets Manager
# All sensitive credentials stored in AWS Secrets Manager:
# - nba-mcp/production/database (DB credentials)
# - nba-mcp/production/aws (AWS credentials)
# - nba-mcp/production/s3 (S3 bucket)

# Logging
NBA_MCP_DEBUG=false
NBA_MCP_LOG_LEVEL=INFO

# Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000

# Features
ENABLE_CACHING=true
CACHE_TTL=3600
```

### **Step 6: Update .gitignore**

**File:** `.gitignore` (add)

```gitignore
# Never commit these files
.env.local
.env.*.local
secrets_backup.json

# Old .env with credentials (archived)
.env.old
```

### **Step 7: Create IAM Policy**

**File:** `infrastructure/iam_secrets_policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSecretsManagerRead",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:nba-mcp/*"
      ]
    },
    {
      "Sid": "AllowSecretsManagerList",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
```

### **Step 8: Enable Secret Rotation**

**File:** `scripts/enable_rotation.sh`

```bash
#!/bin/bash
# Enable automatic secret rotation for NBA MCP secrets

set -e

REGION="us-east-1"
ROTATION_DAYS=90

echo "🔄 Enabling secret rotation for NBA MCP secrets..."
echo ""

# Enable rotation for database credentials
echo "Enabling rotation for database credentials..."
aws secretsmanager rotate-secret \
    --secret-id nba-mcp/production/database \
    --rotation-rules AutomaticallyAfterDays=${ROTATION_DAYS} \
    --region ${REGION}

echo "✅ Database credentials rotation enabled (every ${ROTATION_DAYS} days)"
echo ""

echo "⚠️  Note: You'll need to set up a Lambda function for automatic rotation"
echo "   See: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html"
echo ""
echo "For now, rotate manually using:"
echo "  aws secretsmanager rotate-secret --secret-id nba-mcp/production/database"
```

---

## 🧪 TESTING

### **Test 1: Secret Creation**

```bash
# Create secrets
python scripts/setup_secrets.py

# Verify secrets exist
aws secretsmanager list-secrets --region us-east-1 | grep nba-mcp
```

### **Test 2: Secret Retrieval**

```python
# tests/test_secrets_manager.py
import pytest
from mcp_server.secrets_manager import SecretsManager, get_database_config

def test_secrets_manager_initialization():
    """Test SecretsManager initializes correctly"""
    sm = SecretsManager()
    assert sm.client is not None
    assert sm.region_name == 'us-east-1'

def test_get_database_credentials():
    """Test retrieving database credentials"""
    config = get_database_config()
    assert 'host' in config
    assert 'user' in config
    assert 'password' in config
    assert 'database' in config
    assert 'port' in config

def test_secret_caching():
    """Test that secrets are cached"""
    sm = SecretsManager()

    # First call
    secret1 = sm.get_secret('nba-mcp/production/database')

    # Second call (should be cached)
    secret2 = sm.get_secret('nba-mcp/production/database')

    # Should be same object
    assert secret1 is secret2

    # Clear cache
    sm.clear_cache()

    # Third call (fresh)
    secret3 = sm.get_secret('nba-mcp/production/database')

    # Should be different object
    assert secret1 is not secret3
```

### **Test 3: Database Connection**

```python
# tests/test_database_with_secrets.py
from mcp_server.database import get_database_engine

def test_database_connection_with_secrets():
    """Test database connection using Secrets Manager"""
    engine = get_database_engine()

    # Test connection
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.scalar() == 1

    print("✅ Database connection successful with Secrets Manager")
```

---

## ✅ VALIDATION

### **Checklist:**

- [ ] Secrets created in AWS Secrets Manager
- [ ] IAM policy attached to EC2/ECS role
- [ ] `.env` file updated (no sensitive data)
- [ ] Old `.env` backed up and added to `.gitignore`
- [ ] Database connection works with Secrets Manager
- [ ] S3 access works with Secrets Manager
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Rotation configured (manual or automatic)

### **Validation Commands:**

```bash
# 1. Check secrets exist
aws secretsmanager list-secrets | grep nba-mcp

# 2. Test secret retrieval
python -c "from mcp_server.secrets_manager import get_database_config; print(get_database_config())"

# 3. Run tests
pytest tests/test_secrets_manager.py -v

# 4. Test database connection
python -c "from mcp_server.database import get_database_engine; get_database_engine().connect()"

# 5. Verify no secrets in .env
grep -i password .env || echo "✅ No passwords in .env"
```

---

## 🐛 TROUBLESHOOTING

### **Issue: "Access Denied" when retrieving secrets**

**Solution:**
```bash
# Check IAM permissions
aws iam get-role-policy --role-name nba-mcp-role --policy-name SecretsManagerAccess

# If missing, attach policy
aws iam put-role-policy \
    --role-name nba-mcp-role \
    --policy-name SecretsManagerAccess \
    --policy-document file://infrastructure/iam_secrets_policy.json
```

### **Issue: "Secret not found"**

**Solution:**
```bash
# List all secrets
aws secretsmanager list-secrets

# Create missing secret
python scripts/setup_secrets.py
```

### **Issue: Local development not working**

**Solution:**
Create `.env.local` for local development:
```bash
# .env.local (not committed)
NBA_MCP_ENV=local
USE_LOCAL_CREDENTIALS=true
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=local_dev_password
```

Update code to check `USE_LOCAL_CREDENTIALS`:
```python
if os.getenv('USE_LOCAL_CREDENTIALS') == 'true':
    # Use local .env
else:
    # Use Secrets Manager
```

---

## 📚 DOCUMENTATION

### **Update README.md:**

```markdown
## 🔐 Secrets Management

NBA MCP uses AWS Secrets Manager for secure credential storage.

### Setup

1. Create secrets:
   ```bash
   python scripts/setup_secrets.py
   ```

2. Configure IAM permissions:
   ```bash
   aws iam put-role-policy --role-name your-role \
       --policy-name SecretsManagerAccess \
       --policy-document file://infrastructure/iam_secrets_policy.json
   ```

3. Update `.env` (remove sensitive data)

### Local Development

For local development, create `.env.local`:
```bash
NBA_MCP_ENV=local
USE_LOCAL_CREDENTIALS=true
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your_local_password
```

### Rotating Secrets

Manual rotation:
```bash
aws secretsmanager rotate-secret --secret-id nba-mcp/production/database
```

Automatic rotation: See `scripts/enable_rotation.sh`
```

---

## 🎯 SUCCESS CRITERIA (Final Check)

✅ All database credentials in AWS Secrets Manager
✅ All AWS credentials in Secrets Manager
✅ `.env` file safe to commit (no secrets)
✅ Code retrieves secrets at runtime
✅ IAM permissions configured
✅ Tests passing
✅ Documentation updated
✅ Old .env backed up securely

---

## 🚀 DEPLOYMENT

1. Create secrets in AWS:
   ```bash
   python scripts/setup_secrets.py
   ```

2. Update IAM role:
   ```bash
   aws iam put-role-policy --role-name nba-mcp-role \
       --policy-name SecretsManagerAccess \
       --policy-document file://infrastructure/iam_secrets_policy.json
   ```

3. Update application code (already done in steps above)

4. Deploy updated code:
   ```bash
   git add .
   git commit -m "feat: implement AWS Secrets Manager for credential security"
   git push
   ```

5. Restart services to use new secrets

6. Verify:
   ```bash
   # Check logs for successful secret retrieval
   tail -f /var/log/nba-mcp/application.log | grep "Secrets Manager"
   ```

---

**IMPLEMENTATION TIME:** 2 days
**IMPACT:** Eliminates critical security vulnerability
**STATUS:** ✅ Ready to implement

