import requests
import json
import logging
import logging.handlers
from datetime import datetime

# Configuración de TAXII
TAXII_API = "https://taxii.fsisac.com/ctixapi/ctix2/"
USERNAME = "tu_usuario"
PASSWORD = "tu_contraseña"

# Versión STIX/TAXII (elige "2.0" o "2.1")
TAXII_VERSION = "2.1"

# Configuración de Syslog
SYSLOG_SERVER = "10.13.39.16"
SYSLOG_PORT = 514

# Configuración de archivo de backup
BACKUP_FILE = "/opt/taxii_backup.log"

def load_collections(file_path="collections.json"):
    """
    Carga la lista de collections desde un archivo JSON.
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    return data.get("collections", [])

def get_taxii_indicators(collection_id):
    """
    Realiza la petición al servidor TAXII y obtiene los objetos STIX de la colección.
    """
    headers = {"Accept": f"application/vnd.oasis.stix+json;version={TAXII_VERSION}"}
    url = f"{TAXII_API}collections/{collection_id}/objects/"
    response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, verify=True)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error en la colección {collection_id}: {response.status_code} - {response.text}")

def send_syslog(message):
    """
    Envía un mensaje JSON al servidor Syslog.
    """
    logger = logging.getLogger("TAXII")
    logger.setLevel(logging.INFO)
    handler = logging.handlers.SysLogHandler(address=(SYSLOG_SERVER, SYSLOG_PORT))
    logger.addHandler(handler)
    logger.info(message)

def backup_to_file(collection_id, data):
    """
    Guarda los indicadores en un archivo .log como respaldo.
    """
    with open(BACKUP_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - Collection {collection_id} - {json.dumps(data)}\n")

def main():
    try:
        collections = load_collections()

        for collection_id in collections:
            print(f"Procesando colección: {collection_id}")
            indicators = get_taxii_indicators(collection_id)

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
            backup_to_file(collection_id, indicators_filtered)

        print("Todas las colecciones procesadas correctamente.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
