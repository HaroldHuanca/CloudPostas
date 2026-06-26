# 1. Matamos los procesos en segundo plano
pkill -f "simulador.py"
pkill -f "port-forward"

echo "⏱️ Apagando Minikube de forma segura (esperando a que termine)..."
# 2. El comando corre normal, pero agregamos un indicador visual
minikube stop

# 💡 EL CAMBIO CLAVE: Esperar 5 segundos extra para que Docker libere los contenedores limpios
echo "⏱️ Asegurando el cierre de contenedores..."
sleep 5

echo "🛑 Deteniendo el motor de Docker..."
# 3. Ahora sí, apagamos Docker con seguridad
sudo systemctl stop docker.service docker.socket

echo "=== ¡Laptop liberada limpiamente al 100%! ==="
