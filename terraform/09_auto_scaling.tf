resource "aws_autoscaling_group" "ecs-cluster" {
  name                 = "${var.ecs_cluster_name}_auto_scaling_group"
  min_size             = var.autoscale_min
  max_size             = var.autoscale_max
  desired_capacity     = var.autoscale_desired
  health_check_type    = "EC2"
  launch_configuration = aws_launch_configuration.ec2-ecs-instance.name
  vpc_zone_identifier  = [aws_subnet.public-subnet-2.id]

  instance_refresh {
    strategy = "Rolling"
  }

  tags = [
  for k, v in var.default_tags : {
    key                 = k,
    value               = v,
    propagate_at_launch = true
  }
  ]
}
