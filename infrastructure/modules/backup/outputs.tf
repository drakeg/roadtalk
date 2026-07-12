output "bucket_arn" {
  description = "Backup bucket ARN."
  value       = aws_s3_bucket.this.arn
}

output "bucket_name" {
  description = "Backup bucket name."
  value       = aws_s3_bucket.this.id
}
