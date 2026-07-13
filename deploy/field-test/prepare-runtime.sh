#!/bin/sh
set -eu

region="${AWS_REGION:-us-east-1}"
path="/roadtalk/field-test/"
umask 077
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

aws ssm get-parameters-by-path +  --region "$region" +  --path "$path" +  --recursive +  --with-decryption +  --output json > "$tmp"

python3 - "$tmp" > /opt/roadtalk/runtime.env <<'PY'
import json
import re
import sys

allowed = re.compile(r"^[A-Z][A-Z0-9_]*$")
with open(sys.argv[1], encoding="utf-8") as source:
    parameters = json.load(source)["Parameters"]
for parameter in parameters:
    name = parameter["Name"].rsplit("/", 1)[-1]
    value = parameter["Value"]
    if not allowed.fullmatch(name) or "\n" in value or "\r" in value:
        raise SystemExit(f"Invalid runtime parameter: {name}")
    print(f"{name}={value}")
PY

cp /opt/roadtalk/runtime.env /opt/roadtalk/deployment.env
chmod 0600 /opt/roadtalk/runtime.env /opt/roadtalk/deployment.env
