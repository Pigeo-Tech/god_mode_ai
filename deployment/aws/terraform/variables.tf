variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "god-mode-ai"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "container_image" {
  description = "Full ECR image URI (repo:tag). Defaults to the repo created here at :latest."
  type        = string
  default     = ""
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "task_cpu" {
  type    = number
  default = 1024
}

variable "task_memory" {
  type    = number
  default = 2048
}

variable "db_username" {
  type    = string
  default = "godmode"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "domain_name" {
  description = "Optional. If set, a Route53 alias record is created for the ALB."
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  type    = string
  default = ""
}
