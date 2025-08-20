output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.vector_db.endpoint
}

output "opensearch_kibana_endpoint" {
  description = "OpenSearch Kibana endpoint"
  value       = aws_opensearch_domain.vector_db.kibana_endpoint
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for documents"
  value       = aws_s3_bucket.documents.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for documents"
  value       = aws_s3_bucket.documents.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.process_document.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.process_document.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "random_suffix" {
  description = "Random suffix used for resource naming"
  value       = random_id.bucket_suffix.hex
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}