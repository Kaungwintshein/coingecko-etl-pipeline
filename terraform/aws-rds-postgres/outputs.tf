output "warehouse_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.warehouse.address
}

output "warehouse_port" {
  description = "RDS PostgreSQL port."
  value       = aws_db_instance.warehouse.port
}

output "warehouse_database_name" {
  description = "Warehouse database name."
  value       = aws_db_instance.warehouse.db_name
}

output "warehouse_security_group_id" {
  description = "Security group attached to the warehouse RDS instance."
  value       = aws_security_group.warehouse.id
}
