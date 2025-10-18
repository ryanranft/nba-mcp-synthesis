# NBA MCP Synthesis - Secrets Manager Configuration
# AWS Secrets Manager setup for production secrets

# Secrets Manager for production secrets
resource "aws_secretsmanager_secret" "nba_mcp_synthesis_secrets" {
  for_each = var.production_secrets

  name                    = each.key
  description             = each.value.description
  recovery_window_in_days = 7

  tags = {
    Name        = each.key
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Secret versions
resource "aws_secretsmanager_secret_version" "nba_mcp_synthesis_secrets" {
  for_each = aws_secretsmanager_secret.nba_mcp_synthesis_secrets

  secret_id     = each.value.id
  secret_string = each.value.secret_value
}

# IAM policy for application access to secrets
resource "aws_iam_policy" "secrets_manager_access" {
  name        = "${var.cluster_name}-secrets-manager-access"
  description = "Policy for NBA MCP Synthesis to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:nba-mcp-synthesis/*"
        ]
      }
    ]
  })
}

# Attach policy to EKS node group role
resource "aws_iam_role_policy_attachment" "secrets_manager_access" {
  policy_arn = aws_iam_policy.secrets_manager_access.arn
  role       = aws_iam_role.eks_node_group.name
}

# KMS key for secrets encryption
resource "aws_kms_key" "secrets_manager" {
  description             = "KMS key for NBA MCP Synthesis secrets encryption"
  deletion_window_in_days = 7

  tags = {
    Name        = "${var.cluster_name}-secrets-kms"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

resource "aws_kms_alias" "secrets_manager" {
  name          = "alias/${var.cluster_name}-secrets"
  target_key_id = aws_kms_key.secrets_manager.key_id
}

# Outputs
output "secrets_manager_kms_key_id" {
  description = "KMS key ID for secrets encryption"
  value       = aws_kms_key.secrets_manager.key_id
}

output "secrets_manager_kms_alias" {
  description = "KMS alias for secrets encryption"
  value       = aws_kms_alias.secrets_manager.name
}

output "secrets_manager_policy_arn" {
  description = "IAM policy ARN for secrets access"
  value       = aws_iam_policy.secrets_manager_access.arn
}


