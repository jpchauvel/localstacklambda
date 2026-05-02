output "producer_function_name" {
  description = "Producer Lambda function name"
  value       = aws_lambda_function.producer.function_name
}

output "producer_function_arn" {
  description = "Producer Lambda function ARN"
  value       = aws_lambda_function.producer.arn
}

output "producer_invoke_arn" {
  description = "Producer Lambda invoke ARN"
  value       = aws_lambda_function.producer.invoke_arn
}

output "consumer_function_name" {
  description = "Consumer Lambda function name"
  value       = aws_lambda_function.consumer.function_name
}

output "consumer_function_arn" {
  description = "Consumer Lambda function ARN"
  value       = aws_lambda_function.consumer.arn
}
