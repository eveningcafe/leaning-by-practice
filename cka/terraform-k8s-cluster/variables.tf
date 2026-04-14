variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-southeast-1"  # Singapore region
}

variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
  default     = "DEVOPS-CLASS-2601"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "VPC ID where instances will be created"
  type        = string
  default     = "vpc-036b914bdf14d227e"
}

variable "subnet_id" {
  description = "Subnet ID for instances"
  type        = string
  default     = "subnet-0c51b6b97f99b69ed"
}

variable "ubuntu_ami" {
  description = "Ubuntu 22.04 LTS AMI ID"
  type        = string
  default     = "ami-01811d4912b4ccb26"  # Ubuntu 22.04 LTS in ap-southeast-1 (Singapore)
}

variable "controller_instance_type" {
  description = "Instance type for Kubernetes controller node"
  type        = string
  default     = "t3.medium"  # 2 vCPU, 4 GB RAM - minimum for control plane
}

variable "worker_instance_type" {
  description = "Instance type for Kubernetes worker nodes"
  type        = string
  default     = "t3.medium"  # 2 vCPU, 4 GB RAM - good for worker nodes
}

variable "client_instance_type" {
  description = "Instance type for Kubernetes client node"
  type        = string
  default     = "t3.small"  # 2 vCPU, 2 GB RAM - sufficient for client
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_allowed_ips" {
  description = "List of IPs allowed to SSH into instances"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production
}

variable "kubernetes_version" {
  description = "Kubernetes version to install"
  type        = string
  default     = "1.29.0"
}