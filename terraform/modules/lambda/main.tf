resource "null_resource" "build_zips" {
  triggers = {
    src_hash = sha256(join("", [
      for f in fileset("${var.source_root}/src", "**/*.py") :
      filesha256("${var.source_root}/src/${f}")
    ]))
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/build_zips.sh ${var.source_root}"
  }
}

resource "aws_lambda_function" "producer" {
  depends_on       = [null_resource.build_zips]
  function_name    = "${var.project_name}-producer"
  role             = var.producer_role_arn
  handler          = "producer.handler.handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory
  filename         = "${path.module}/build/producer.zip"
  source_code_hash = fileexists("${path.module}/build/producer.zip") ? filebase64sha256("${path.module}/build/producer.zip") : null
  tags             = var.tags

  environment {
    variables = {
      EVENT_BUS_NAME    = var.event_bus_name
      EVENT_SOURCE      = var.event_source
      EVENT_DETAIL_TYPE = var.event_detail_type
      AWS_ENDPOINT_URL  = "http://localhost.localstack.cloud:4566"
    }
  }
}

resource "aws_lambda_function" "consumer" {
  depends_on       = [null_resource.build_zips]
  function_name    = "${var.project_name}-consumer"
  role             = var.consumer_role_arn
  handler          = "consumer.handler.handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory
  filename         = "${path.module}/build/consumer.zip"
  source_code_hash = fileexists("${path.module}/build/consumer.zip") ? filebase64sha256("${path.module}/build/consumer.zip") : null
  tags             = var.tags

  environment {
    variables = {
      REDIS_HOST        = var.redis_host
      REDIS_PORT        = tostring(var.redis_port)
      REDIS_TTL_SECONDS = tostring(var.redis_ttl_seconds)
      AWS_ENDPOINT_URL  = "http://localhost.localstack.cloud:4566"
    }
  }
}

resource "aws_cloudwatch_log_group" "producer" {
  name              = "/aws/lambda/${var.project_name}-producer"
  retention_in_days = 1
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "consumer" {
  name              = "/aws/lambda/${var.project_name}-consumer"
  retention_in_days = 1
  tags              = var.tags
}
