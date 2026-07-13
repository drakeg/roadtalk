#!/bin/sh
set -eu

instance_id="${1:?instance ID is required}"
region="${AWS_REGION:-us-east-1}"
parameters='{"commands":["set -euo pipefail","/opt/roadtalk/rollback.sh"]}'

command_id="$(aws ssm send-command --region "$region" --instance-ids "$instance_id" --document-name AWS-RunShellScript --comment "RoadTalk rollback" --parameters "$parameters" --query Command.CommandId --output text)"
aws ssm wait command-executed --region "$region" --command-id "$command_id" --instance-id "$instance_id"
aws ssm get-command-invocation --region "$region" --command-id "$command_id" --instance-id "$instance_id"
