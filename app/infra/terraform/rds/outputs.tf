output "database_url" {
  description = "SQLAlchemy-compatible connection string for app/src/database.py (DATABASE_URL)."
  value       = "postgresql+psycopg2://${var.db_username}:${var.db_password}@${aws_db_instance.registration.address}:${aws_db_instance.registration.port}/${var.db_name}"
  sensitive   = true
}

output "db_host" {
  value = aws_db_instance.registration.address
}

output "db_port" {
  value = aws_db_instance.registration.port
}
