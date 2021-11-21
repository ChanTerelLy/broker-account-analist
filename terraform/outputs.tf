output "aws_ecs_service" {
  value = aws_ecs_service.production.name
}
output "aws_ecs_task_definition" {
  value = aws_ecs_task_definition.app.arn
}
data "aws_instances" "prod" {
  instance_tags = {
    "Service" : "BAA",
    "Stage" : "Prod"
  }
  instance_state_names = ["running"]
  depends_on = [aws_autoscaling_group.ecs-cluster]
}
output "ec2-ids" {
  value = join(", ", data.aws_instances.prod.public_ips)
}
output "rds-host" {
  value = aws_db_instance.production.address
}
output "redis-host" {
  value = join(", ", aws_elasticache_cluster.redis.cache_nodes[*].address)
}
output "efs" {
  value = module.efs.id
}