# ALB Security Group (Traffic Internet -> ALB)
locals {
  cidr_all = ["0.0.0.0/0"]
}

module "web_server_sg" {
  source = "terraform-aws-modules/security-group/aws//modules/https-443"

  name        = "load_balancer_security_group"
  description = "Controls access to the ALB"
  vpc_id      = module.vpc.vpc_id

  ingress_cidr_blocks = local.cidr_all
}


module "efs_sg" {
  source = "terraform-aws-modules/security-group/aws//modules/nfs"

  name        = "efs_security_group"
  description = "Controls access to the ALB"
  vpc_id      = module.vpc.vpc_id

  ingress_cidr_blocks = local.cidr_all
}

# ECS Security group (traffic ALB -> ECS, ssh -> ECS)
resource "aws_security_group" "ecs" {
  name        = "ecs_security_group"
  description = "Allows inbound access from the ALB only"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [module.web_server_sg.security_group_id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = local.cidr_all
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS Security Group (traffic ECS -> RDS)
resource "aws_security_group" "rds" {
  name        = "rds-security-group"
  description = "Allows inbound access from ECS only"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = "5432"
    to_port         = "5432"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = local.cidr_all
  }
}

# Redis security group
resource "aws_security_group" "redis" {
  name        = "redis-security-group"
  description = "Access for all vpc"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol    = "tcp"
    from_port   = "6379"
    to_port     = "6379"
    cidr_blocks = local.cidr_all
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = local.cidr_all
  }
}
