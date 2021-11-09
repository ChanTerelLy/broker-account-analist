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

resource "aws_s3_bucket" "terraform_state" {
  bucket = "terraform-${var.project_name}-sync"
  versioning {
    enabled = true
  }
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-up-and-running-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}