variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "pubsub"
}

variable "lambda_runtime" {
  description = "Lambda runtime environment (use python3.13 — AWS provider v5.x does not yet validate python3.14; LocalStack executes Python 3.14 code regardless of this label)"
  type        = string
  default     = "python3.13"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256
}

variable "redis_ttl_seconds" {
  description = "Redis key TTL in seconds"
  type        = number
  default     = 300
}

variable "event_bus_name" {
  description = "EventBridge event bus name"
  type        = string
  default     = "orders-bus"
}

variable "event_source" {
  description = "EventBridge event source"
  type        = string
  default     = "orders.api"
}

variable "event_detail_type" {
  description = "EventBridge event detail type"
  type        = string
  default     = "OrderCreated"
}
