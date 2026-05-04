output "controller_public_ips" {
  description = "Public IPs of controller nodes"
  value       = aws_instance.k8s_controller[*].public_ip
}

output "controller_private_ips" {
  description = "Private IPs of controller nodes"
  value       = aws_instance.k8s_controller[*].private_ip
}

output "worker_public_ip" {
  description = "Public IP of worker node"
  value       = aws_instance.k8s_worker.public_ip
}

output "worker_private_ip" {
  description = "Private IP of worker node"
  value       = aws_instance.k8s_worker.private_ip
}

output "ssh_commands" {
  description = "SSH commands for all nodes"
  value = merge(
    { for i, ip in aws_instance.k8s_controller[*].public_ip :
      "controller-${i + 1}" => "ssh -i ~/.ssh/id_rsa ubuntu@${ip}"
    },
    { "worker" = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_instance.k8s_worker.public_ip}" }
  )
}

output "kubeadm_init_command" {
  description = "Run on controller-1 to init the cluster"
  value       = "sudo kubeadm init --apiserver-advertise-address=${aws_instance.k8s_controller[0].private_ip} --pod-network-cidr=192.168.0.0/16"
}

output "security_group_id" {
  value = aws_security_group.k8s_cluster_sg.id
}
