import json
import os
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from prometheus_client import start_http_server, Counter, Gauge

# 1. DEFINICIÓN DE MÉTRICAS AVANZADAS PARA PROMETHEUS
# Lógica de flujo (Líneas dinámicas)
PACIENTES_ATENDIDOS = Counter('posta_pacientes_atendidos_total', 'Pacientes atendidos acumulados', ['posta', 'region'])
PACIENTES_ESPERA = Gauge('posta_pacientes_en_espera', 'Pacientes actuales en cola', ['posta', 'region'])
CAMAS_OCUPADAS = Gauge('posta_camas_ocupadas', 'Camas ocupadas en el establecimiento', ['posta', 'region'])

# Tiempos e Inventario (Gauges, Rangos y Predicciones)
TIEMPO_ESPERA = Gauge('posta_tiempo_espera_minutos', 'Tiempo de espera estimado en minutos', ['posta', 'region'])
STOCK_MEDICAMENTO = Gauge('posta_medicamento_stock_unidades', 'Unidades de medicamento en almacén', ['posta', 'region', 'medicamento'])

# Alertas Críticas e Indicadores de Colapso (Mapeos y Stats)
ALERTA_COLAPSO = Gauge('posta_alerta_colapso', 'Indicador de riesgo de colapso inminente (0 o 1)', ['posta', 'region'])

# 2. CONFIGURACIÓN DE GCP PUB/SUB
PROJECT_ID = "monitor-postas-minsa"  # Asegúrate de que coincida con tu consola de GCP
SUBSCRIPTION_ID = "sub-procesador-postas"    # Tu suscripción de Pub/Sub

def callback(message):
    try:
        data = json.loads(message.data.decode('utf-8'))
        posta = data['posta']
        region = data['region']
        
        print(f"[{region}] Procesando datos de: {posta}")
        
        # Inyectar datos en las métricas de Prometheus
        PACIENTES_ESPERA.labels(posta=posta, region=region).set(data['pacientes_espera'])
        CAMAS_OCUPADAS.labels(posta=posta, region=region).set(data['camas_ocupadas'])
        
        # Incrementar el contador de atendidos simulando la tasa
        PACIENTES_ATENDIDOS.labels(posta=posta, region=region).inc(data['atendidos_recientemente'])
        
        # Calcular tiempo de espera dinámico
        tiempo_estimado = data['pacientes_espera'] * 15
        TIEMPO_ESPERA.labels(posta=posta, region=region).set(tiempo_estimado)
        
        # Registrar stock por cada medicamento enviado en el diccionario
        for med, stock in data['medicamentos'].items():
            STOCK_MEDICAMENTO.labels(posta=posta, region=region, medicamento=med).set(stock)
            
        # Lógica de Alerta de Colapso (Gauges de control)
        # Si la cola supera el 90% de la capacidad y hay pocos médicos
        if (data['pacientes_espera'] >= data['capacidad_maxima'] * 0.9) and (data['medicos_disponibles'] <= 1):
            ALERTA_COLAPSO.labels(posta=posta, region=region).set(1)
            print(f"🚨 ALERT: ¡{posta} en riesgo de colapso sanitario!")
        else:
            ALERTA_COLAPSO.labels(posta=posta, region=region).set(0)
            
        message.ack()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        message.nack()

if __name__ == "__main__":
    # Iniciar el servidor de métricas de Prometheus en el puerto 8000
    start_http_server(8000)
    print("🚀 Servidor de métricas Prometheus escuchando en el puerto 8000...")
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"📥 Escuchando mensajes en {subscription_path}...")
    
    with subscriber:
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.result()
