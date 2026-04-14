terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider AWS
provider "aws" {
  region = "ap-southeast-1" # Thay đổi region nếu cần
}

# Định nghĩa biến cục bộ để lưu tên key đã có sẵn
locals {
  ssh_key_name = "hoanq3" # <<== Đổi tên key của bạn tại đây
}


# Tạo một security group để cho phép SSH
resource "aws_security_group" "instance_sg" {
  name        = "instance_sg_amazon_linux-demo1"
  description = "Allow SSH inbound traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Tạo EC2 instance t2.micro
resource "aws_instance" "tvtien_instance" {
  ami           = "ami-03bec25d3c8e6cd26"
  instance_type = "t2.micro"
  key_name      = local.ssh_key_name
  security_groups = [aws_security_group.instance_sg.name]

  tags = {
    Name = "tvtien-instance-demo1"
  }
}

# Xuất public IP của instance
output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.tvtien_instance.public_ip
}
