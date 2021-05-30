module "store_write" {
  source = "git::https://github.com/cloudposse/terraform-aws-ssm-parameter-store?ref=master"

  parameter_write = concat([
  for i, v in data.template_file.app.vars : {
    name = "/projects/${var.project_name}/env/${upper(i)}",
    value = v,
    type = "String",
    overwrite = "true",
  }
  ])

  tags = {
    ManagedBy = "Terraform"
  }
  depends_on = [
    aws_elasticache_cluster.redis,
    aws_db_instance.production]
  }