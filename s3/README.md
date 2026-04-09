# S3 Object Storage — Complete Demo

Learn S3 buckets, storage classes, lifecycle policies, and cross-region replication.

## What You'll Learn

```
Single Region Bucket → Multi-Region Replication → Storage Classes → Lifecycle Management
```

## Understanding S3 Durability (11 9's)

### Automatic Multi-AZ Storage - No Configuration Needed!

When you upload an object to S3, it's **automatically** stored across multiple AZs:

```bash
# Create a bucket in ap-southeast-1 (Singapore)
BUCKET="durability-test-$(date +%s)"
aws s3api create-bucket \
  --bucket $BUCKET \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

# Upload an object - automatically stored in 3+ AZs
echo "Critical data" > important.txt
aws s3api put-object \
  --bucket $BUCKET \
  --key important.txt \
  --body important.txt

# PROOF: Check object details - available immediately from any AZ
aws s3api head-object \
  --bucket $BUCKET \
  --key important.txt

# The object is instantly available even if an AZ fails
# S3 automatically serves from healthy AZs - ZERO downtime
```

### How to Verify Multi-AZ Resilience

```bash
# Method 1: Check S3 Service Health Dashboard
# Even when an AZ has issues, your objects remain accessible
open https://status.aws.amazon.com/

# Method 2: CloudWatch Metrics show availability
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketRequests \
  --dimensions Name=BucketName,Value=$BUCKET \
  --statistics Sum \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600

# Method 3: Test from different AZs using EC2 instances
# Launch EC2 in different AZs of same region
# All can access the S3 object instantly - no special config needed
```

### What Happens During AZ Failure?

```
Normal Operation:
Client → S3 Endpoint → [AZ-1a ✓] [AZ-1b ✓] [AZ-1c ✓]
                        All 3 AZs have your data

AZ Failure (e.g., AZ-1b fails):
Client → S3 Endpoint → [AZ-1a ✓] [AZ-1b ✗] [AZ-1c ✓]
                        S3 automatically serves from healthy AZs
                        NO DOWNTIME - NO ACTION NEEDED!
```

### Key Points:
- **Instant**: No delay - S3 automatically routes to healthy AZs
- **Automatic**: No configuration needed - works out of the box
- **Transparent**: You don't even know which AZ is serving your request
- **No Extra Cost**: Multi-AZ durability is included in S3 pricing

### Durability vs Availability vs Replication

| Feature | What It Does | Automatic? | Use Case |
|---------|-------------|------------|----------|
| **Multi-AZ Durability** | Protects against AZ/hardware failure | ✅ Yes | Default protection |
| **S3 Availability** | 99.99% uptime SLA | ✅ Yes | Always accessible |
| **Cross-Region Replication** | Copies to different region | ❌ Manual | Region disaster/compliance |

```bash
# This is ALL you need for 11 9's durability:
aws s3api put-object --bucket $BUCKET --key file.txt --body file.txt

# That's it! Your data is now:
# ✓ In 3+ AZs
# ✓ Protected from AZ failure  
# ✓ Instantly accessible from any AZ
# ✓ No configuration needed
```

## Prerequisites

```bash
aws configure        # needs AWS credentials
```

## Part 1 — Create Single Region Bucket

Simple bucket in one region.

```bash
# Create bucket in ap-southeast-1 (Singapore)
aws s3api create-bucket \
  --bucket my-demo-bucket-$(date +%s) \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

# For us-east-1 (no location constraint needed)
aws s3api create-bucket \
  --bucket my-us-bucket-$(date +%s) \
  --region us-east-1

# Enable versioning (required for lifecycle and replication)
aws s3api put-bucket-versioning \
  --bucket my-demo-bucket-xxx \
  --versioning-configuration Status=Enabled
```

## Part 2 — Multi-Region with Replication

Set up cross-region replication for disaster recovery.

```bash
# Create source bucket (ap-southeast-1)
SOURCE_BUCKET="source-bucket-$(date +%s)"
aws s3api create-bucket \
  --bucket $SOURCE_BUCKET \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

# Create destination bucket (ap-southeast-2) for replication
DEST_BUCKET="dest-bucket-$(date +%s)"
aws s3api create-bucket \
  --bucket $DEST_BUCKET \
  --region ap-southeast-2 \
  --create-bucket-configuration LocationConstraint=ap-southeast-2

# Enable versioning on both (required for replication)
aws s3api put-bucket-versioning \
  --bucket $SOURCE_BUCKET \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket $DEST_BUCKET \
  --versioning-configuration Status=Enabled \
  --region ap-southeast-2

# Apply replication (see replication-config.json)
aws s3api put-bucket-replication \
  --bucket $SOURCE_BUCKET \
  --replication-configuration file://replication-config.json
```

## Part 3 — Upload with Storage Classes

Different storage classes for different access patterns.

```bash
# Create test files
echo "Hot data" > hot.txt
echo "Warm data" > warm.txt
echo "Cold data" > cold.txt

# STANDARD - Frequently accessed
aws s3api put-object \
  --bucket my-demo-bucket-1775136714 \
  --key data/hot.txt \
  --body hot.txt \
  --storage-class STANDARD \
  --metadata Type=Hot,Access=Frequent

# STANDARD_IA - Infrequent Access (30+ days)
aws s3api put-object \
  --bucket my-demo-bucket-1775136714 \
  --key archive/warm.txt \
  --body warm.txt \
  --storage-class STANDARD_IA \
  --metadata Type=Warm,Access=Monthly

# GLACIER_IR - Archive with instant retrieval
aws s3api put-object \
  --bucket my-demo-bucket-xxx \
  --key backup/cold.txt \
  --body cold.txt \
  --storage-class GLACIER_IR \
  --metadata Type=Cold,Access=Yearly

# INTELLIGENT_TIERING - Auto-moves between tiers
aws s3api put-object \
  --bucket my-demo-bucket-xxx \
  --key auto/data.txt \
  --body data.txt \
  --storage-class INTELLIGENT_TIERING \
  --metadata AutoTier=true
```

### Storage Class Comparison

| Class | Access Pattern | Retrieval Time | Cost | Use Case |
|-------|---------------|----------------|------|----------|
| STANDARD | Frequent | Immediate | $$$ | Active data |
| STANDARD_IA | Infrequent (30+ days) | Immediate | $$ | Backups |
| INTELLIGENT_TIERING | Unknown | Immediate | $$ + monitoring | Auto-optimize |
| GLACIER_IR | Rare | Immediate | $ | Long-term backup |
| GLACIER_FLEXIBLE | Very rare | 1-12 hours | ¢¢ | Archives |
| DEEP_ARCHIVE | Almost never | 12+ hours | ¢ | Compliance |

## Part 4 — Lifecycle Policies

Automatically transition objects between storage classes.

```bash
# Apply lifecycle configuration
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-demo-bucket-1775136714 \
  --lifecycle-configuration file://lifecycle-policy.json

# Verify
aws s3api get-bucket-lifecycle-configuration \
  --bucket my-demo-bucket-xxx
```

Lifecycle rules in `lifecycle-policy.json`:
- Documents: STANDARD → IA (30d) → GLACIER (90d) → Delete (365d)
- Logs: Delete after 7 days
- Backups: Keep for 180 days
- Incomplete uploads: Abort after 7 days

## Part 5 — List and Analyze

```bash
# List objects with storage class
aws s3api list-objects-v2 \
  --bucket my-demo-bucket-1775136714 \
  --query 'Contents[*].[Key,StorageClass,Size,LastModified]' \
  --output table

# Get object metadata
aws s3api head-object \
  --bucket my-demo-bucket-1775136714 \
  --key data/hot.txt

# Add tags for cost tracking
aws s3api put-object-tagging \
  --bucket my-demo-bucket-1775136714 \
  --key data/hot.txt \
  --tagging 'TagSet=[{Key=Environment,Value=Prod},{Key=Team,Value=DataEng}]'
```

## Part 6 — Monitor Storage Costs

```bash
# Enable storage class analysis
aws s3api put-bucket-analytics-configuration \
  --bucket my-demo-bucket-xxx \
  --id FullBucketAnalysis \
  --analytics-configuration file://storage-analysis.json

# Check bucket size by storage class
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=my-demo-bucket-xxx \
               Name=StorageType,Value=StandardStorage \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 86400 \
  --statistics Average
```

## Part 7 — Clean Up

```bash
# Empty bucket (delete all objects)
aws s3 rm s3://my-demo-bucket-xxx --recursive

# Delete bucket
aws s3api delete-bucket --bucket my-demo-bucket-xxx

# If using replication, clean up IAM role
aws iam detach-role-policy \
  --role-name s3-replication-role \
  --policy-arn arn:aws:iam::123456789012:policy/replication-policy

aws iam delete-role --role-name s3-replication-role
```

## Key Concepts

| Feature | Purpose | When to Use |
|---------|---------|-------------|
| **Single Region** | Low latency in one location | Regional apps |
| **Multi-Region** | Disaster recovery, global access | Critical data |
| **Storage Classes** | Cost optimization | Based on access frequency |
| **Lifecycle** | Automatic transitions | Predictable access patterns |
| **Versioning** | Keep object history | Compliance, protection |
| **Replication** | Copy across regions | DR, compliance |

## Cost Optimization Tips

1. **Use INTELLIGENT_TIERING** for unknown access patterns
2. **Set lifecycle policies** to auto-transition old data
3. **Delete incomplete uploads** to avoid charges
4. **Use GLACIER** for archives (but remember retrieval costs)
5. **Monitor with CloudWatch** and S3 Storage Lens

## What You Learned

- Create buckets in single/multiple regions
- Upload objects with appropriate storage classes
- Implement lifecycle policies for automatic transitions
- Set up cross-region replication for DR
- Tag objects for cost allocation
- Monitor and optimize storage costs