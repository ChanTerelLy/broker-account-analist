resource "aws_db_subnet_group" "production" {
  name       = "main"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_db_instance" "production" {
  identifier                          = "production"
  name                                = var.rds_db_name
  username                            = var.rds_username
  password                            = var.rds_password
  port                                = "5432"
  engine                              = "postgres"
  engine_version                      = 12.7
  instance_class                      = var.rds_instance_class
  allocated_storage                   = "20"
  storage_encrypted                   = false
  vpc_security_group_ids              = [aws_security_group.rds.id]
  db_subnet_group_name                = aws_db_subnet_group.production.name
  multi_az                            = false
  storage_type                        = "gp2"
  publicly_accessible                 = false
  backup_retention_period             = 0
  skip_final_snapshot                 = true
  iam_database_authentication_enabled = true

  lifecycle {
    prevent_destroy = false
  }
}
