output "state_bucket_name" {
  description = "State bucket name, or null while bootstrap is disabled."
  value       = try(aws_s3_bucket.state[0].id, null)
}

output "backend_configuration" {
  description = "Non-secret backend values for field-test initialization."
  value = var.enable_bootstrap ? {
    bucket       = aws_s3_bucket.state[0].id
    key          = "field-test/terraform.tfstate"
    region       = var.aws_region
    use_lockfile = true
  } : null
}
