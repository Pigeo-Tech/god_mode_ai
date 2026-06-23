# Private DNS namespace so the API can reach Qdrant at qdrant.god-mode.local:6333
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "god-mode.local"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "qdrant" {
  name = "qdrant"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {
      type = "A"
      ttl  = 10
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config { failure_threshold = 1 }
}

# Persistent storage for Qdrant via EFS.
resource "aws_efs_file_system" "qdrant" {
  creation_token = "${var.project}-qdrant"
  encrypted      = true
  tags           = { Name = "${var.project}-qdrant-efs" }
}

resource "aws_efs_mount_target" "qdrant" {
  count           = 2
  file_system_id  = aws_efs_file_system.qdrant.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.qdrant.id]
}

resource "aws_ecs_task_definition" "qdrant" {
  family                   = "${var.project}-qdrant"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.task_execution.arn

  volume {
    name = "qdrant-storage"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.qdrant.id
      transit_encryption = "ENABLED"
    }
  }

  container_definitions = jsonencode([{
    name      = "qdrant"
    image     = "qdrant/qdrant:latest"
    essential = true
    portMappings = [{ containerPort = 6333, protocol = "tcp" }]
    mountPoints  = [{ sourceVolume = "qdrant-storage", containerPath = "/qdrant/storage" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.qdrant.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "qdrant"
      }
    }
  }])
}

resource "aws_ecs_service" "qdrant" {
  name            = "${var.project}-qdrant"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.qdrant.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.qdrant.id]
  }
  service_registries {
    registry_arn = aws_service_discovery_service.qdrant.arn
  }
}
