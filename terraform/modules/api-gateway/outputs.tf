output "api_id" {
  description = "API Gateway HTTP API ID"
  value       = aws_apigatewayv2_api.this.id
}

output "api_endpoint" {
  description = "API Gateway base endpoint"
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "invoke_url" {
  description = "Full URL for POST /orders"
  value       = "${aws_apigatewayv2_api.this.api_endpoint}/orders"
}
