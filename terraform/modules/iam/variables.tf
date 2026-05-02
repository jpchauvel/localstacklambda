variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "event_bus_arn" {
  description = "ARN of the EventBridge event bus"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
