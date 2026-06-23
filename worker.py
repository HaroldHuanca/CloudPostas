from google.cloud import pubsub_v1
from prometheus_client import start_http_server, Gauge
import json
import time

# Definición de Métricas para Prometheus
PACIENTES_COLA = Gauge('posta_pacientes_en_espera', 'Pacientes en cola', ['posta', 'region'])
STOCK_MEDICAMENTO = Gauge('posta_stock_medicamento', 'Stock de medicamentos', ['posta', 'region'])
ALERTA_RIESGO = Gauge('posta_alerta_colapso', 'Riesgo de colapso inminente (1=Si, 0=No)', ['posta', 'region'])
TIEMPO_ESPERA_ESTIMADO = Gauge('posta_tiempo_espera_minutos', 'Tiempo de espera estimado', ['posta', 'region'])

project_id = "monitor-postas-minsa"
subscription_id = "sub-procesador-postas"

def callback(message):
    try:
        datos = json.loads(message.data.decode("utf-8"))
        posta = datos["infraestructura"]["nombre"]
        region = datos["infraestructura"]["ubicacion"]
        capacidad = datos["infraestructura"]["capacidad_maxima"]
        
        cola = datos["pacientes"]["en_espera"]
        medicos = datos["personal_salud"]["medicos_disponibles"]
        stock = datos["medicamentos"]["stock_actual"]
        
        # 1. Actualizar métricas base
        PACIENTES_COLA.labels(posta=posta, region=region).set(cola)
        STOCK_MEDICAMENTO.labels(posta=posta, region=region).set(stock)
        
        # 2. Calcular Indicadores (Ej: Tiempo de espera estimado)
        # Si no hay médicos el tiempo tiende a infinito, simulamos penalización alta
        factor_atencion = medicos if medicos > 0 else 0.1
        tiempo_espera = (cola * 15) / factor_atencion 
        TIEMPO_ESPERA_ESTIMADO.labels(posta=posta, region=region).set(tiempo_espera)
        
        # 3. Lógica de Alertas / Riesgo de Colapso
        sobrecarga = cola > capacidad
        falta_personal = medicos == 0
        
        if sobrecarga and falta_personal:
            ALERTA_RIESGO.labels(posta=posta, region=region).set(1) # RIESGO CRÍTICO
        else:
            ALERTA_RIESGO.labels(posta=posta, region=region).set(0)
            
        print(f"Procesado: {posta} | Cola: {cola} | Alerta Colapso: {1 if (sobrecarga and falta_personal) else 0}")
        message.ack()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

if __name__ == "__main__":
    # Iniciar el servidor de métricas de Prometheus en el puerto 8000
    start_http_server(8000)
    print("Servidor de métricas Prometheus escuchando en el puerto 8000")
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Escuchando mensajes en {subscription_path}...")
    
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
