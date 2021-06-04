output "alb_hostname" {
  value = aws_lb.production.dns_name
}
output "aws_ecs_task_definition" {
  value = aws_ecs_task_definition.app.arn
}
