output "bus_arn" {
  description = "ARN of the EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.this.arn
}

output "bus_name" {
  description = "Name of the EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.this.name
}

output "rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.orders_created.arn
}

output "rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.orders_created.name
}
