terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

# Security Group for Kubernetes Cluster
resource "aws_security_group" "k8s_cluster_sg" {
  name        = "${var.cluster_name}-sg"
  description = "Security group for Kubernetes cluster nodes"
  vpc_id      = var.vpc_id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips
  }

  # Kubernetes API server
  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # etcd server client API
  ingress {
    from_port   = 2379
    to_port     = 2380
    protocol    = "tcp"
    self        = true
  }

  # Kubelet API
  ingress {
    from_port   = 10250
    to_port     = 10250
    protocol    = "tcp"
    self        = true
  }

  # kube-scheduler
  ingress {
    from_port   = 10259
    to_port     = 10259
    protocol    = "tcp"
    self        = true
  }

  # kube-controller-manager
  ingress {
    from_port   = 10257
    to_port     = 10257
    protocol    = "tcp"
    self        = true
  }

  # NodePort Services
  ingress {
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Flannel VXLAN
  ingress {
    from_port   = 8472
    to_port     = 8472
    protocol    = "udp"
    self        = true
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-sg"
    Environment = var.environment
    Type        = "kubernetes"
  }
}

# Key Pair for SSH access
resource "aws_key_pair" "k8s_key" {
  key_name   = "${var.cluster_name}-key"
  public_key = file(var.ssh_public_key_path)

  tags = {
    Name        = "${var.cluster_name}-key"
    Environment = var.environment
  }
}

# Kubernetes Controller Node (Master)
resource "aws_instance" "k8s_controller" {
  ami           = var.ubuntu_ami
  instance_type = var.controller_instance_type
  key_name      = aws_key_pair.k8s_key.key_name
  
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.k8s_cluster_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    hostnamectl set-hostname DEVOPS-CLASS-2601-controller
  EOF

  tags = {
    Name        = "DEVOPS-CLASS-2601-controller"
    Environment = var.environment
    Type        = "kubernetes-controller"
    Role        = "master"
  }
}

# Kubernetes Worker Node
resource "aws_instance" "k8s_worker" {
  ami           = var.ubuntu_ami
  instance_type = var.worker_instance_type
  key_name      = aws_key_pair.k8s_key.key_name
  
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.k8s_cluster_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    hostnamectl set-hostname DEVOPS-CLASS-2601-worker
  EOF

  tags = {
    Name        = "DEVOPS-CLASS-2601-worker"
    Environment = var.environment
    Type        = "kubernetes-worker"
    Role        = "worker"
  }
}

