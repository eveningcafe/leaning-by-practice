# CloudWatch Container Insights for the SRE-agent lab.
# The amazon-cloudwatch-observability addon deploys the CloudWatch agent +
# Fluent Bit as a DaemonSet, publishing pod/node metrics to the
# "ContainerInsights" namespace (used by the agent's query_metrics tool).
#
# The addon's pods authenticate with the NODE role, so it needs
# CloudWatchAgentServerPolicy attached there.

resource "aws_iam_role_policy_attachment" "node_cloudwatch_agent" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_eks_addon" "cloudwatch_observability" {
  cluster_name                = aws_eks_cluster.eks_cluster.name
  addon_name                  = "amazon-cloudwatch-observability"
  addon_version               = var.cloudwatch_observability_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [
    aws_eks_node_group.eks_nodes,
    aws_iam_role_policy_attachment.node_cloudwatch_agent,
  ]

  tags = var.tags
}

variable "cloudwatch_observability_version" {
  description = "Version of the amazon-cloudwatch-observability EKS addon"
  type        = string
  default     = "v6.3.0-eksbuild.1" # for k8s 1.35
}
