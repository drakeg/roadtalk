terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.54"
    }
  }
}

provider "aws" {
  region = var.aws_region

  skip_credentials_validation = !var.enable_bootstrap
  skip_metadata_api_check     = !var.enable_bootstrap
  skip_requesting_account_id  = !var.enable_bootstrap

  default_tags {
    tags = {
      Application = "roadtalk"
      Environment = "bootstrap"
      ManagedBy   = "terraform"
    }
  }
}
