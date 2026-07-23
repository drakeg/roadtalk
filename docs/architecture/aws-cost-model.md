# RoadTalk AWS Cost Model

- Status: Planning estimate
- Region: `us-east-1`
- AWS pricing checked: 2026-07-12
- LiveKit pricing checked: 2026-07-16
- Issue: #10
- Requirements: S00-R06
- Acceptance: S00-T04

Prices change. Recalculate in AWS Pricing Calculator immediately before deployment. Taxes, support, CI services, developer accounts, and unexpected transfer are excluded.

## Assumptions

- 730 hours/month
- ARM Linux where supported
- low-volume invite-only field testing
- LiveKit Cloud Build where eligible; it has hard monthly caps and no paid overage
- field-test Terraform currently defaults to one `t4g.small`, not `t4g.medium`
- eligible t4g.small usage may use the AWS Graviton free trial through 2026-12-31
- one public IPv4 in field test
- 40 GB gp3 field-test storage
- modest logs and backups
- no NAT Gateway in field test
- no Route 53 hosted-zone assumption
- no audio recording or egress

## Field-test estimate

| Item | Planning estimate/month | Basis |
|---|---:|---|
| EC2 `t4g.small` | $12.26 normally; $0 during an applicable promotion | $0.0168/hour planning rate × 730. AWS currently advertises up to 750 hours/month free through 2026-12-31 for eligible use; confirm account eligibility. |
| 40 GB gp3 EBS | $3.20 | $0.08/GB-month. |
| Public IPv4 | $3.65 | $0.005/hour × 730. |
| S3 backups | $0–$1 | Low-volume estimate including requests and short retention. |
| CloudWatch/SNS/Budget | $1–$3 | Three-day logs, two alarms, one route, and one budget; no paid dashboards/custom metrics. |
| Control-plane data transfer | $0–$1 | Low-volume estimate; media is handled by LiveKit Cloud. |
| LiveKit Cloud Build | $0 | Separate hard usage caps apply; see the media scenarios below. |
| **Expected without compute promotion** | **$20–$23 plus unusual transfer** | Before tax/support and assuming the small instance passes load evidence. |
| **Expected with applicable compute promotion** | **$8–$11 plus unusual transfer** | Promotion ends 2026-12-31 and requires account/workload eligibility. |

The low-cost default is `t4g.small`. It must be resized only after measured memory,
CPU-credit, disk-latency, or network evidence shows it cannot meet the controlled
field-test targets. A resize creates an explicit new monthly-cost decision.

## Sprint 4 LiveKit Cloud scenarios

Pricing checked on 2026-07-16. LiveKit measures participant connection time in
one-minute increments and downstream transfer in 0.01 GB increments. Connection time,
not speaking time, is the primary minute driver for a receive-ready PTT client.

| Plan/scenario | Included use | Planning cost/month |
|---|---|---:|
| Cloud disabled; local/CI fakes only | No provider project or calls | **$0** |
| Build | 5,000 WebRTC participant-minutes, 50 GB downstream transfer, 100 concurrent connections; hard caps | **$0** |
| Ship | 150,000 WebRTC participant-minutes and 250 GB downstream transfer | **$50 minimum** |
| Ship overage | Usage above included Ship amounts | $0.0005/participant-minute and $0.12/GB |

Build has no paid overage: new requests fail after an included allowance is exhausted.
RoadTalk's proposed controlled-test stops are lower—3,000 participant-minutes,
10 GB/month, and 25 concurrent connections—so a usage-reporting delay or test overrun
retains headroom. Crossing a stop pauses testing and never triggers an upgrade.

Combined planning scenarios:

- code/CI only: **$0/month**;
- LiveKit Build with AWS disabled: **$0/month**;
- enabled AWS field test plus Build: **$20–$23/month**, or **$8–$11/month** during an
  applicable compute promotion;
- enabled AWS field test plus Ship: **$70–$73+/month**, or **$58–$61+/month** during
  an applicable compute promotion.

The zero-revenue default is **$0/month**, with an initial hard operating ceiling of
**$10/month**. Scheduled AWS testing is planned at about **$4–$6 in an active test
month**; destroying the stack returns an inactive month to $0, while intentionally
retaining disk/backups may cost about $3–$5.

The earlier $35 and $85 amounts are no longer default budgets. They are scenario
references only if a future written decision approves always-on Build or Ship. No
automatic plan upgrade, scaling, or payment-method attachment is allowed. Recording,
egress, transcription, telephony, agents, enhanced paid audio processing, and
self-hosting remain excluded.

## Zero-revenue operating policy

- Development, CI, and inactive months target **$0**.
- Prefer local services and deterministic provider fakes.
- Use LiveKit Build only for separately approved physical-device tests.
- Use scheduled AWS test windows; stop or destroy resources immediately afterward.
- Do not preserve EBS, snapshots, backups, public IPv4, logs, or secrets merely for
  convenience without accepting their continuing cost.
- Any projected recurring spend above **$10/month** requires explicit approval.
- No always-on public deployment until demand, funding, or a revenue path justifies it.
- Cost estimates are refreshed before activation and reported after every test window.

## Managed production baseline estimate

| Item | Planning estimate/month | Notes |
|---|---:|---|
| One Fargate ARM task, 0.5 vCPU/1 GB | ~$14–$18 | Verify current ARM rate; two tasks approximately double compute. |
| ALB fixed charge | ~$16.43 | $0.0225/hour × 730, before LCUs. |
| ALB usage | ~$5.84 minimum planning allowance | One LCU-hour at $0.008; actual highest dimension applies. |
| RDS PostgreSQL single-AZ small burstable | $15–$30 | Instance-class price must be calculated immediately before deploy. |
| RDS storage/backups | $3–$10 | Size, retention, and backup overage dependent. |
| ECR, S3, CloudWatch, secrets | $5–$20 | Log/metric and secret counts drive cost. |
| Public IPv4/service-managed addresses | $3.65+ each | Inventory all addresses. |
| Data transfer | variable | Control traffic and media-provider egress vary. |
| LiveKit Cloud | variable | Connection minutes and downstream bandwidth are metered. |
| **Single-task/single-AZ planning range** | **$65–$110 plus transfer/media** | Not an availability commitment. |
| **Two-task/Multi-AZ planning range** | **$110–$200+ plus transfer/media** | Recalculate with exact RDS class and traffic. |

## Major cost drivers

1. realtime downstream audio bandwidth and connected participant minutes
2. managed database availability class
3. ALB and public IPv4 fixed costs
4. log ingestion/retention and custom metrics
5. NAT Gateway if introduced
6. multi-AZ redundancy
7. data transfer and TURN relay rate

## Cost controls

- AWS Budget alerts at $25, $50, $100, and forecasted overage during field test
- cost-anomaly detection
- short log retention with explicit extensions
- no NAT Gateway in field test
- no managed Redis until required
- one Region and limited test enrollment
- no recording/transcription/egress
- resource tagging: application, environment, owner, sprint, managed-by
- monthly cost review and per-active-user/per-audio-minute reporting
- delete unused snapshots, volumes, addresses, load balancers, and test stacks
- no commitment purchase until at least three months of stable utilization

## Media cost measurement

Track:

- unique active users
- connected participant minutes
- publisher minutes
- downstream audio GB
- TURN relay percentage
- average and peak concurrency
- cost per active user and per delivered audio minute

Self-host LiveKit only when a documented three-month total-cost comparison includes EC2, bandwidth, load balancing, public IPs, TURN, Redis, monitoring, upgrades, on-call effort, and failure risk.

## Primary pricing references

- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)
- [AWS VPC and public IPv4 pricing](https://aws.amazon.com/vpc/pricing/)
- [AWS RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/)
- [AWS Graviton free trial](https://aws.amazon.com/ec2/instance-types/c6g/)
- [LiveKit pricing](https://livekit.com/pricing)
- [LiveKit Cloud billing](https://docs.livekit.io/deploy/admin/billing/)
