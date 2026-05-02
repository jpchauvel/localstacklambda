# Producer Lambda IAM Role
resource "aws_iam_role" "producer_lambda" {
  name = "${var.project_name}-producer-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Producer Lambda inline policy - PutEvents to EventBridge + CloudWatch Logs
resource "aws_iam_role_policy" "producer_policy" {
  name = "${var.project_name}-producer-policy"
  role = aws_iam_role.producer_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PutEventsToEventBridge"
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = [
          var.event_bus_arn
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:*"
        ]
      }
    ]
  })
}

# Consumer Lambda IAM Role
resource "aws_iam_role" "consumer_lambda" {
  name = "${var.project_name}-consumer-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Consumer Lambda inline policy - CloudWatch Logs only
resource "aws_iam_role_policy" "consumer_policy" {
  name = "${var.project_name}-consumer-policy"
  role = aws_iam_role.consumer_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:*"
        ]
      }
    ]
  })
}
