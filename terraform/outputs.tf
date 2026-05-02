output "api_endpoint" {
  description = "API Gateway base endpoint"
  value       = module.api_gateway.api_endpoint
}

output "invoke_url" {
  description = "Full URL for POST /orders"
  value       = module.api_gateway.invoke_url
}

output "event_bus_name" {
  description = "EventBridge custom bus name"
  value       = module.eventbridge.bus_name
}

output "event_bus_arn" {
  description = "EventBridge custom bus ARN"
  value       = module.eventbridge.bus_arn
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.elasticache.redis_endpoint
}

output "redis_port" {
  description = "Redis cluster port"
  value       = module.elasticache.redis_port
}

output "producer_function_name" {
  description = "Producer Lambda function name"
  value       = module.lambda.producer_function_name
}

output "consumer_function_name" {
  description = "Consumer Lambda function name"
  value       = module.lambda.consumer_function_name
}
