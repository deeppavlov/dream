###Конфигурируем aws
```shell script
aws configure

AKIAT2RXIFYZLDB66LZ3
WP1ShlTqOyKJ7d2qoZn2cJCouyhiJzCr/Ed9Sf43
us-east-1
```

###Логинимся в докере
(ключ сбрасывается через 12 часов)
```shell script
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 263182626354.dkr.ecr.us-east-1.amazonaws.com
```

###Создаём репозиторий для образа
```shell script
aws ecr create-repository --repository-name greeting_skill
```

Или создаём сразу все образы (за исключением mongo):
```shell script
for service in $(docker-compose -f docker-compose.yml -f dev.yml ps --services | grep -wv -e mongo)
do
  aws ecr create-repository --repository-name $service
done
```

###Билдим все образы
```shell script
VERSION=latest ENV_FILE=.env.staging DP_AGENT_PORT=4242 DOCKER_REGISTRY=263182626354.dkr.ecr.us-east-1.amazonaws.com docker-compose -f docker-compose.yml -f dev.yml -f staging.yml build
```

###Пушим образы:
```shell script
VERSION=latest ENV_FILE=.env.staging DP_AGENT_PORT=4242 DOCKER_REGISTRY=263182626354.dkr.ecr.us-east-1.amazonaws.com docker-compose -f docker-compose.yml -f staging.yml push
```

###Создаем кластер
```shell script
eksctl create cluster -f kubernetes/eks/<environment>/cluster.yaml
```

###Проверяем есть ли в списке нужный кластер
```shell script
aws eks list-clusters
```

###Обновляем kubeconfig для доступа к кластеру через kubectl
```shell script
aws eks update-kubeconfig --name {{cluster_name}}
```

###Добавление пользователя в auth config-map
```bash
kubectl get cm -n kube-system aws-auth -o yaml > aws-auth.yaml
```

###Создать namespaces
```bash
kubectl apply -f kubernetes/eks/<cluster>/namespace.yaml
```

###ebs-csi-driver (works only for readwriteone mode)
```bash
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update
helm upgrade --install aws-ebs-csi-driver \
    --namespace kube-system \
    --set enableVolumeScheduling=true \
    --set enableVolumeResizing=true \
    --set enableVolumeSnapshot=true \
    aws-ebs-csi-driver/aws-ebs-csi-driver
```

###efs-csi-driver
```bash
helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver/
helm repo update
helm upgrade -i aws-efs-csi-driver aws-efs-csi-driver/aws-efs-csi-driver \
    --namespace kube-system \
    --set image.repository=602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efs-csi-driver \
    --set serviceAccount.controller.create=false \
    --set serviceAccount.controller.name=efs-csi-controller-sa
```

###Create efs filesystem
```bash
vpc_id=$(aws eks describe-cluster \
    --name <cluster> \
    --query "cluster.resourcesVpcConfig.vpcId" \
    --output text)

cidr_range=$(aws ec2 describe-vpcs \
    --vpc-ids $vpc_id \
    --query "Vpcs[].CidrBlock" \
    --output text)

security_group_id=$(aws ec2 create-security-group \
    --group-name EfsSecurityGroup \
    --description "efs security group" \
    --vpc-id $vpc_id \
    --output text)

aws ec2 authorize-security-group-ingress \
    --group-id $security_group_id \
    --protocol tcp \
    --port 2049 \
    --cidr $cidr_range

file_system_id=$(aws efs create-file-system \
    --region us-west-2 \
    --performance-mode generalPurpose \
    --query 'FileSystemId' \
    --tags 'Name: dp' \
    --output text)

aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$vpc_id" \
    --query 'Subnets[*].{SubnetId: SubnetId,AvailabilityZone: AvailabilityZone,CidrBlock: CidrBlock}' \
    --output table

---------------------------------------------------------------------
|                          DescribeSubnets                          |
+------------------+-------------------+----------------------------+
| AvailabilityZone |     CidrBlock     |         SubnetId           |
+------------------+-------------------+----------------------------+
|  us-west-2b      |  192.168.96.0/19  |  subnet-00822cb3201bbb4a1  |
|  us-west-2b      |  192.168.32.0/19  |  subnet-071ff1b4accbddac6  |
|  us-west-2a      |  192.168.64.0/19  |  subnet-0ab890f0f35e3f572  |
|  us-west-2a      |  192.168.0.0/19   |  subnet-03d01cb11748b2670  |
+------------------+-------------------+----------------------------+

aws efs create-mount-target \
    --file-system-id $file_system_id \
    --subnet-id subnet-071ff1b4accbddac6 \
    --security-groups $security_group_id

aws efs create-mount-target \
    --file-system-id $file_system_id \
    --subnet-id subnet-03d01cb11748b2670 \
    --security-groups $security_group_id
```

###Создать pv
```bash
kubectl apply -f kubernetes/eks/<cluster>/pv.yaml
```

###Установка nginx
```shell script
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx ingress-nginx/ingress-nginx
```

---

###Обновление переменных окружения
```shell script
kubectl delete configmap env -n alexa
kubectl create configmap env -n alexa --from-env-file .env.dev
```

###Генерация деплоймент файлов
```shell script
export DOCKER_REGISTRY=<registry-address>
python3 kubernetes/kuber_generator.py
```

###Деплой в кубер
```shell script
for dir in kubernetes/models/*; do k apply -f $dir; done
```

###Обновление сервисов
```shell script
for file in kubernetes/models/*/*-lb.yaml; do k apply -f $file; done
```

###Сервисы для видеокарт
```shell script
helm repo add nvgfd https://nvidia.github.io/gpu-feature-discovery
helm install nvgfd nvgfd/gpu-feature-discovery

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm install nvdp nvdp/nvidia-device-plugin

helm repo add gpu-helm-charts \
   https://nvidia.github.io/gpu-monitoring-tools/helm-charts

kubectl apply -f https://raw.githubusercontent.com/prometheus-community/helm-charts/main/charts/kube-prometheus-stack/crds/crd-servicemonitors.yaml

helm upgrade -i dcgm-exporter gpu-helm-charts/dcgm-exporter -f kubernetes/helm-charts/dcgm-exporter/values.yaml

```

###Mongodb
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```
- prod:
  `helm upgrade -i -n default mongo bitnami/mongodb -f kubernetes/helm-charts/mongodb/values-prod.yaml`
- dev:
  `helm upgrade -i -n alexa mongodb bitnami/mongodb -f kubernetes/helm-charts/mongodb/values-dev.yaml`

###Kubernetes-dashboard
```console
# Add kubernetes-dashboard repository
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
# Deploy a Helm Release named "kubernetes-dashboard" using the kubernetes-dashboard chart
helm upgrade -i kubernetes-dashboard/kubernetes-dashboard --name kubernetes-dashboard -n monitoring -f kubernetes/helm-charts/kubernetes-dashboard/values.yaml
```

###Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade -i prometheus prometheus-community/prometheus -n monitoring -f kubernetes/helm-charts/prometheus/values.yaml
```

###Grafana
```console
helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade -i grafana grafana/grafana -n monitoring -f kubernetes/helm-charts/grafana/values.yaml
```

###Loki
```console
helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade -i loki grafana/loki -n monitoring -f kubernetes/helm-charts/loki/values.yaml
```

###Metric API
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
