import time
import json
import random
from google.cloud import pubsub_v1

project_id = "monitor-postas-minsa"
topic_id = "topico-postas-datos"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

postas = [
    {"nombre": "Posta Cusco-Sicuani", "ubicacion": "Cusco", "capacidad_max": 40},
    {"nombre": "Posta Cusco-Ocongate", "ubicacion": "Cusco", "capacidad_max": 20},
    {"nombre": "Posta Loreto-Nauta", "ubicacion": "Amazonía", "capacidad_max": 30},
    {"nombre": "Posta Ucayali-Purús", "ubicacion": "Amazonía", "capacidad_max": 15}
]

print("Iniciando simulación de envío a Pub/Sub...")

while True:
    for posta in postas:
        # Simulación de fluctuación de datos
        en_espera = random.randint(5, 50)
        atendidos = random.randint(10, 30)
        medicos = random.randint(0, 3) # 0 significa falta de personal
        stock_paracetamol = random.randint(5, 100) # menos de 20 es crítico
        
        data = {
            "infraestructura": {
                "nombre": posta["nombre"],
                "ubicacion": posta["ubicacion"],
                "capacidad_maxima": posta["capacidad_max"]
            },
            "pacientes": {
                "en_espera": en_espera,
                "atendidos": atendidos,
                "total": en_espera + atendidos
            },
            "personal_salud": {
                "medicos_disponibles": medicos,
                "enfermeros": random.randint(1, 4)
            },
            "medicamentos": {
                "stock_actual": stock_paracetamol,
                "consumo_diario": random.randint(5, 15)
            }
        }
        
        payload = json.dumps(data).encode("utf-8")
        future = publisher.publish(topic_path, payload)
        print(f"Enviado datos de {posta['nombre']} - MsgID: {future.result()}")
        
    time.sleep(5) # Envía reportes cada 5 segundos
