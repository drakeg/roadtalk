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
  description = "Small monthly field-test budget limit."
  type        = number
  default     = 20
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
