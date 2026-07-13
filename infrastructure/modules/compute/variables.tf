variable "name" {
  description = "Resource name prefix."
  type        = string
}

variable "vpc_id" {
  description = "VPC containing the field-test host."
  type        = string
}

variable "subnet_id" {
  description = "Public subnet for the field-test host."
  type        = string
}

variable "instance_type" {
  description = "ARM instance type; increase only after measured load requires it."
  type        = string
  default     = "t4g.small"

  validation {
    condition     = startswith(var.instance_type, "t4g.")
    error_message = "The field-test baseline must use a t4g ARM instance."
  }
}

variable "root_volume_size_gb" {
  description = "Encrypted gp3 root/data volume size."
  type        = number
  default     = 40

  validation {
    condition     = var.root_volume_size_gb >= 40
    error_message = "The field-test recovery baseline requires at least 40 GB."
  }
}

variable "backup_bucket_arn" {
  description = "ARN of the off-instance backup bucket."
  type        = string
}

variable "repository_arn" {
  description = "ECR repository the host may pull."
  type        = string
}

variable "runtime_parameter_prefix" {
  description = "SSM parameter path populated out-of-band; secret values never enter Terraform."
  type        = string
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
}
