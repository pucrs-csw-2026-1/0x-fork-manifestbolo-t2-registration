resource "aws_db_instance" "registration" {
  identifier          = "registration-db"
  engine              = "postgres"
  engine_version      = "15"
  instance_class      = var.db_instance_class
  allocated_storage   = 20
  db_name             = var.db_name
  username            = var.db_username
  password            = var.db_password
  port                = 5432
  publicly_accessible = true
  skip_final_snapshot = true
  apply_immediately   = true
}
