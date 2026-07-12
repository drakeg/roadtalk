# RoadTalk AWS Cost Model

- Status: Planning estimate
- Region: `us-east-1`
- Pricing checked: 2026-07-12
- Issue: #10
- Requirements: S00-R06
- Acceptance: S00-T04

Prices change. Recalculate in AWS Pricing Calculator immediately before deployment. Taxes, support, CI services, developer accounts, and unexpected transfer are excluded.

## Assumptions

- 730 hours/month
- ARM Linux where supported
- low-volume invite-only field testing
- LiveKit Cloud Build/free tier where eligible; media overages remain usage-dependent
- one public IPv4 in field test
- 40 GB gp3 field-test storage
- modest logs and backups
- no NAT Gateway in field test
- no Route 53 hosted-zone assumption
- no audio recording or egress

## Field-test estimate

| Item | Planning estimate/month | Basis |
|---|---:|---|
| EC2 `t4g.medium` | $24.53 | $0.0336/hour planning rate × 730; confirm in calculator. |
| 40 GB gp3 EBS | $3.20 | $0.08/GB-month. |
| Public IPv4 | $3.65 | $0.005/hour × 730. |
| S3 backups | $1–$3 | Low-volume estimate including requests. |
| CloudWatch | $2–$8 | Depends on log volume, retention, custom metrics. |
| Data transfer | $0–$10+ | Usage-dependent; media is handled by LiveKit Cloud. |
| LiveKit Cloud | $0+ | Plan and usage dependent; verify current quotas/rates. |
| **Expected fixed/low-use range** | **$34–$49 plus transfer/media** | Before tax/support. |

A smaller instance may be tested, but `t4g.medium` is the minimum planning target for co-located API, PostgreSQL, and Redis. The instance must be resized if memory, CPU credits, disk latency, or network performance fails NFR testing.

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
- [LiveKit pricing](https://livekit.io/pricing)
- [LiveKit Cloud billing](https://docs.livekit.io/deploy/admin/billing/)
