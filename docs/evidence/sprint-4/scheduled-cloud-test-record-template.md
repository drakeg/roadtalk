# Sprint 4 scheduled provider/AWS test record

- Status: Not run
- Date/time and pricing check (UTC):
- Operator / destroy owner / reviewer:
- Approved issue/change record:
- Commit and immutable image:
- Region and environment label:
- Approved start/end time:

## Pre-cost estimate

| Cost/usage driver | Current month | Maximum added by window | Post-window retained | Planning cost |
|---|---:|---:|---:|---:|
| EC2 `t4g.small` hours |  |  |  |  |
| 40 GB gp3 duration |  |  |  |  |
| Public IPv4 duration |  |  |  |  |
| ECR/S3/backups |  |  |  |  |
| CloudWatch/SNS/Budget |  |  |  |  |
| Data transfer |  |  |  |  |
| LiveKit participant-minutes |  |  |  | $0 Build only |
| LiveKit downstream GB / peak connections |  |  |  | $0 Build only |
| **Total incremental USD** |  |  |  |  |

- [ ] Maximum estimate is at or below $10 and explicitly approved
- [ ] Provider dashboard headroom exceeds the complete script
- [ ] Disabled Terraform plan reports zero resources
- [ ] Enabled private plan contains only the approved single-host design
- [ ] `monthly_budget_usd = 10`; alerts are understood not to be automatic shutdown
- [ ] Destroy procedure, credentials, backup decision, and independent inventory are ready

## Window execution

| Time/step | Expected | Actual aggregate result | Review/stop status | Decision |
|---|---|---|---|---|
|  |  |  |  |  |

Never include provider secrets/tokens, request bodies, audio/transcripts, callsigns,
coordinates, account/device/session IDs, room/participant references, public IPs,
database contents, or unrestricted logs.

## Mandatory stop and destroy record

- Client disconnect completed at:
- Provider grants/participants contained at:
- Provider keys revoked at:
- Disposable provider project deletion/no-valid-key verification at:
- Terraform destroy started/completed at:
- Post-destroy enabled plan result:
- Disabled plan zero-resource result:
- Independent EC2/EBS/snapshot/IPv4/ECR/S3/CloudWatch/SNS/Budget/SSM inventory result:
- Retained item, reason, owner, deletion date, and accepted monthly cost:
- Final participant-minutes / downstream GB / peak concurrency:
- Final estimated/actual AWS and LiveKit cost:
- Delayed billing/usage recheck date and owner:

## Decision

- [ ] Passed and fully destroyed
- [ ] Passed with explicitly approved retained cost
- [ ] Failed and contained
- [ ] Blocked before activation

Follow-ups and reviewer approval:
