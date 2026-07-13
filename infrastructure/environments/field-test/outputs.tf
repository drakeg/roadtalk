output "instance_id" {
  description = "Field-test host ID, or null while disabled."
  value       = try(module.compute[0].instance_id, null)
}

output "public_ip" {
  description = "Ephemeral public IP, or null while disabled."
  value       = try(module.compute[0].public_ip, null)
}

output "backup_bucket_name" {
  description = "Encrypted backup bucket, or null while disabled."
  value       = try(module.backup[0].bucket_name, null)
}

output "runtime_parameter_path" {
  description = "Out-of-band SSM path; secret values are never Terraform inputs."
  value       = var.enable_field_test ? "/roadtalk/field-test/" : null
}

output "repository_url" {
  description = "Immutable ECR repository URL, or null while disabled."
  value       = try(module.registry[0].repository_url, null)
}
