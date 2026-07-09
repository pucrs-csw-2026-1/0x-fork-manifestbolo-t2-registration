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

  lifecycle {
    # A Ministack (LocalStack) popula `max_allocated_storage` na instancia, gerando
    # um diff perpetuo (20 -> null) que trava o `terraform apply` de reconciliacao
    # num ModifyDBInstance nao completado pelo emulador. Ignorar mantem o
    # `docker compose up` idempotente (re-apply vira no-op) sem afetar o create.
    ignore_changes = [max_allocated_storage]
  }
}
