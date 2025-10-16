#!/bin/bash
# NBA MCP Synthesis - Build and Push Docker Image to ECR
# Builds the Docker image and pushes it to Amazon ECR

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="nba-mcp-synthesis"
IMAGE_TAG="${1:-latest}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}NBA MCP Synthesis - Docker Build and Push${NC}"
echo "=============================================="
echo "AWS Region: $AWS_REGION"
echo "ECR Repository: $ECR_REPOSITORY"
echo "Image Tag: $IMAGE_TAG"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS CLI not configured or credentials invalid${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}Checking ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating ECR repository: $ECR_REPOSITORY${NC}"
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    echo -e "${GREEN}ECR repository created successfully${NC}"
else
    echo -e "${GREEN}ECR repository already exists${NC}"
fi

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}ECR login successful${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
echo -e "${GREEN}Docker image built successfully${NC}"

# Tag image for ECR
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
echo -e "${YELLOW}Tagging image for ECR: $ECR_URI${NC}"
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI

# Push image to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push $ECR_URI
echo -e "${GREEN}Image pushed to ECR successfully${NC}"

# Display image information
echo ""
echo -e "${GREEN}Build and push completed successfully!${NC}"
echo "=============================================="
echo "Image URI: $ECR_URI"
echo "Repository: https://console.aws.amazon.com/ecr/repositories/private/$ACCOUNT_ID/$ECR_REPOSITORY"
echo ""

# Optional: Update Kubernetes deployment
if [ "$2" = "--update-k8s" ]; then
    echo -e "${YELLOW}Updating Kubernetes deployment...${NC}"
    kubectl set image deployment/nba-mcp-synthesis \
        nba-mcp-synthesis=$ECR_URI \
        -n nba-mcp-synthesis
    echo -e "${GREEN}Kubernetes deployment updated${NC}"
fi

echo -e "${GREEN}All done!${NC}"

