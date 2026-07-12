#!/bin/sh
set -eu

for module in infrastructure/modules/*; do
  test -f "$module/variables.tf" || {
    echo "Missing module contract: $module/variables.tf"
    exit 1
  }
  test -f "$module/outputs.tf" || {
    echo "Missing module contract: $module/outputs.tf"
    exit 1
  }
done

prohibited_resources='aws_nat_gateway|aws_db_instance|aws_rds_cluster|aws_elasticache_|aws_lb|aws_ecs_'
if grep -ERn "resource[[:space:]]+\"($prohibited_resources)" infrastructure --include='*.tf'; then
  echo "A prohibited recurring-cost field-test resource was detected."
  exit 1
fi

if grep -ERn 'from_port[[:space:]]*=[[:space:]]*(5432|6379)' infrastructure --include='*.tf'; then
  echo "A public database or cache ingress port was detected."
  exit 1
fi

grep -q 'default[[:space:]]*=[[:space:]]*false' infrastructure/bootstrap/variables.tf
grep -q 'default[[:space:]]*=[[:space:]]*false' \
  infrastructure/environments/field-test/variables.tf

echo "Terraform cost, network, and module-contract guardrails passed."
