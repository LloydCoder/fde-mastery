variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "application_security_group_id" {
  type = string
}

variable "database_name" {
  type    = string
  default = "fde_platform"
}

variable "database_username" {
  type    = string
  default = "fde_admin"
}

variable "postgres_version" {
  type    = string
  default = "16.4"
}

variable "postgres_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "postgres_storage_gb" {
  type    = number
  default = 50
}

variable "redis_version" {
  type    = string
  default = "7.1"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}
