#!/usr/bin/env python3

import os
import json
import random
import datetime
from configobj import ConfigObj
from taxii2client.v21 import Server

config = ConfigObj("fsisac.conf")

FSISAC_USERNAME = config["FSISAC_USERNAME"]
FSISAC_PASSWORD = config["FSISAC_PASSWORD"]
FSISAC_TAXII_SERVER = config["FSISAC_TAXII_SERVER"]
FSISAC_API_ROOT = config["FSISAC_API_ROOT"]
FSISAC_COLLECTION_ID = config["FSISAC_COLLECTION_ID"]
STIX_DOWNLOADED_PATH = config["FSISAC_STIX_DOWNLOADED_PATH"]
FSISAC_JSON_OUTPUT_PATH = config["FSISAC_JSON_OUTPUT_PATH"]

os.makedirs(STIX_DOWNLOADED_PATH, exist_ok=True)
os.makedirs(FSISAC_JSON_OUTPUT_PATH, exist_ok=True)

class FSISAC_STIX_Downloader:

    def download_stix(self):
        server = Server(
            FSISAC_TAXII_SERVER + FSISAC_API_ROOT,
            user=FSISAC_USERNAME,
            password=FSISAC_PASSWORD
        )

        api_root = server.api_roots[0]
        collection = api_root.collections.get(FSISAC_COLLECTION_ID)

        response = collection.get_objects()
        objects = response.get("objects", [])

        if not objects:
            print("No indicators received")
            return

        ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        out_file = f"fsisac_stix_{ts}_{random.randint(1000,9999)}.json"
        out_path = os.path.join(STIX_DOWNLOADED_PATH, out_file)

        with open(out_path, "w") as f:
            json.dump(objects, f)

        print(f"Downloaded {len(objects)} indicators")

    def extract_urls(self):
        files = [f for f in os.listdir(STIX_DOWNLOADED_PATH) if f.endswith(".json")]

        for file in files:
            full_path = os.path.join(STIX_DOWNLOADED_PATH, file)
            with open(full_path, "r") as f:
                data = json.load(f)

            urls = []
            for obj in data:
                if obj.get("type") == "indicator":
                    pattern = obj.get("pattern", "")
                    if "url:value" in pattern:
                        urls.append({
                            "id": obj.get("id"),
                            "pattern": pattern,
                            "confidence": obj.get("confidence"),
                            "valid_from": obj.get("valid_from")
                        })

            if urls:
                out = os.path.join(
                    FSISAC_JSON_OUTPUT_PATH,
                    f"urls_{file.replace('.json','')}.json"
                )
                with open(out, "w") as o:
                    json.dump(urls, o)

                print(f"Extracted {len(urls)} URLs from {file}")

if __name__ == "__main__":
    d = FSISAC_STIX_Downloader()
    d.download_stix()
    d.extract_urls()
