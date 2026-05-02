variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
}

variable "memory" {
  description = "Lambda memory size in MB"
  type        = number
}

variable "producer_role_arn" {
  description = "IAM role ARN for producer Lambda"
  type        = string
}

variable "consumer_role_arn" {
  description = "IAM role ARN for consumer Lambda"
  type        = string
}

variable "event_bus_name" {
  description = "EventBridge bus name used by producer"
  type        = string
}

variable "event_source" {
  description = "Event source emitted by producer"
  type        = string
}

variable "event_detail_type" {
  description = "Event detail-type emitted by producer"
  type        = string
}

variable "redis_host" {
  description = "Redis host for consumer"
  type        = string
}

variable "redis_port" {
  description = "Redis port for consumer"
  type        = number
}

variable "redis_ttl_seconds" {
  description = "Redis TTL for deduplication keys"
  type        = number
}

variable "source_root" {
  description = "Path to repository root for Lambda source archiving"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
