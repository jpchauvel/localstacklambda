variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "producer_function_name" {
  description = "Producer Lambda function name"
  type        = string
}

variable "producer_function_arn" {
  description = "Producer Lambda function ARN"
  type        = string
}

variable "producer_invoke_arn" {
  description = "Producer Lambda invoke ARN"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
