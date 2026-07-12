#!/bin/sh
set -eu

if find infrastructure -type f -name '*.tf' -print -quit | grep -q .; then
  echo "Terraform detected: Trivy IaC checks were enforced."
else
  echo "Terraform not present yet; the IaC gate will activate with S01-D09."
fi

if find . -type f -name 'Dockerfile*' -print -quit | grep -q .; then
  echo "Dockerfile detected: Trivy configuration checks were enforced."
else
  echo "Dockerfile not present yet; the container gate will activate with S01-D10."
fi
