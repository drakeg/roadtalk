#!/bin/sh
set -eu

instance_id="${1:?instance ID is required}"
image="${2:?immutable image URI is required}"
region="${AWS_REGION:-us-east-1}"
registry="${image%%/*}"

parameters="$(IMAGE="$image" REGION="$region" REGISTRY="$registry" python3 <<'PY'
import json
import os

image = os.environ["IMAGE"]
region = os.environ["REGION"]
registry = os.environ["REGISTRY"]
commands = [
    "set -euo pipefail",
    f"aws ecr get-login-password --region {region} | "
    f"docker login --username AWS --password-stdin {registry}",
    f"docker pull {image}",
    f"container=$(docker create {image})",
    "rm -rf /tmp/roadtalk-deploy && mkdir -p /tmp/roadtalk-deploy",
    "docker cp $container:/opt/roadtalk/deploy/. /tmp/roadtalk-deploy/",
    "docker rm $container",
    "install -d -m 0750 /opt/roadtalk",
    "cp /tmp/roadtalk-deploy/* /opt/roadtalk/",
    "chmod 0750 /opt/roadtalk/*.sh",
    "/opt/roadtalk/prepare-runtime.sh",
    f"/opt/roadtalk/deploy.sh {image}",
]
print(json.dumps({"commands": commands}))
PY
)"

command_id="$(aws ssm send-command --region "$region" --instance-ids "$instance_id" --document-name AWS-RunShellScript --comment "RoadTalk immutable deployment" --parameters "$parameters" --query Command.CommandId --output text)"
aws ssm wait command-executed --region "$region" --command-id "$command_id" --instance-id "$instance_id"
aws ssm get-command-invocation --region "$region" --command-id "$command_id" --instance-id "$instance_id" --query '{Status:Status,Output:StandardOutputContent,Error:StandardErrorContent}'
