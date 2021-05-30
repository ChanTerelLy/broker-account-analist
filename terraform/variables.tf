# core
variable "region" {
  description = "The AWS region to create resources in."
  default     = "us-west-1"
}

variable "project_name" {
  default = "baa"
}
# networking

variable "public_subnet_1_cidr" {
  description = "CIDR Block for Public Subnet 1"
  default     = "10.0.1.0/24"
}
variable "public_subnet_2_cidr" {
  description = "CIDR Block for Public Subnet 2"
  default     = "10.0.2.0/24"
}
variable "private_subnet_1_cidr" {
  description = "CIDR Block for Private Subnet 1"
  default     = "10.0.3.0/24"
}
variable "private_subnet_2_cidr" {
  description = "CIDR Block for Private Subnet 2"
  default     = "10.0.4.0/24"
}
variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-west-1a", "us-west-1c"]
}


# load balancer

variable "health_check_path" {
  description = "Health check path for the default target group"
  default     = "/ping/"
}


# ecs

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  default     = "production"
}
variable "amis" {
  description = "Which AMI to spawn."
  default = {
    us-west-1 = "ami-0667a9cc6a93f50fe"
  }
}
variable "instance_type" {
  default = "t2.micro"
}
variable "cache_instance_type" {
  default = "cache.t2.micro"
}
variable "docker_image_url_django" {
  description = "Docker image to run in the ECS cluster"
  default     = "chanterelly/baa-service"
}
variable "docker_image_url_nginx" {
  description = "Docker image to run in the ECS cluster"
  default     = "nginx:latest"
}
variable "app_count" {
  description = "Number of Docker containers to run"
  default     = 2
}

variable "certificate_arn" {}

# logs

variable "log_retention_in_days" {
  default = 30
}


# key pair

variable "ssh_pubkey_file" {
  description = "Path to an SSH public key"
  default     = "~/.ssh/id_rsa.pub"
}


# auto scaling

variable "autoscale_min" {
  description = "Minimum autoscale (number of EC2)"
  default     = "1"
}
variable "autoscale_max" {
  description = "Maximum autoscale (number of EC2)"
  default     = "1"
}
variable "autoscale_desired" {
  description = "Desired autoscale (number of EC2)"
  default     = "1"
}


# rds

variable "rds_db_name" {
  description = "RDS database name"
  default     = "mydb"
}
variable "rds_username" {
  description = "RDS database username"
  default     = "postgres"
}
variable "rds_password" {
  description = "RDS database password"
  default     = "postgres"
}
variable "rds_instance_class" {
  description = "RDS instance type"
  default     = "db.t2.micro"
}

# application variables
variable "secret_key" {
  type = string
}

variable "debug" {
  type = number
}

variable "db_engine" {
  type = string
}

variable "email_host" {
  type = string
}

variable "email_port" {
  type = number
}

variable "email_host_user" {
  type = string
}

variable "email_host_password" {
  type = string
}

variable "admin_email" {
  type = string
}
variable "google_service_redirect_uri" {
  type = string
}
variable "social_auth_google_oauth_2_key" {
  type = string
}
variable "social_auth_google_oauth_2_secret" {
  type = string
}
variable "google_config" {
  type = "map"
}
