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
VERSION=latest ENV_FILE=.env.dev DP_AGENT_PORT=4242 DOCKER_REGISTRY=263182626354.dkr.ecr.us-east-1.amazonaws.com docker-compose -f docker-compose.yml -f dev.yml -f staging.yml build
```

###Пушим образы:
```shell script
VERSION=latest ENV_FILE=.env.dev DP_AGENT_PORT=4242 DOCKER_REGISTRY=263182626354.dkr.ecr.us-east-1.amazonaws.com docker-compose -f docker-compose.yml -f staging.yml push
```

###Проверяем есть ли в списке нужный кластер
```shell script
aws eks list-clusters
```

###Обновляем kubeconfig для доступа к кластеру через kubectl
```shell script
aws eks update-kubeconfig --name {{cluster_name}}
```

###Обновление переменных окружения
```shell script
kubectl delete configmap env-dev -n alexa
kubectl create configmap env-dev -n alexa --from-env-file .env.dev
```

###Установка nginx
```shell script
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx ingress-nginx/ingress-nginx
```

###Генерация деплоймент файлов
```shell script
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
```
helm repo add nvgfd https://nvidia.github.io/gpu-feature-discovery
helm install nvgfd nvgfd/gpu-feature-discovery

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm install nvdp nvdp/nvidia-device-plugin

helm repo add gpu-helm-charts \
   https://nvidia.github.io/gpu-monitoring-tools/helm-charts

kubectl apply -f https://raw.githubusercontent.com/prometheus-community/helm-charts/main/charts/kube-prometheus-stack/crds/crd-servicemonitors.yaml

helm upgrade -i dcgm-exporter gpu-helm-charts/dcgm-exporter -f kubernetes/helm-charts/dcgm-exporter/values.yaml

```
