variable "bus_name" {
  description = "Name of the EventBridge custom event bus"
  type        = string
}

variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
  default     = "orders-created-rule"
}

variable "event_source" {
  description = "Source of the events to match"
  type        = string
}

variable "event_detail_type" {
  description = "Detail type of the events to match"
  type        = string
}

variable "consumer_lambda_arn" {
  description = "ARN of the Lambda function to invoke"
  type        = string
}

variable "consumer_lambda_function_name" {
  description = "Name of the Lambda function to invoke"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
