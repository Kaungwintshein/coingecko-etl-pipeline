terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_db_subnet_group" "warehouse" {
  name       = "${var.project_name}-warehouse-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_security_group" "warehouse" {
  name        = "${var.project_name}-warehouse-rds-sg"
  description = "PostgreSQL access for the ETL warehouse"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL from approved CIDR blocks"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_postgres_cidrs
  }

  egress {
    description = "Outbound access"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_db_instance" "warehouse" {
  identifier             = "${var.project_name}-${var.environment}-warehouse"
  engine                 = "postgres"
  engine_version         = var.postgres_engine_version
  instance_class         = var.db_instance_class
  allocated_storage      = var.allocated_storage_gb
  max_allocated_storage  = var.max_allocated_storage_gb
  storage_type           = "gp3"
  db_name                = var.database_name
  username               = var.database_username
  password               = var.database_password
  db_subnet_group_name   = aws_db_subnet_group.warehouse.name
  vpc_security_group_ids = [aws_security_group.warehouse.id]
  publicly_accessible    = false
  skip_final_snapshot    = var.skip_final_snapshot
  deletion_protection    = var.deletion_protection
  backup_retention_period = var.backup_retention_days
  apply_immediately      = false

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
