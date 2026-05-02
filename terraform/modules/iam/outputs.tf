output "producer_role_arn" {
  description = "ARN of the Producer Lambda IAM role"
  value       = aws_iam_role.producer_lambda.arn
}

output "producer_role_name" {
  description = "Name of the Producer Lambda IAM role"
  value       = aws_iam_role.producer_lambda.name
}

output "consumer_role_arn" {
  description = "ARN of the Consumer Lambda IAM role"
  value       = aws_iam_role.consumer_lambda.arn
}

output "consumer_role_name" {
  description = "Name of the Consumer Lambda IAM role"
  value       = aws_iam_role.consumer_lambda.name
}
