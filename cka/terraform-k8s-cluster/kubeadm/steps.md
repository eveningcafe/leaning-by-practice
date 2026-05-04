# Kubeadm Install Steps (Ubuntu 22.04, containerd, K8s 1.35)
# Run on ALL nodes unless marked [controller] or [worker]
#
# controller: ubuntu@54.255.211.67  (private: 172.31.95.70)
# worker:     ubuntu@54.169.186.251 (private: 172.31.86.170)
# ssh:        ssh -i ~/.ssh/id_rsa ubuntu@<ip>

## 1. Kernel modules
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

## 2. Sysctl
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

## 3. Disable swap
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab
```

## 4. Install containerd
```bash
sudo apt-get update
sudo apt-get install -y containerd

sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd
```

## 5. Install kubeadm, kubelet, kubectl
```bash
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable kubelet
```

## 6. [controller] Init cluster
```bash
sudo kubeadm init \
  --apiserver-advertise-address=172.31.95.70 \
  --pod-network-cidr=192.168.0.0/16

mkdir -p $HOME/.kube
sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

## 7. [controller] Install CNI — Calico
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml

# Wait for calico pods to be ready
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=120s
```

## 8. [controller] Get join command
```bash
kubeadm token create --print-join-command
```

## 9. [worker] Join cluster
```bash
# paste output from step 8
sudo kubeadm join 172.31.95.70:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

## 10. [controller] Verify
```bash
kubectl get nodes
kubectl get pods -A
```
