# Optional AWS RDS PostgreSQL Terraform Scaffold

This directory demonstrates how the local PostgreSQL warehouse could be promoted to a managed PostgreSQL target on AWS RDS.

It is intentionally optional. The primary portfolio project runs locally with Docker Compose so reviewers can execute it without a cloud account.

## Prerequisites

- Terraform `>= 1.6`
- AWS credentials configured outside the repository
- Existing VPC and private subnets
- A narrow CIDR range allowed to connect to PostgreSQL

## Usage

```bash
cd terraform/aws-rds-postgres
terraform init
terraform validate
```

Create a local `terraform.tfvars` file that is not committed:

```hcl
vpc_id                 = "vpc-xxxxxxxx"
private_subnet_ids     = ["subnet-aaaa", "subnet-bbbb"]
allowed_postgres_cidrs = ["10.0.0.0/16"]
database_password      = "replace-with-a-strong-secret"
```

Plan and apply only when you intentionally want to create cloud resources:

```bash
terraform plan
terraform apply
```

## Security Notes

- Do not commit `terraform.tfvars` or state files.
- Prefer private subnets and VPN/bastion access.
- Keep `allowed_postgres_cidrs` as narrow as possible.
- Use AWS Secrets Manager or a CI/CD secret store for production credentials.
