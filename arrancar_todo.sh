#!/bin/bash

echo "🚀 Iniciando la infraestructura básica..."
sudo systemctl start docker
minikube start
minikube addons enable registry

# 💡 EL CAMBIO CLAVE: Esperar a que los Pods estén estables antes de avanzar
echo "⏱️ Esperando a que los servicios del clúster estén listos..."
kubectl wait --namespace default --for=condition=Ready pods --all --timeout=30s

echo "📦 Aplicando configuraciones de Kubernetes..."
kubectl apply -f ~/CloudPostas/deployment.yaml
kubectl apply -f ~/CloudPostas/servicemonitor.yaml

echo "🔌 Abriendo los túneles en segundo plano..."
# Guardamos posibles errores en archivos .log en lugar de /dev/null para investigar
kubectl port-forward svc/prometheus-grafana 3000:80 >~/CloudPostas/grafana_tunnel.log 2>&1 &
kubectl port-forward --namespace kube-system service/registry 5000:80 >~/CloudPostas/registry_tunnel.log 2>&1 &

echo "⏱️ Esperando 5 segundos a que los túneles se estabilicen..."
sleep 5

echo "📊 Iniciando el Simulador..."
cd ~/CloudPostas/
source env/bin/activate
python simulador.py
