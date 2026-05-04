# Kubespray Setup

Kubespray installs Kubernetes on the EC2 nodes provisioned by Terraform.
The inventory here points to the devops-class nodes — update the IPs after each `terraform apply`.

## Steps

### 1. Get node IPs from Terraform
```bash
cd ..
terraform output
```

### 2. Update hosts.ini with the IPs
Edit `hosts.ini` and replace `ansible_host` and `ip` for controller and worker.

### 3. Clone Kubespray
```bash
git clone https://github.com/kubernetes-sigs/kubespray
cd kubespray
pip install -r requirements.txt --user
```

### 4. Run the playbook
```bash
ansible-playbook -i ../kubespray-inventory/hosts.ini cluster.yml -b
```

This takes ~15–20 minutes. Kubespray installs containerd + Calico CNI by default.

### 5. Get kubeconfig
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<controller-ip> "cat ~/.kube/config"
```

Save it to `~/.kube/config` on your local machine to use `kubectl` locally.

## Verify installation

SSH into the controller, then run:

```bash
# All nodes should be Ready
kubectl get nodes -o wide

# All pods should be Running
kubectl get pods -A

# Check Calico is up
kubectl get pods -n kube-system -l k8s-app=calico-node

# Check component health
kubectl get componentstatuses

# Check cluster info
kubectl cluster-info
```

## Check control plane components

```bash
# etcd (systemd service)
systemctl status etcd

# kube-apiserver (static pod)
sudo crictl logs $(sudo crictl ps -q --name kube-apiserver)

# kube-scheduler (static pod)
sudo crictl logs $(sudo crictl ps -q --name kube-scheduler)
```
