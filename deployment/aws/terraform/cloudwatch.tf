resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "qdrant" {
  name              = "/ecs/${var.project}-qdrant"
  retention_in_days = 14
}
