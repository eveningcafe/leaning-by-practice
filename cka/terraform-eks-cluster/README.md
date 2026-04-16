# Minimal EKS Cluster for Learning

A cost-optimized EKS cluster setup designed for students and CKA practice. Uses the same VPC/network as the EC2-based K8s setup but with managed EKS.

## Cost Comparison

| Setup | Control Plane | Worker Nodes | Total Monthly |
|-------|--------------|--------------|---------------|
| **EC2 K8s** (previous) | t3.medium (~$30) | t3.medium (~$30) | **~$60** |
| **This EKS** (with spot) | EKS ($73) | t3.small spot (~$5.50) | **~$78.50** |
| **This EKS** (on-demand) | EKS ($73) | t3.small (~$18.40) | **~$91.40** |

For just $18.50 more than EC2, you get:
- Managed control plane (no etcd headaches)
- High availability across AZs
- Automatic updates and patches
- AWS integrations (IAM, ALB, EBS)
- Production-grade reliability

## Quick Start

### Prerequisites

1. AWS CLI configured:
```bash
aws configure
```

2. kubectl installed:
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

3. eksctl (optional but recommended):
```bash
# macOS
brew install eksctl

# Linux
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

### Deploy the Cluster

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Create the cluster (takes ~10-15 minutes)
terraform apply

# Configure kubectl
aws eks update-kubeconfig --region ap-southeast-1 --name devops-class-eks

# Verify connection
kubectl get nodes
```

### Test the Cluster

```bash
# Deploy a test application
kubectl create deployment nginx --image=nginx --replicas=2
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Check the pods
kubectl get pods
kubectl get svc nginx

# Get the LoadBalancer URL (wait 2-3 minutes)
kubectl get svc nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Cost Optimization

#### 1. Scale Down When Not Using
```bash
# Scale all deployments to 0
kubectl scale deployment --all --replicas=0 -n default

# Scale node group to 0 (saves ~$5.50-$18/month)
aws eks update-nodegroup-config \
  --cluster-name devops-class-eks \
  --nodegroup-name devops-class-eks-node-group \
  --scaling-config minSize=0,maxSize=0,desiredSize=0 \
  --region ap-southeast-1
```

#### 2. Scale Back Up When Needed
```bash
# Scale node group back to 1
aws eks update-nodegroup-config \
  --cluster-name devops-class-eks \
  --nodegroup-name devops-class-eks-node-group \
  --scaling-config minSize=1,maxSize=2,desiredSize=1 \
  --region ap-southeast-1

# Scale deployments back up
kubectl scale deployment nginx --replicas=2
```

#### 3. Destroy When Done (IMPORTANT!)
```bash
# Delete all K8s resources first
kubectl delete all --all -n default

# Destroy the infrastructure
terraform destroy
```

## Configuration Options

Edit `variables.tf` to customize:

```hcl
# Use cheaper t3.micro (not recommended - only 1GB RAM)
node_instance_type = "t3.micro"

# Use on-demand instead of spot (more stable but 3x cost)
use_spot_instances = false

# Add more nodes (increases cost)
desired_nodes = 2
max_nodes = 3
```

## Architecture

```
Internet
    │
    ├── EKS Control Plane (Managed by AWS)
    │   ├── API Server
    │   ├── etcd
    │   ├── Controller Manager
    │   └── Scheduler
    │
    └── Node Group (Your Worker Nodes)
        └── t3.small (2 vCPU, 2GB RAM)
            ├── kubelet
            ├── kube-proxy
            └── Your pods
```

## What's Included

- **EKS Cluster**: Kubernetes 1.29
- **Node Group**: 1x t3.small with Spot pricing
- **Networking**: Uses existing VPC from EC2 setup
- **IAM Roles**: Properly configured for EKS
- **OIDC Provider**: For IAM Roles for Service Accounts (IRSA)
- **Security Groups**: Minimal required ports open

## Common Issues

### Issue: Nodes not joining cluster
```bash
# Check node group status
aws eks describe-nodegroup \
  --cluster-name devops-class-eks \
  --nodegroup-name devops-class-eks-node-group \
  --region ap-southeast-1
```

### Issue: Can't connect with kubectl
```bash
# Re-configure kubeconfig
aws eks update-kubeconfig --region ap-southeast-1 --name devops-class-eks --alias devops-eks

# Check current context
kubectl config current-context
```

### Issue: Spot instance interrupted
- This is expected with spot instances
- Pods will be rescheduled when new node comes up
- Use on-demand for stability: `use_spot_instances = false`

## Monitoring Costs

```bash
# Check current costs in AWS Console
# Cost Explorer > Filter by Service: EKS, EC2

# Or use AWS CLI
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://cost-filter.json
```

## Learning Resources

- [EKS Workshop](https://www.eksworkshop.com/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [CKA Exam Prep](https://github.com/cncf/curriculum)

## Important Notes

1. **This is for LEARNING only** - not production ready
2. **Spot instances can be interrupted** - your pods will restart
3. **Single AZ setup** - no high availability
4. **Minimal resources** - t3.small has only 2GB RAM
5. **ALWAYS destroy when done** to avoid charges

## Next Steps

After cluster is running:
1. Install metrics server for `kubectl top`
2. Deploy sample applications
3. Practice CKA scenarios
4. Experiment with different workloads
5. **Remember to destroy everything when done!**

---

**WARNING**: This creates real AWS resources that cost money. Always run `terraform destroy` when you're done practicing!