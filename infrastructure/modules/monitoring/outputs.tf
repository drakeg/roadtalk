output "log_group_name" {
  description = "API log group."
  value       = aws_cloudwatch_log_group.api.name
}

output "alerts_topic_arn" {
  description = "Operational alarm topic."
  value       = aws_sns_topic.alerts.arn
}
