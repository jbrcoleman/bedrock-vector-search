variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "knowledge-base"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch cluster"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of instances in OpenSearch cluster"
  type        = number
  default     = 1
}

variable "opensearch_ebs_volume_size" {
  description = "EBS volume size for OpenSearch (GB)"
  type        = number
  default     = 20
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "Memory for ECS task (MB)"
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "AI Knowledge Base"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}