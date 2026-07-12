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

  skip_credentials_validation = !var.enable_field_test
  skip_metadata_api_check     = !var.enable_field_test
  skip_requesting_account_id  = !var.enable_field_test

  default_tags {
    tags = local.tags
  }
}
