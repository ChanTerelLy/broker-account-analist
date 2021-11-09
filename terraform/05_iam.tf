### ECS ###

locals {
  trusted_role_services = [
    "ec2.amazonaws.com",
    "ecs.amazonaws.com"
  ]
}

module "ecs_service_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "~> 4.3"

  create_role = true

  trusted_role_services = local.trusted_role_services

  role_name = "ecs_service_role"

  role_requires_mfa = false


  custom_role_policy_arns = [
    module.ecs_service_policy.arn
  ]

  depends_on = [module.ecs_service_policy]
}

module "ecs_service_policy" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "~> 4.3"

  name        = "ecs-service-role-policy"
  path        = "/"
  description = ""

  policy = file("policies/ecs-service-role-policy.json")
}


### EC2 ###

resource "aws_iam_instance_profile" "ec2-ecs-instance" {
  name = "ecs_instance_profile"
  path = "/"
  role = module.ecs_instance_role.iam_role_name
}


module "ecs_instance_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "~> 4.3"

  create_role = true

  trusted_role_services = local.trusted_role_services

  role_requires_mfa = false


  role_name = "ecs_host_role"

  custom_role_policy_arns = [
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    module.ecs_instance_role_policy.arn
  ]

  depends_on = [module.ecs_instance_role_policy]
}

module "ecs_instance_role_policy" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "~> 4.3"

  name        = "ecs_instance_role_policy"
  path        = "/"
  description = ""

  policy = file("policies/ecs-instance-role-policy.json")
}