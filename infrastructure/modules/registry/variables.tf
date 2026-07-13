variable "name" {
  description = "ECR repository name."
  type        = string
}

variable "retained_images" {
  description = "Small number of images retained for rollback."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
}
