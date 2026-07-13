variable "enable_bootstrap" {
  description = "Explicit opt-in. The default plan creates no resources."
  type        = bool
  default     = false
}

variable "aws_region" {
  description = "AWS region for the state bucket."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Globally unique Terraform state bucket name."
  type        = string
  default     = ""

}
