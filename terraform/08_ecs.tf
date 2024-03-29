resource "aws_ecs_cluster" "production" {
  name = "${var.ecs_cluster_name}-cluster"

#  setting {
#    name  = "containerInsights"
#    value = "enabled"
#  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_launch_configuration" "ec2-ecs-instance" {
  vpc_classic_link_security_groups = []
  image_id                         = lookup(var.amis, var.region)
  instance_type                    = var.instance_type
  security_groups                  = [aws_security_group.ecs.id]
  iam_instance_profile             = aws_iam_instance_profile.ec2-ecs-instance.name
  key_name                         = aws_key_pair.production.key_name
  associate_public_ip_address      = true
  user_data                        = data.template_file.bootstrap.rendered

  lifecycle {
    create_before_destroy = true
  }
}

data "template_file" "bootstrap" {
  template = file("templates/bootstrap.sh")

  vars = {
    ecs_cluster_name = var.ecs_cluster_name
  }
}

data "template_file" "app" {
  template = file("templates/django_app.json.tpl")

  vars = {
    docker_image_url_django           = var.docker_image_url_django
    region                            = var.region
    app_name                          = var.project_name
    db_name                           = var.rds_db_name
    db_username                       = var.rds_username
    db_password                       = var.rds_password
    db_hostname                       = aws_db_instance.production.address
    db_port                           = "5432"
    redis_url                         = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
    secret_key                        = var.secret_key
    debug                             = var.debug
    db_engine                         = var.db_engine
    email_host                        = var.email_host
    email_port                        = var.email_port
    sentry_dsn                        = var.sentry_dsn
    internal_api_token                = var.internal_api_token
    site_url                          = var.site_url
    email_host_user                   = var.email_host_user
    email_host_password               = var.email_host_password
    admin_email                       = var.admin_email
    google_service_redirect_uri       = var.google_service_redirect_uri
    social_auth_google_oauth_2_key    = var.social_auth_google_oauth_2_key
    social_auth_google_oauth_2_secret = tostring(var.social_auth_google_oauth_2_secret)
    google_config                     = jsonencode(var.google_config)
    django_settings_module            = var.django_settings_module
    efs_id                            = module.efs.id
  }
}

resource "aws_ecs_task_definition" "app" {
  family                = "django-app"
  container_definitions = data.template_file.app.rendered
  depends_on            = [aws_db_instance.production, aws_elasticache_cluster.redis]

  volume {
    name = "efs"
    efs_volume_configuration {
      file_system_id = module.efs.id
    }
  }

}

resource "aws_ecs_service" "production" {
  name                               = "${var.ecs_cluster_name}-service"
  cluster                            = aws_ecs_cluster.production.id
  task_definition                    = aws_ecs_task_definition.app.arn
  iam_role                           = module.ecs_service_role.iam_role_arn
  desired_count                      = var.app_count
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 30

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  depends_on = [
    aws_alb_listener.ecs-alb-http-listener, module.ecs_service_role
  ]

  load_balancer {
    target_group_arn = aws_alb_target_group.default-target-group.arn
    container_name   = "django-app"
    container_port   = 80
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [task_definition]
  }
}
