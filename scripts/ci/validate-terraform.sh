#!/bin/sh
set -eu

terraform fmt -check -recursive infrastructure

for root in infrastructure/bootstrap infrastructure/environments/field-test; do
  terraform -chdir="$root" init -backend=false -input=false
  terraform -chdir="$root" validate
  AWS_ACCESS_KEY_ID=disabled-plan \
    AWS_SECRET_ACCESS_KEY=disabled-plan \
    terraform -chdir="$root" plan -refresh=false -input=false -detailed-exitcode
done

tflint --chdir=infrastructure/bootstrap
tflint --chdir=infrastructure/environments/field-test --call-module-type=all

sh scripts/ci/check-terraform-guardrails.sh
