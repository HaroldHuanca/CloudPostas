import json
import random
import time
from google.cloud import pubsub_v1

PROJECT_ID = "monitor-postas-minsa"
TOPIC_ID = "topico-postas-datos"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Definición base de las postas rurales
POSTAS = [
    {"name": "Posta Cusco-Ocongate", "region": "Cusco", "capacidad": 30, "camas": 10},
    {"name": "Posta Cusco-Sicuani", "region": "Cusco", "capacidad": 40, "camas": 15},
    {"name": "Posta Loreto-Nauta", "region": "Amazonía", "capacidad": 25, "camas": 8},
    {"name": "Posta Ucayali-Purús", "region": "Amazonía", "capacidad": 20, "camas": 5}
]

# Inicialización de inventarios base locales para simular decrementos continuos
stocks_locales = {p["name"]: {"Paracetamol": 100, "Amoxicilina": 80, "Ibuprofeno": 120} for p in POSTAS}

print("⚡ Iniciando el simulador dinámico de Postas Médicas Rurales...")

try:
    while True:
        for p in POSTAS:
            name = p["name"]
            
            # 1. Simular consumo de medicamentos (Va bajando progresivamente)
            for med in stocks_locales[name]:
                decremento = random.randint(0, 4)
                stocks_locales[name][med] = max(0, stocks_locales[name][med] - decremento)
                # Reabastecimiento aleatorio para simular logística cloud
                if stocks_locales[name][med] <= 5:
                    stocks_locales[name][med] += random.randint(50, 100)
            
            # 2. Provocar picos de pacientes aleatorios para forzar alertas visuales
            forzar_colapso = random.random() < 0.15 # 15% de probabilidad de estrés crítico
            
            if forzar_colapso:
                pacientes_espera = random.randint(int(p["capacidad"] * 0.9), p["capacidad"] + 5)
                medicos = random.randint(0, 1)  # Detona la alerta de colapso
                camas_ocupadas = p["camas"]
            else:
                pacientes_espera = random.randint(5, int(p["capacidad"] * 0.6))
                medicos = random.randint(2, 4)
                camas_ocupadas = random.randint(1, p["camas"] - 2)
                
            atendidos_ahora = random.randint(1, 5)
            
            payload = {
                "posta": name,
                "region": p["region"],
                "pacientes_espera": pacientes_espera,
                "atendidos_recientemente": atendidos_ahora,
                "camas_ocupadas": camas_ocupadas,
                "medicos_disponibles": medicos,
                "capacidad_maxima": p["capacidad"],
                "medicamentos": stocks_locales[name]
            }
            
            # Publicar mensaje a GCP Pub/Sub
            data_str = json.dumps(payload)
            future = publisher.publish(topic_path, data_str.encode('utf-8'))
            print(f"📦 [{p['region']}] Evento enviado -> {name} | Cola: {pacientes_espera} | Meds: {stocks_locales[name]['Paracetamol']} u.")
            
        time.sleep(3) # Envía ráfagas cada 3 segundos para dar dinamismo a las líneas de Grafana

except KeyboardInterrupt:
    print("\n🛑 Simulador detenido correctamente.")
