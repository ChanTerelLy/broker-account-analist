module "efs" {
  source  = "cloudposse/efs/aws"
  version = "0.32.0"

  name                      = "baa-storage"
  efs_backup_policy_enabled = false
  region                    = var.region
  vpc_id                    = module.vpc.vpc_id
  subnets                   = module.vpc.private_subnets
  transition_to_ia          = ["AFTER_90_DAYS"]

  access_points = {
    "" = {
      posix_user = null
    }
  }

  allowed_security_group_ids = [aws_security_group.ecs.id]
}
