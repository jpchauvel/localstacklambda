resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  node_type            = var.node_type
  num_cache_nodes      = 1
  port                 = var.port
  parameter_group_name = "default.redis7"
  tags                 = var.tags
}
