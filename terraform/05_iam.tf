### ECS ###

resource "aws_iam_role" "ecs-service-role" {
  name               = "ecs_service_role_prod"
  assume_role_policy = file("policies/ecs-role.json")
}

resource "aws_iam_role_policy" "ecs-service-role-policy" {
  name   = "ecs_service_role_policy"
  policy = file("policies/ecs-service-role-policy.json")
  role   = aws_iam_role.ecs-service-role.id
}


### EC2 ###

resource "aws_iam_instance_profile" "ec2-ecs-instance" {
  name = "ec2_ecs_instance_profile_prod"
  path = "/"
  role = aws_iam_role.ecs-host-role.name
}

# Role
resource "aws_iam_role" "ecs-host-role" {
  name               = "ecs_host_role_prod"
  assume_role_policy = file("policies/ecs-role.json")
}

# Policies
resource "aws_iam_role_policy" "ecs-instance-role-policy" {
  name   = "ecs_instance_role_policy"
  policy = file("policies/ec2-ecs-instance-role-policy.json")
  role   = aws_iam_role.ecs-host-role.id
}

resource "aws_iam_role_policy_attachment" "cloud-watch-policy" {
  role       = aws_iam_role.ecs-host-role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}