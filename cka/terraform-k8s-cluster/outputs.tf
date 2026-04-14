output "controller_public_ip" {
  description = "Public IP of Kubernetes controller node"
  value       = aws_instance.k8s_controller.public_ip
}

output "controller_private_ip" {
  description = "Private IP of Kubernetes controller node"
  value       = aws_instance.k8s_controller.private_ip
}

output "worker_public_ip" {
  description = "Public IP of Kubernetes worker node"
  value       = aws_instance.k8s_worker.public_ip
}

output "worker_private_ip" {
  description = "Private IP of Kubernetes worker node"
  value       = aws_instance.k8s_worker.private_ip
}

output "ssh_command_controller" {
  description = "SSH command to connect to controller node"
  value       = "ssh -i ${var.ssh_public_key_path} ubuntu@${aws_instance.k8s_controller.public_ip}"
}

output "ssh_command_worker" {
  description = "SSH command to connect to worker node"
  value       = "ssh -i ${var.ssh_public_key_path} ubuntu@${aws_instance.k8s_worker.public_ip}"
}

output "kubeadm_init_command" {
  description = "Command to initialize Kubernetes cluster on controller"
  value       = "sudo kubeadm init --apiserver-advertise-address=${aws_instance.k8s_controller.private_ip} --pod-network-cidr=10.244.0.0/16"
}

output "security_group_id" {
  description = "Security group ID for the cluster"
  value       = aws_security_group.k8s_cluster_sg.id
}