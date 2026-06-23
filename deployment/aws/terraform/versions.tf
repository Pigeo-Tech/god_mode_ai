terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
  # Configure a remote backend (S3 + DynamoDB lock) in production:
  # backend "s3" { bucket = "god-mode-tfstate" key = "prod/terraform.tfstate" region = "us-east-1" dynamodb_table = "god-mode-tf-lock" }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
