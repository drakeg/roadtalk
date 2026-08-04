# Push-to-Talk operations and cost controls

- Deliverable: S04-D08
- Issue: #98
- Requirements: S04-R01, S04-R05, S04-R09–R12
- Acceptance: S04-T01, S04-T05, S04-T09–T11
- Pricing verified: 2026-08-03

## Scope and current state

This runbook governs synthetic PTT rehearsal, any later approved LiveKit Build test,
provider credential activation/rotation/revocation, and an optional scheduled AWS
field-test window. It does **not** authorize activation. As of S04-D08:

- AWS and LiveKit resources created by Sprint 4: **none**;
- live provider credentials or calls in source, CI, or shared evidence: **none**;
- current and incremental monthly cost: **$0 AWS + $0 LiveKit**;
- Terraform remains disabled and its default plan creates zero resources;
- the backend has a typed disabled provider boundary and deterministic fake, not an
  approved live-network adapter.

Live/provider and physical-device work remains blocked until the applicable Sprint 1
exceptions close, a live adapter is separately reviewed, and the product owner
approves the dated test plan. Do not represent this procedural runbook as completed
live-provider evidence.

## Activation stages

| Stage | Allowed posture | Projected monthly cost | Authority |
|---|---|---:|---|
| 0 — implementation | Local services and deterministic CI fakes; no provider project or AWS resource | **$0** | Current default |
| 1 — device-only Build test | Separately approved disposable LiveKit Build project; backend remains local | **$0** within RoadTalk stops | New test-window approval |
| 2 — scheduled AWS test | Existing single-host Terraform design plus Build, created only for a bounded test and then destroyed | **about $4–$6 in an active test month** | New dated estimate and approval; must remain below $10 |
| 3 — always-on or paid | Always-on AWS, LiveKit paid plan, automatic scaling/upgrade, or public beta | **Prohibited** | New architecture/cost decision required |

An inactive month with the AWS stack fully destroyed targets **$0**. Intentionally
retained storage/backups may cost about **$3–$5/month** and requires a recorded
retention decision. Always-on AWS is a scenario reference only: approximately
**$8–$11/month during an eligible promotion and $20–$23/month afterward**, before
unusual transfer, taxes, or support. It is not approved.

## Hard stops

RoadTalk pauses all controlled testing when any one of these is reached or projected
to be crossed during the approved window:

- **3,000 WebRTC participant-minutes per calendar month**;
- **10 GB downstream transfer per calendar month**;
- **25 concurrent participants**;
- **$10 total incremental cost in the active test month**.

Use operator review points at 2,250 participant-minutes, 7.5 GB, 20 concurrent
participants, and $8 forecasted cost. Review points are not permission to continue;
they exist to stop comfortably before the hard limits. Connection time, not speaking
time, drives participant-minutes, so disconnect every client outside the test step.

Crossing a review point requires the operator to decide whether the remaining script
can finish within every stop. Crossing a hard stop requires immediate pause,
participant disconnection, credential containment when appropriate, and owner
notification. It must never attach a payment method, upgrade LiveKit, resize AWS,
increase a quota/budget, or scale automatically. AWS Budget notifications and provider
dashboards are alerts, not automatic shutdown controls.

## Approval checklist before any live test

Do not create a project, credential, or AWS resource until every item is checked in a
reviewed [scheduled test record](../evidence/sprint-4/scheduled-cloud-test-record-template.md):

1. the specific Sprint 1 device/deployment exceptions required by the script are closed;
2. the exact commit, synthetic scenario, devices, region, start/end time, operator,
   reviewer, rollback, and stop owner are recorded;
3. official LiveKit and AWS pricing is rechecked and a dated maximum-cost estimate is
   below $10;
4. current-month AWS cost and LiveKit aggregate usage leave enough headroom for the
   whole script;
5. the default disabled Terraform plan is verified at zero resources;
6. any enabled Terraform plan is saved privately, reviewed, contains only the
   existing single-host field-test design, and uses a $10 budget;
7. the approved backend contains a reviewed live-provider adapter and remains
   fail-closed when configuration is absent;
8. synthetic accounts and speech content are prepared; no real callsign, location,
   account, device, room, participant, or credential value will enter evidence;
9. no recording, egress, transcription, telephony, agent, paid processing, RDS,
   managed Redis, NAT Gateway, ALB, Fargate, or self-hosting is present;
10. the post-test destroy and verification owner is available for the entire window.

## LiveKit Build activation

This procedure is a future, manual operator procedure; S04-D08 does not execute it.

1. Reconfirm the approved window and current Build allowances in the LiveKit dashboard.
2. Create a disposable Build project with no paid add-on, payment-method change,
   recording, ingress, egress, agents, telephony, or automatic upgrade.
3. Generate a least-privilege server API key through the provider UI. Enter its value
   only through the approved masked secret path; never use Git, CI variables, chat,
   tickets, shell arguments/history, screenshots, mobile configuration, or evidence.
4. Inject the project URL/key/secret only into the approved field-test runtime. Keep
   `ROADTALK_PTT_MEDIA_PROVIDER_ENABLED=false` everywhere else.
5. Deploy the reviewed immutable commit and prove missing/invalid configuration still
   fails closed before allowing a synthetic participant.
6. Run only the approved script while watching aggregate participant-minutes,
   downstream GB, and peak concurrency. Record totals, never room/participant values.
7. Disconnect all clients and continue immediately to revocation and shutdown.

## Provider credential rotation

Use this for planned rotation or suspected disclosure. Do not rotate merely to work
around a limit.

1. Stop new test joins and disconnect active synthetic participants.
2. Record the project/key label and provider audit timestamp only; never record values.
3. Create a new provider key using the masked secret path and update the field-test
   runtime secret as one reviewed change.
4. Restart/redeploy the same immutable application version and validate one bounded
   receive-only join, microphone-only hold/release, and participant removal.
5. Revoke the superseded key immediately after validation. If compromise is
   suspected, revoke first and accept test interruption.
6. Verify the old key fails, the new key remains server-only, logs/evidence contain no
   token or secret, and aggregate usage has not crossed a stop.
7. If validation fails, disable live-provider access and return to the deterministic
   fake; do not keep both credentials active as an unbounded rollback.

## Provider revocation and project shutdown

1. Stop new grants locally and disconnect every test device.
2. Revoke all project API keys and remove any remaining synthetic participants.
3. Delete the disposable project when the provider permits it; otherwise verify no
   active sessions, no paid feature, no payment-method change, and no valid key.
4. Confirm the provider dashboard reports the final aggregate minutes, transfer, and
   peak concurrency below RoadTalk stops.
5. Remove field-test runtime parameters through the approved secret manager and verify
   no provider value exists in Git, CI, mobile builds, tickets, or retained evidence.
6. Record only aggregate totals, provider audit timestamps, and pass/fail outcomes.

## Scheduled AWS test window

AWS is optional. Prefer a local backend with LiveKit Build whenever that proves the
approved device behavior.

### Pre-cost and plan check

1. Recalculate EC2 hours, gp3 duration, public IPv4 duration, monitoring, ECR/S3,
   backups, transfer, and retained-resource cost for the exact window.
2. Confirm month-to-date AWS cost plus the maximum estimate is below $10 and record the
   estimate. A range above $10 blocks activation even if a budget is configured.
3. Run the disabled plan and require zero resources.
4. Privately generate an enabled plan for the existing `t4g.small`, 40 GB gp3,
   single-host design with monitoring and `monthly_budget_usd = 10`; review the exact
   plan before applying it manually. CI never applies Terraform.
5. Confirm the test record names who will destroy resources even if the test fails.

### During the window

1. Follow the field-test deployment runbook and use only immutable images and synthetic data.
2. Watch AWS cost/forecast, instance status, and aggregate LiveKit usage at each script boundary.
3. Stop immediately on an unexpected resource, credential leak, private-data leak,
   failed cleanup, unavailable destroy owner, or any review/hard stop.
4. Do not resize, add services, increase budgets, or extend the window without a new
   plan, estimate, and explicit approval.

### Stop, destroy, and verify

1. Disconnect clients and complete provider revocation before dismantling the backend.
2. Preserve only privacy-safe identifiers required by the existing deployment/backup
   runbooks, then run the reviewed Terraform destroy.
3. Require a new enabled configuration plan to report no remaining managed resources.
4. Independently inventory EC2 instances, EBS volumes/snapshots, public IPv4/EIPs,
   ECR images, S3 objects/buckets, CloudWatch logs/alarms, SNS subscriptions, Budgets,
   and SSM parameters. Delete test artifacts unless a documented retention decision
   accepts their continuing cost.
5. Re-run the disabled plan and require zero resources.
6. Record destroy time, final aggregate usage, estimated/actual AWS cost, any retained
   item and monthly cost, and the operator/reviewer decision.
7. Check billing again after provider/AWS reporting settles. An unexplained charge or
   retained resource keeps the record open.

Stopping the EC2 instance alone is not a $0 state: gp3, snapshots/backups, logs, ECR,
and other retained items may continue charging. Full destroy plus independent
inventory is the preferred inactive posture.

## Synthetic rehearsal and approved evidence

Run local/CI tests with deterministic fakes and record only:

- commit and GitHub Actions run URL;
- test/gate name and pass/fail outcome;
- route template, HTTP status, and stable problem code when needed;
- aggregate counts, durations, percentiles, participant-minutes, GB, concurrency,
  and estimated/actual cost;
- opaque provider audit event time or cloud resource identifier only when a protected
  operational record truly requires it.

Never retain raw participant tokens, API keys/secrets, authorization headers, request
or response bodies, audio, transcripts, callsigns, coordinates, account/device/session
IDs, room/participant references, public IPs, unrestricted logs, or database dumps.
Do not record or upload audio to prove that audio worked; use two-operator observation
and metadata-only outcomes in the physical-device template.

See [Sprint 4 synthetic evidence](../evidence/sprint-4/README.md) and the
[physical-device template](../evidence/sprint-4/physical-device-media-test-template.md).

## Current pricing basis

Official information was rechecked on 2026-08-03. LiveKit documents Build allowances
of 5,000 WebRTC participant-minutes, 50 GB downstream transfer, and 100 concurrent
participants. RoadTalk's lower stops retain substantial headroom. AWS documents
public IPv4 at $0.005/hour and gp3 example pricing at $0.08/GB-month; the cost model's
`t4g.small` planning rate remains $0.0168/hour and must be recalculated before use.

Provider allowances, promotions, taxes, transfer, and account eligibility can change.
This runbook never treats a free allowance or notification budget as protection from
charges.

## References

- [RoadTalk AWS cost model](../architecture/aws-cost-model.md)
- [Field-test deployment](field-test-deployment.md)
- [Monitoring and cost controls](monitoring-cost-controls.md)
- [Credential rotation](credential-rotation.md)
- [LiveKit pricing](https://livekit.com/pricing)
- [LiveKit quotas and limits](https://docs.livekit.io/deploy/admin/quotas-and-limits/)
- [LiveKit Cloud billing](https://docs.livekit.io/deploy/admin/billing/)
- [AWS VPC/public IPv4 pricing](https://aws.amazon.com/vpc/pricing/)
- [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)
