module "elasticache" {
  source       = "./modules/elasticache"
  project_name = var.project_name
  tags         = local.common_tags
}

module "iam" {
  source        = "./modules/iam"
  project_name  = var.project_name
  event_bus_arn = "arn:aws:events:${var.aws_region}:000000000000:event-bus/${var.event_bus_name}"
  tags          = local.common_tags
}

module "lambda" {
  source            = "./modules/lambda"
  project_name      = var.project_name
  runtime           = var.lambda_runtime
  timeout           = var.lambda_timeout
  memory            = var.lambda_memory
  producer_role_arn = module.iam.producer_role_arn
  consumer_role_arn = module.iam.consumer_role_arn
  event_bus_name    = var.event_bus_name
  event_source      = var.event_source
  event_detail_type = var.event_detail_type
  redis_host        = module.elasticache.redis_endpoint
  redis_port        = module.elasticache.redis_port
  redis_ttl_seconds = var.redis_ttl_seconds
  source_root       = "${path.module}/.."
  tags              = local.common_tags
}

module "eventbridge" {
  source                        = "./modules/eventbridge"
  bus_name                      = var.event_bus_name
  event_source                  = var.event_source
  event_detail_type             = var.event_detail_type
  consumer_lambda_arn           = module.lambda.consumer_function_arn
  consumer_lambda_function_name = module.lambda.consumer_function_name
  tags                          = local.common_tags
}

module "api_gateway" {
  source                 = "./modules/api-gateway"
  project_name           = var.project_name
  producer_function_name = module.lambda.producer_function_name
  producer_function_arn  = module.lambda.producer_function_arn
  producer_invoke_arn    = module.lambda.producer_invoke_arn
  tags                   = local.common_tags
}
