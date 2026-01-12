#!/usr/bin/env python3

import json
import socket
import requests
from taxii2client.v20 import Server

# ===== FS-ISAC TAXII CONFIG =====
TAXII_SERVER = "https://taxii.fsisac.com"
API_ROOT = "https://taxii.fsisac.com/ctixapi/ctix2/"
COLLECTION_ID = "3e941cc9-8d9e-4f06-a995-b170579afd91"

USERNAME = "0aa84b5f-27ab-40af-8783-ee9afb1448e8"
PASSWORD = "e418faa7-9336-4c28-96af-80a99af9858c"

# ===== SYSLOG CONFIG =====
SYSLOG_SERVER = "10.13.39.17"
SYSLOG_PORT = 514

# ==============================

def send_syslog(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (SYSLOG_SERVER, SYSLOG_PORT))
    sock.close()

def main():
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    session.verify = True

    server = Server(TAXII_SERVER, session=session)
    api_root = server.api_roots[API_ROOT]
    collection = api_root.collections.get(COLLECTION_ID)

    stix_bundle = collection.get_objects()
    objects = stix_bundle.get("objects", [])

    for obj in objects:
        send_syslog(json.dumps(obj))

if __name__ == "__main__":
    main()
