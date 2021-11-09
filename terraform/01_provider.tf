provider "aws" {
  region = var.region
  default_tags {
    tags = var.default_tags
  }
}

terraform {

  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "baa"

    workspaces {
      name = "broker-account-analist"
    }
  }
}