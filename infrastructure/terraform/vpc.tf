# NBA MCP Synthesis - VPC Configuration
# Production-ready VPC with private subnets and NAT gateways

# VPC
resource "aws_vpc" "nba_mcp_synthesis" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.cluster_name}-vpc"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "nba_mcp_synthesis" {
  vpc_id = aws_vpc.nba_mcp_synthesis.id

  tags = {
    Name        = "${var.cluster_name}-igw"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.nba_mcp_synthesis.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                            = "${var.cluster_name}-public-${count.index + 1}"
    Environment                                     = "production"
    Project                                         = "nba-mcp-synthesis"
    ManagedBy                                       = "terraform"
    "kubernetes.io/role/elb"                        = "1"
    "kubernetes.io/cluster/${var.cluster_name}"    = "shared"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.nba_mcp_synthesis.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name                                            = "${var.cluster_name}-private-${count.index + 1}"
    Environment                                     = "production"
    Project                                         = "nba-mcp-synthesis"
    ManagedBy                                       = "terraform"
    "kubernetes.io/role/internal-elb"              = "1"
    "kubernetes.io/cluster/${var.cluster_name}"    = "shared"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = length(var.availability_zones)

  domain = "vpc"
  depends_on = [aws_internet_gateway.nba_mcp_synthesis]

  tags = {
    Name        = "${var.cluster_name}-nat-eip-${count.index + 1}"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# NAT Gateways
resource "aws_nat_gateway" "nba_mcp_synthesis" {
  count = length(var.availability_zones)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.cluster_name}-nat-${count.index + 1}"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }

  depends_on = [aws_internet_gateway.nba_mcp_synthesis]
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.nba_mcp_synthesis.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.nba_mcp_synthesis.id
  }

  tags = {
    Name        = "${var.cluster_name}-public-rt"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Route Table Associations for Public Subnets
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count = length(var.availability_zones)

  vpc_id = aws_vpc.nba_mcp_synthesis.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nba_mcp_synthesis[count.index].id
  }

  tags = {
    Name        = "${var.cluster_name}-private-rt-${count.index + 1}"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Route Table Associations for Private Subnets
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Group for EKS Cluster
resource "aws_security_group" "eks_cluster" {
  name_prefix = "${var.cluster_name}-cluster-"
  vpc_id      = aws_vpc.nba_mcp_synthesis.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-cluster-sg"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Security Group for EKS Nodes
resource "aws_security_group" "eks_nodes" {
  name_prefix = "${var.cluster_name}-node-"
  vpc_id      = aws_vpc.nba_mcp_synthesis.id

  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-node-sg"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Security Group for Application Load Balancer
resource "aws_security_group" "alb" {
  name_prefix = "${var.cluster_name}-alb-"
  vpc_id      = aws_vpc.nba_mcp_synthesis.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-alb-sg"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Security Group for RDS Database
resource "aws_security_group" "rds" {
  name_prefix = "${var.cluster_name}-rds-"
  vpc_id      = aws_vpc.nba_mcp_synthesis.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-rds-sg"
    Environment = "production"
    Project     = "nba-mcp-synthesis"
    ManagedBy   = "terraform"
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.nba_mcp_synthesis.id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = aws_vpc.nba_mcp_synthesis.cidr_block
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_security_group.eks_cluster.id
}

output "eks_nodes_security_group_id" {
  description = "EKS nodes security group ID"
  value       = aws_security_group.eks_nodes.id
}

output "alb_security_group_id" {
  description = "Application Load Balancer security group ID"
  value       = aws_security_group.alb.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}


