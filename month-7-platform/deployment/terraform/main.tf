terraform {
  required_version = ">= 1.8.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_db_subnet_group" "postgres" {
  name       = "fde-postgres"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "data" {
  name        = "fde-data"
  description = "Private data services for FDE platform"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL from application security group"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [var.application_security_group_id]
  }

  ingress {
    description = "Redis from application security group"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [var.application_security_group_id]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "fde-platform"
  engine                 = "postgres"
  engine_version         = var.postgres_version
  instance_class         = var.postgres_instance_class
  allocated_storage      = var.postgres_storage_gb
  db_name                = var.database_name
  username               = var.database_username
  manage_master_user_password = true
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.data.id]
  storage_encrypted      = true
  backup_retention_period = 7
  deletion_protection    = true
  skip_final_snapshot    = false
  publicly_accessible    = false
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "fde-redis"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "fde-platform"
  description                = "FDE platform distributed rate limiting and ephemeral state"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  engine                     = "redis"
  engine_version             = var.redis_version
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.data.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = true
}
