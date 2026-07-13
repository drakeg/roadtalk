locals {
  name = "roadtalk-field-test"
  tags = {
    Application = "roadtalk"
    Environment = "field-test"
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = "roadtalk-field-test"
  }
}

resource "terraform_data" "validation" {
  count = var.enable_field_test ? 1 : 0

  lifecycle {
    precondition {
      condition = (
        can(regex("^[0-9]{12}$", var.aws_account_id)) &&
        length(var.backup_bucket_name) >= 3 &&
        var.enable_monitoring
      )
      error_message = "Enabled field test requires account ID, backup bucket, and monitoring."
    }
  }
}

resource "terraform_data" "monitoring_validation" {
  count = var.enable_field_test && var.enable_monitoring ? 1 : 0

  lifecycle {
    precondition {
      condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+$", var.alert_email))
      error_message = "A valid operational alert_email is required for monitoring."
    }
  }
}

module "network" {
  count  = var.enable_field_test ? 1 : 0
  source = "../../modules/network"

  name                = local.name
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  tags                = local.tags
  depends_on          = [terraform_data.validation]
}

module "backup" {
  count  = var.enable_field_test ? 1 : 0
  source = "../../modules/backup"

  bucket_name    = var.backup_bucket_name
  retention_days = var.backup_retention_days
  tags           = local.tags
}

module "registry" {
  count  = var.enable_field_test ? 1 : 0
  source = "../../modules/registry"

  name            = "roadtalk/backend"
  retained_images = 3
  tags            = local.tags
}

module "compute" {
  count  = var.enable_field_test ? 1 : 0
  source = "../../modules/compute"

  name                     = local.name
  vpc_id                   = module.network[0].vpc_id
  subnet_id                = module.network[0].public_subnet_ids[0]
  instance_type            = var.instance_type
  root_volume_size_gb      = var.root_volume_size_gb
  backup_bucket_arn        = module.backup[0].bucket_arn
  repository_arn           = module.registry[0].repository_arn
  logs_resource_arn        = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/roadtalk/field-test/*"
  runtime_parameter_prefix = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/roadtalk/field-test/*"
  tags                     = local.tags
}

module "monitoring" {
  count  = var.enable_field_test && var.enable_monitoring ? 1 : 0
  source = "../../modules/monitoring"

  name               = local.name
  instance_id        = module.compute[0].instance_id
  alert_email        = var.alert_email
  monthly_budget_usd = var.monthly_budget_usd
  log_retention_days = 3
  tags               = local.tags

  depends_on = [terraform_data.monitoring_validation]
}
