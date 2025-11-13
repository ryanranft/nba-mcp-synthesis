# AWS Knowledge MCP Implementation Guide
## NBA MCP Synthesis Project

[← Previous: Memory MCP](MEMORY_MCP_IMPLEMENTATION.md) | [📊 Progress Tracker](README.md) | [Master Guide](../MCP_IMPLEMENTATION_GUIDE.md) | [Next: Brave Search MCP →](BRAVE_SEARCH_MCP_IMPLEMENTATION.md)

---

**Purpose:** Real-time AWS documentation access for accurate boto3/AWS code generation. Reduces hallucinations when working with AWS services.

**Priority:** Medium-High (valuable for AWS development)
**Estimated Time:** 5 minutes
**Credentials Required:** No
**Cost:** Free (remote AWS-managed service)

**IMPORTANT:** This MCP complements (not replaces) your existing boto3/psycopg2 connectors. It provides documentation context to help Claude generate better AWS code.

---

## Implementation Checklist

### Prerequisites
- [ ] Internet connection for remote service access
- [ ] No credentials required (remote managed service)
- [ ] No API keys needed
- [ ] Python uvx tool available

---

### Step 1: Test AWS Knowledge MCP Installation

- [ ] Check if uvx is installed:
  ```bash
  which uvx || pip install uvx
  ```

- [ ] Run test command:
  ```bash
  uvx awslabs.aws-knowledge-mcp-server@latest --help
  ```

- [ ] Verify installation successful (will download on first run)

- [ ] Note: First run may take 1-2 minutes to download dependencies

---

### Step 2: Update MCP Configuration - Desktop App

- [ ] Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

- [ ] Add AWS Knowledge MCP configuration to `mcpServers` section:
  ```json
  "aws-knowledge": {
    "command": "uvx",
    "args": ["-y", "awslabs.aws-knowledge-mcp-server@latest"],
    "env": {
      "AWS_REGION": "us-east-1"
    }
  }
  ```

- [ ] Save file

---

### Step 3: Update MCP Configuration - CLI

#### Update .claude/mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.claude/mcp.json`

- [ ] Add AWS Knowledge MCP configuration to `mcpServers` section:
  ```json
  "aws-knowledge": {
    "command": "uvx",
    "args": ["-y", "awslabs.aws-knowledge-mcp-server@latest"],
    "env": {
      "AWS_REGION": "us-east-1"
    }
  }
  ```

- [ ] Save file

#### Update .mcp.json

- [ ] Open: `/Users/ryanranft/nba-mcp-synthesis/.mcp.json`

- [ ] Add same AWS Knowledge MCP configuration

- [ ] Save file

---

### Step 4: Test AWS Knowledge MCP Connection

#### Restart Claude

- [ ] Quit Claude desktop app completely (Cmd+Q)
- [ ] Restart Claude desktop app
- [ ] In CLI, run: `/mcp`
- [ ] Verify "aws-knowledge" appears in connected MCPs list

---

### Step 5: Test AWS Documentation Queries

#### boto3 S3 API Queries

- [ ] **S3 PutObject with metadata:**
  - Ask Claude: "What's the latest boto3 API for S3 PutObject with custom metadata?"
  - Verify it returns accurate boto3 code example

- [ ] **S3 lifecycle policies:**
  - Ask Claude: "Show me AWS best practices for S3 lifecycle policies for archiving data older than 90 days"
  - Verify it returns current best practices

#### RDS PostgreSQL Queries

- [ ] **Connection pooling:**
  - Ask Claude: "How do I configure RDS PostgreSQL connection pooling best practices in boto3?"
  - Verify it returns relevant RDS documentation

- [ ] **Backup strategies:**
  - Ask Claude: "What are AWS recommended backup strategies for RDS PostgreSQL production databases?"
  - Verify it returns current AWS recommendations

#### Lambda Queries

- [ ] **IAM permissions:**
  - Ask Claude: "What are the IAM permissions needed for Lambda execution role to access S3 and write to CloudWatch Logs?"
  - Verify it returns accurate IAM policy

- [ ] **Event schemas:**
  - Ask Claude: "Show me the AWS Lambda event schema for S3 PutObject triggers"
  - Verify it returns correct event structure

---

### Step 6: Test Integration with Your Infrastructure

#### S3 Operations (Your Existing Connector)

- [ ] **Query S3 best practices:**
  ```
  "I'm using boto3 s3_client.put_object() to upload NBA game data. What are AWS best practices for:
  - Optimal chunk size for multipart uploads
  - Metadata tagging for data lake objects
  - Storage class selection for archival data"
  ```

- [ ] Verify recommendations align with your use case

- [ ] Compare with your current implementation in `mcp_server/connectors/s3_connector.py`

#### RDS PostgreSQL (Your Existing Connector)

- [ ] **Query RDS optimization:**
  ```
  "I have a PostgreSQL RDS database for NBA stats with heavy read queries. What are AWS best practices for:
  - Read replica configuration
  - Connection pooling settings
  - Query performance optimization"
  ```

- [ ] Verify recommendations are actionable

- [ ] Review your current setup in `mcp_server/connectors/odds_database_connector.py`

#### Glue Operations (Your Existing Connector)

- [ ] **Query Glue best practices:**
  ```
  "I'm using AWS Glue to catalog NBA data in S3. What are best practices for:
  - Partition strategies for time-series data
  - Crawler configuration for Parquet files
  - Performance optimization"
  ```

- [ ] Verify recommendations match your data structure

---

### Step 7: Use Cases for Your NBA Project

#### Generating boto3 Code

**Before AWS Knowledge MCP:**
```python
# May have incorrect parameter names or outdated syntax
s3_client.put_object(
    Bucket='bucket',
    Key='key',
    Body=data,
    Metadata={'custom': 'value'}  # Is this correct?
)
```

**With AWS Knowledge MCP:**
- Ask Claude: "Generate boto3 code to upload JSON data to S3 with custom metadata"
- Get accurate, up-to-date code with correct parameter names
- Includes error handling and best practices

#### Troubleshooting RDS Connections

**Before:**
- Search Google for "psycopg2 RDS connection timeout"
- Find outdated Stack Overflow answers

**With AWS Knowledge MCP:**
- Ask: "What causes connection timeouts to RDS PostgreSQL and how to fix?"
- Get official AWS troubleshooting steps
- Get current best practices for connection management

#### Understanding Lambda Event Schemas

**Before:**
- Manually construct event payload for testing
- May have incorrect structure

**With AWS Knowledge MCP:**
- Ask: "Show me the Lambda event schema for S3 PUT events"
- Get exact event structure from AWS docs
- Use for testing Lambda functions

#### Validating IAM Policies

**Before:**
```json
{
  "Effect": "Allow",
  "Action": "s3:*",  // Too permissive?
  "Resource": "*"
}
```

**With AWS Knowledge MCP:**
- Ask: "Generate least-privilege IAM policy for Lambda to read from S3 bucket nba-sim-raw-data-lake"
- Get precise, minimal permissions
- Follow AWS security best practices

---

### Step 8: Common AWS Documentation Queries

#### S3 Queries

```
"What are the S3 storage classes and when to use each?"
"How do I configure S3 lifecycle policies in boto3?"
"What's the best way to handle S3 multipart uploads in Python?"
"Show me S3 object tagging best practices for data lakes"
```

#### RDS Queries

```
"What are RDS PostgreSQL parameter group best practices for analytics workloads?"
"How do I configure RDS read replicas in boto3?"
"What's the recommended backup retention strategy for production RDS?"
"Show me RDS connection pooling configuration for Python applications"
```

#### CloudWatch Queries

```
"How do I create custom CloudWatch metrics in boto3?"
"What are CloudWatch Logs retention best practices?"
"Show me how to set up CloudWatch alarms for RDS performance"
```

#### Lambda Queries

```
"What's the Lambda environment variable size limit?"
"How do I configure Lambda VPC access to RDS?"
"Show me Lambda concurrency limits and best practices"
"What are Lambda event source mapping configurations for S3?"
```

---

## Benefits

### ✅ Always Up-to-Date

- AWS Knowledge MCP is remotely managed by AWS
- Always has latest API documentation
- Includes recent service updates
- No need to update manually

### ✅ Reduces AI Hallucinations

- Claude can reference official AWS docs
- Generates accurate boto3 code
- Uses correct parameter names
- Follows current best practices

### ✅ Complements Your Infrastructure

- Doesn't replace your existing connectors
- Provides documentation context only
- Your direct SDK approach remains superior
- Helps generate better AWS code

### ✅ Zero Maintenance

- No credentials to manage
- No API keys to rotate
- No rate limits to worry about
- AWS maintains the service

### ✅ Free

- No cost for using service
- No API usage charges
- No data transfer costs

---

## Important Notes

### What AWS Knowledge MCP Does

✅ **Provides documentation** - Access to AWS docs
✅ **Generates code examples** - boto3 code snippets
✅ **Explains services** - Service overviews
✅ **Shows best practices** - AWS recommendations
✅ **Validates syntax** - Correct API usage

### What AWS Knowledge MCP Does NOT Do

❌ **Execute AWS operations** - Can't run boto3 commands
❌ **Access your AWS account** - Read-only documentation
❌ **Replace your connectors** - Complements, doesn't replace
❌ **Manage resources** - Can't create/modify AWS resources
❌ **Monitor your infrastructure** - No access to your AWS account

### Keep Your Existing Approach

**DO NOT replace these with AWS MCP:**
- ✅ Keep `S3Connector` (boto3 direct access)
- ✅ Keep `OddsDatabaseConnector` (psycopg2 direct access)
- ✅ Keep `GlueConnector` (boto3 direct access)
- ✅ Keep hierarchical secrets system

**USE AWS Knowledge MCP for:**
- Generating new boto3 code
- Troubleshooting AWS issues
- Learning best practices
- Validating implementations

---

## Troubleshooting

### Connection Issues

**Symptom:** AWS Knowledge MCP not connecting

**Solution:**
1. Verify internet connection (remote service)
2. Check uvx is installed:
   ```bash
   which uvx || pip install uvx
   ```
3. Test manual connection:
   ```bash
   uvx awslabs.aws-knowledge-mcp-server@latest --help
   ```
4. Restart Claude app completely

### Slow Response Times

**Symptom:** Queries take long to return

**Solution:**
- Remote service may have latency
- First query may be slower (caching)
- Subsequent queries usually faster
- Check internet connection speed

### Outdated Information

**Symptom:** Documentation seems outdated

**Solution:**
- AWS Knowledge MCP is usually current
- Double-check with aws.amazon.com for critical decisions
- File feedback with AWS if consistently outdated

---

## Verification Checklist

- [ ] uvx installed
- [ ] AWS Knowledge MCP tested successfully
- [ ] Desktop app config updated
- [ ] CLI configs updated (.claude/mcp.json and .mcp.json)
- [ ] AWS Knowledge MCP connects successfully
- [ ] Can query boto3 S3 APIs
- [ ] Can query RDS best practices
- [ ] Can query Lambda information
- [ ] Can query IAM policies
- [ ] Tested with your existing infrastructure
- [ ] Understand what it does vs doesn't do
- [ ] Keeping existing connectors (not replacing)

---

## Next Steps After Implementation

1. **Generate new boto3 code** - Use for new AWS features
2. **Review existing code** - Validate against best practices
3. **Document AWS patterns** - Build internal knowledge base
4. **Train team** - Show how to query AWS docs via Claude
5. **Integrate with development** - Use during coding sessions

---

## Integration with Development Workflow

### During Code Development

**When writing new AWS code:**
1. Ask AWS Knowledge MCP for code example
2. Get accurate boto3 syntax
3. Follow AWS best practices
4. Implement in your codebase

**When troubleshooting:**
1. Query AWS Knowledge MCP for error explanation
2. Get official troubleshooting steps
3. Apply to your infrastructure
4. Document solution

### During Code Review

**Review checklist:**
1. Does code follow AWS best practices? (ask MCP)
2. Are IAM permissions minimal? (ask MCP)
3. Are error handlers correct? (ask MCP)
4. Is configuration optimal? (ask MCP)

---

*Implementation Status:* [ ] Not Started | [ ] In Progress | [ ] Completed
*Last Updated:* 2025-11-12
*Document Version:* 1.0
