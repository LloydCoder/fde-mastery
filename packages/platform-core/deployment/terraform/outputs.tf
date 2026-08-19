output "postgres_endpoint" {
  value     = aws_db_instance.postgres.address
  sensitive = false
}

output "postgres_secret_arn" {
  value     = aws_db_instance.postgres.master_user_secret[0].secret_arn
  sensitive = false
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}
