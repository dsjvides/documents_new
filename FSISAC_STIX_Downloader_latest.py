##!/usr/bin/env python3

import os
import json
import logging
from configobj import ConfigObj
from taxii2client.v21 import Server

config = ConfigObj("fsisac.conf")

FSISAC_TAXII_SERVER = config["FSISAC_TAXII_SERVER"]
FSISAC_API_ROOT = config["FSISAC_API_ROOT"]
FSISAC_COLLECTION_ID = config["FSISAC_COLLECTION_ID"]
FSISAC_USERNAME = config["FSISAC_USERNAME"]
FSISAC_PASSWORD = config["FSISAC_PASSWORD"]

STIX_OUTPUT_PATH = config.get("FSISAC_STIX_DOWNLOADED_PATH", "stix_files")

os.makedirs(STIX_OUTPUT_PATH, exist_ok=True)

logging.basicConfig(
    filename="fsisac_downloader.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def download_stix():
    logging.info("Starting FS-ISAC TAXII download")

    server = Server(
        FSISAC_TAXII_SERVER,
        user=FSISAC_USERNAME,
        password=FSISAC_PASSWORD,
        timeout=30
    )

    logging.info("Connecting to API Root")
    api_root = server.api_roots[FSISAC_API_ROOT]

    logging.info(f"Using collection {FSISAC_COLLECTION_ID}")
    collection = api_root.collections.get(FSISAC_COLLECTION_ID)

    try:
        objects = collection.get_objects()
        count = len(objects.get("objects", []))
        logging.info(f"Objects retrieved: {count}")
    except Exception as e:
        logging.error(f"Error retrieving objects: {e}")
        raise

    output_file = os.path.join(
        STIX_OUTPUT_PATH,
        "fsisac_stix_objects.json"
    )

    with open(output_file, "w") as f:
        json.dump(objects, f, indent=2)

    logging.info(f"STIX data written to {output_file}")

    with open("fsisac_objects.log", "a") as f:
        f.write(json.dumps(objects) + "\n")

    logging.info("Download finished successfully")


if __name__ == "__main__":
    try:
        download_stix()
        logging.info("Process completed")
    except Exception as e:
        logging.exception("Fatal error")
