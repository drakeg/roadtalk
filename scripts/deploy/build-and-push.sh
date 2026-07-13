#!/bin/sh
set -eu

repository_url="${1:?ECR repository URL is required}"
region="${AWS_REGION:-us-east-1}"
tag="${2:-$(git rev-parse HEAD)}"
registry="${repository_url%%/*}"
image="${repository_url}:${tag}"

aws ecr get-login-password --region "$region" |
  docker login --username AWS --password-stdin "$registry"
docker buildx build +  --platform linux/arm64 +  --file backend/Dockerfile +  --tag "$image" +  --push +  .

echo "$image"
