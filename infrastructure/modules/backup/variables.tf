variable "bucket_name" {
  description = "Globally unique off-instance backup bucket name."
  type        = string
}

variable "retention_days" {
  description = "Days to retain current backup objects."
  type        = number
  default     = 30

  validation {
    condition     = var.retention_days >= 7 && var.retention_days <= 365
    error_message = "Backup retention must be between 7 and 365 days."
  }
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
}
