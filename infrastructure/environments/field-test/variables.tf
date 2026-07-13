variable "enable_field_test" {
  description = "Explicit opt-in. The default plan creates no resources."
  type        = bool
  default     = false
}

variable "aws_region" {
  description = "Single approved AWS region."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID used only to scope the runtime SSM IAM policy."
  type        = string
  default     = ""

}

variable "availability_zones" {
  description = "Two AZs reserved for staged growth."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "vpc_cidr" {
  description = "Field-test VPC CIDR."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs. No private subnet or NAT Gateway is created."
  type        = list(string)
  default     = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "instance_type" {
  description = "Low-cost ARM field-test size; increase after load evidence."
  type        = string
  default     = "t4g.small"
}

variable "root_volume_size_gb" {
  description = "Encrypted gp3 volume for host, API, and local data services."
  type        = number
  default     = 40
}

variable "backup_bucket_name" {
  description = "Globally unique encrypted off-instance backup bucket name."
  type        = string
  default     = ""

}

variable "backup_retention_days" {
  description = "Short field-test backup retention."
  type        = number
  default     = 30
}

variable "owner" {
  description = "Operational owner tag."
  type        = string
  default     = "roadtalk"
}

variable "enable_monitoring" {
  description = "Explicit opt-in for minimal alarms, logs, and budget controls."
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Operational contact; required only when monitoring is enabled."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly field-test budget limit."
  type        = number
  default     = 20
}
