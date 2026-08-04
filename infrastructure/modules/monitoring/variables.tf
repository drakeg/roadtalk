variable "name" {
  description = "Resource name prefix."
  type        = string
}

variable "instance_id" {
  description = "Field-test EC2 instance ID."
  type        = string
}

variable "alert_email" {
  description = "Operational email for alarm and budget notifications."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Hard monthly field-test notification ceiling."
  type        = number
  default     = 10

  validation {
    condition     = var.monthly_budget_usd > 0 && var.monthly_budget_usd <= 10
    error_message = "monthly_budget_usd must be from $1 through the approved $10 ceiling."
  }
}

variable "log_retention_days" {
  description = "Short retention to minimize ingestion/storage cost."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags applied to supported resources."
  type        = map(string)
}
