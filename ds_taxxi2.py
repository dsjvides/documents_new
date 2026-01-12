import requests
import json
import logging
import logging.handlers
from datetime import datetime

# Configuración de TAXII
TAXII_API = "https://taxii.fsisac.com/ctixapi/ctix2/"
USERNAME = "0aa84b5f-27ab-40af-8783-ee9afb1448e8"
PASSWORD = "e418faa7-9336-4c28-96af-80a99af9858c"
TAXII_VERSION = "2.1"

# Archivos
COLLECTIONS_FILE = "collections.json"
BACKUP_FILE = "/opt/taxii_backup.log"
ERROR_FILE = "/opt/taxii_errors.log"

# Syslog
SYSLOG_SERVER = "10.13.39.16"
SYSLOG_PORT = 514

def load_collections(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data.get("collections", [])

def get_taxii_indicators(collection_id):
    headers = {"Accept": f"application/vnd.oasis.stix+json;version={TAXII_VERSION}"}
    url = f"{TAXII_API}collections/{collection_id}/objects/"
    response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, verify=True)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error en la colección {collection_id}: {response.status_code} - {response.text}")

def send_syslog(message):
    logger = logging.getLogger("TAXII")
    logger.setLevel(logging.INFO)
    handler = logging.handlers.SysLogHandler(address=(SYSLOG_SERVER, SYSLOG_PORT))
    logger.addHandler(handler)
    logger.info(message)

def backup_to_file(collection_id, data):
    with open(BACKUP_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - Collection {collection_id} - {json.dumps(data)}\n")

def log_error(collection_id, error_message):
    with open(ERROR_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()} - Collection {collection_id} - ERROR: {error_message}\n")

def main():
    collections = load_collections(COLLECTIONS_FILE)

    for collection_id in collections:
        print(f"Procesando colección: {collection_id}")
        try:
            indicators = get_taxii_indicators(collection_id)

            # Filtrar solo objetos tipo "indicator"
            if "objects" in indicators:
                indicators_filtered = [obj for obj in indicators["objects"] if obj.get("type") == "indicator"]
            else:
                indicators_filtered = indicators

            indicators_json = json.dumps(indicators_filtered, indent=2)

            # Enviar por syslog
            send_syslog(indicators_json)

            # Guardar en backup
            backup_to_file(collection_id, indicators_filtered)

        except Exception as e:
            log_error(collection_id, str(e))
            print(f"Error en colección {collection_id}: {e}")

    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
