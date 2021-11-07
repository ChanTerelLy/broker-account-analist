output "aws_ecs_task_definition" {
  value = aws_ecs_task_definition.app.arn
}

data "aws_instances" "prod" {
  instance_tags        = {
    "Service" : "BAA",
    "Stage" : "Prod"
  }
  instance_state_names = ["running", "stopped"]
}
output ec2-ids {
    value = data.aws_instances.prod[*].public_ips
}