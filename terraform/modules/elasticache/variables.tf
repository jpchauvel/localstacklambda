variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
