# Production VPC


module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "production-vpc"
  cidr = "10.0.0.0/16"

  azs             = var.availability_zones
  private_subnets = [var.private_subnet_1_cidr, var.private_subnet_2_cidr]
  public_subnets  = [var.public_subnet_1_cidr, var.public_subnet_2_cidr]

  enable_nat_gateway      = false
  enable_vpn_gateway      = false
  enable_dns_hostnames    = true
  map_public_ip_on_launch = false

}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "tf-test-cache-subnet"
  subnet_ids = module.vpc.private_subnets
}