variable "aws_region" {
  description = "AWS region where RDS will be provisioned."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project name used in resource names."
  type        = string
  default     = "coingecko-etl"
}

variable "environment" {
  description = "Environment label, such as dev or prod."
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "VPC ID for the RDS security group."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the RDS subnet group. Use at least two subnets in different AZs."
  type        = list(string)
}

variable "allowed_postgres_cidrs" {
  description = "CIDR blocks allowed to connect to PostgreSQL. Keep this narrow."
  type        = list(string)
  default     = []
}

variable "postgres_engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "16.3"
}

variable "db_instance_class" {
  description = "RDS instance class. db.t4g.micro is commonly Free Tier eligible in supported regions/accounts."
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage_gb" {
  description = "Initial allocated storage in GB."
  type        = number
  default     = 20
}

variable "max_allocated_storage_gb" {
  description = "Maximum autoscaled storage in GB."
  type        = number
  default     = 100
}

variable "database_name" {
  description = "Initial warehouse database name."
  type        = string
  default     = "crypto_warehouse"
}

variable "database_username" {
  description = "Master username for the database."
  type        = string
  default     = "warehouse_user"
}

variable "database_password" {
  description = "Master password for the database. Pass through terraform.tfvars or TF_VAR_database_password."
  type        = string
  sensitive   = true
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot on deletion. Use false for production."
  type        = bool
  default     = true
}
