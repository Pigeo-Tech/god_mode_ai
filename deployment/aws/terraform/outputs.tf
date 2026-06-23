output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public API endpoint (HTTP)."
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.assets.domain_name
}

output "cluster_name" {
  value = aws_ecs_cluster.main.name
}
