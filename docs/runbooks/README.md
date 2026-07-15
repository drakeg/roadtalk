# Operational runbooks

These runbooks are the operator entry point for Sprint 1 and Sprint 2. Follow them exactly, use
only synthetic data, and record evidence without secrets, tokens, database dumps,
or personal data.

| Operation | Runbook | Evidence to retain |
|---|---|---|
| Clean machine setup | [Clean setup](clean-setup.md) | Tool versions and successful health/test results |
| Authentication lifecycle | [Authentication operations](authentication-operations.md) | Redacted status codes and correlation IDs |
| Identity and anonymous recovery | [Identity and recovery operations](identity-recovery-operations.md) | Stable problem codes, route templates, synthetic lifecycle result |
| CI failure triage | [CI quality and security](ci-quality-security.md) | Workflow URL, failed gate, corrective commit |
| Field-test deploy/rollback | [Field-test deployment](field-test-deployment.md) | Commit, image digest, SSM command IDs, health results |
| Backup/restore | [Database backup and restore](database-backup-restore.md) | Object key/version, checksums, row-count comparison |
| Secret changes | [Credential rotation](credential-rotation.md) | Parameter names/versions, time, approver, validation |
| Alarms, logs, and budget | [Monitoring and cost controls](monitoring-cost-controls.md) | Alarm notification and bounded query result |

## Safety rules

- Stop when the target environment, AWS account, region, or backup is ambiguous.
- Never paste secret values into Git, tickets, chat, logs, workflow inputs, or shell
  history. Use an approved masked secret-entry path.
- Take and verify a pre-change backup before a destructive restore or data change.
- Preserve immutable image digests and database backups independently.
- Roll back application code without downgrading the database automatically.
- Keep field-test infrastructure disabled except during an approved test window;
  no runbook authorizes RDS, NAT Gateway, load balancer, Fargate, or managed Redis.
- Never request a callsign or recovery key as diagnostic evidence. There is no
  support or administrator bypass for a lost anonymous recovery key.

## Rehearsal record

For S01-T12, create one evidence record containing date, operator, environment,
starting and ending commit, commands/actions (with values redacted), expected and
actual results, artifact identifiers, duration, cost impact, and follow-ups. Exercise:

1. image A to image B deployment followed by application rollback to A;
2. a backup restored into a disposable database and compared with its source;
3. credential-rotation review, including signing-key session impact and rollback;
4. field-test shutdown after evidence collection.

The runbooks are complete when a reviewer can reproduce each bounded procedure.
Execution evidence belongs in S01-D13, not in this directory.
