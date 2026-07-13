output "instance_id" {
  description = "Field-test EC2 instance ID."
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Ephemeral public IPv4 address; DNS must tolerate replacement."
  value       = aws_instance.this.public_ip
}

output "security_group_id" {
  description = "Host security group ID."
  value       = aws_security_group.this.id
}
