resource "aws_cloudwatch_event_bus" "this" {
  name = var.bus_name
  tags = var.tags
}

resource "aws_cloudwatch_event_rule" "orders_created" {
  name           = var.rule_name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  event_pattern = jsonencode({
    source        = [var.event_source]
    "detail-type" = [var.event_detail_type]
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "consumer" {
  rule           = aws_cloudwatch_event_rule.orders_created.name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  arn            = var.consumer_lambda_arn
  target_id      = "consumer-lambda"
}

resource "aws_lambda_permission" "eventbridge_invoke_consumer" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.consumer_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.orders_created.arn
}
