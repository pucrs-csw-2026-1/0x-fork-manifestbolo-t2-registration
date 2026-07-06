variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "ministack_endpoint" {
  description = "Base endpoint of the shared external Ministack (LocalStack-compatible), used by all services in the platform."
  type        = string
  default     = "http://host.docker.internal:4566"
}

variable "db_name" {
  description = "Database name. Kept as app_db to match the existing app/.env.example convention."
  type        = string
  default     = "app_db"
}

variable "db_username" {
  type    = string
  default = "postgres"
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "postgres"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}
