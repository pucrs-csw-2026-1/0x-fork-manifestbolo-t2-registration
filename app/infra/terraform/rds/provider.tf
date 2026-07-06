terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Points at the shared external Ministack (LocalStack-compatible) instance,
# not a real AWS account. Credentials are fake by design (Ministack ignores
# them), same pattern already used by app/src/aws.py for the SNS client.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    rds = var.ministack_endpoint
    sns = var.ministack_endpoint
  }
}
