# Monitoring and cost controls

## Minimal enabled baseline

Field test cannot be enabled unless `enable_monitoring = true`. The baseline uses:

- existing five-minute EC2 basic metrics (detailed monitoring remains off);
- one instance-status alarm;
- one sustained CPU alarm;
- one SNS topic/email subscription;
- one API log group with three-day retention;
- one monthly budget with forecasted 80% and actual 100% email notifications.

CloudWatch alarms and log ingestion can incur small charges. This is the minimum
accepted field-test set; no paid dashboard, custom metric, high-frequency metric,
Container Insights, X-Ray, or cost-anomaly service is enabled.

## Privacy

The API emits structured events, correlation IDs, paths, statuses, and latency only.
Never log authorization headers, request/response bodies, refresh credentials,
location, profile data, audio, database URLs, or runtime parameter values.

Search a narrow time window to limit Logs Insights query cost:

```text
fields @timestamp, event, request_id, status_code, duration_ms
| filter status_code >= 500
| sort @timestamp desc
| limit 50
```

## Alarm rehearsal

1. confirm the SNS email subscription;
2. temporarily lower the CPU threshold in a reviewed plan or use the CloudWatch
   `set-alarm-state` test API;
3. verify the notification reaches the operational contact;
4. restore the real threshold and record evidence;
5. test instance-status routing without stopping the production-like data volume.

Never generate uncontrolled load merely to trigger an alarm.

## Budget response

At 80% forecast:

1. verify the field test is actively needed;
2. stop the instance outside scheduled testing if acceptable;
3. inspect EC2, public IPv4, EBS, ECR, S3, logs, and alarm charges;
4. remove stale images/backups only within retention policy.

At 100% actual, pause the field test unless the owner explicitly approves continued
spend. A budget is notification, not an automatic shutdown.

## Scaling rule

Do not resize from `t4g.small` or add managed services from a single alarm. Require
sustained measurements, profiling, a cost comparison, and a reviewed Terraform plan.
