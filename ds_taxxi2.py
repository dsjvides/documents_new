import requests
import json
import logging
import logging.handlers
from datetime import datetime

# Configuración de TAXII
TAXII_API = "https://taxii.fsisac.com/ctixapi/ctix2/"
USERNAME = "0aa84b5f-27ab-40af-8783-ee9afb1448e8"
PASSWORD = "e418faa7-9336-4c28-96af-80a99af9858c"
COLLECTION_ID = "3e941cc9-8d9e-4f06-a995-b170579afd91"

# Versión STIX/TAXII (elige "2.0" o "2.1")
TAXII_VERSION = "2.1"

# Configuración de Syslog
SYSLOG_SERVER = "10.13.39.16"
SYSLOG_PORT = 514

# Configuración de archivo de backup
BACKUP_FILE = "/var/log/taxii_backup.log"

def get_taxii_indicators():
    """
    Realiza la petición al servidor TAXII y obtiene los objetos STIX de la colección.
    """
    if TAXII_VERSION == "2.0":
        headers = {"Accept": "application/vnd.oasis.stix+json;version=2.0"}
    else:
        headers = {"Accept": "application/vnd.oasis.stix+json;version=2.1"}

    url = f"{TAXII_API}collections/{COLLECTION_ID}/objects/"
    response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, verify=True)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error en la petición TAXII: {response.status_code} - {response.text}")

def send_syslog(message):
    """
    Envía un mensaje JSON al servidor Syslog.
    """
    logger = logging.getLogger("TAXII")
    logger.setLevel(logging.INFO)
    handler = logging.handlers.SysLogHandler(address=(SYSLOG_SERVER, SYSLOG_PORT))
    logger.addHandler(handler)
    logger.info(message)

def backup_to_file(data):
    """
    Guarda los indicadores en un archivo .log como respaldo.
    """
    with open(BACKUP_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {json.dumps(data)}\n")

def main():
    try:
        indicators = get_taxii_indicators()

        # Filtrar solo objetos tipo "indicator"
        if "objects" in indicators:
            indicators_filtered = [obj for obj in indicators["objects"] if obj.get("type") == "indicator"]
        else:
            indicators_filtered = indicators

        # Convertir a JSON string
        indicators_json = json.dumps(indicators_filtered, indent=2)

        # Enviar por syslog
        send_syslog(indicators_json)

        # Guardar en archivo de backup
        backup_to_file(indicators_filtered)

        print("Indicadores obtenidos, enviados por syslog y respaldados en archivo.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
