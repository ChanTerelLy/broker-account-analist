module "store_write" {
  source = "git::https://github.com/cloudposse/terraform-aws-ssm-parameter-store?ref=master"

  parameter_write = concat(concat([
    for i, v in data.template_file.app.vars : {
      name      = "/projects/${var.project_name}/env/${upper(i)}",
      value     = v,
      type      = "String",
      overwrite = "true",
    }
    ]),
    [
      {
        name      = "AmazonCloudWatchEc2Config",
        value     = file("templates/cloud-watch-config.json"),
        type      = "String",
        overwrite = "true",
      }
  ])

  depends_on = [
    aws_elasticache_cluster.redis,
    aws_db_instance.production
  ]
}