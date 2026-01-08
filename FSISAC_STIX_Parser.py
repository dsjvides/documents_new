#!/usr/bin/env python3

import sys
import json
import re
import collections
from urllib.parse import urlparse
import iocextract
from stix.core import STIXPackage


class FSISAC_STIX_Parser:

    def extract_observable(self, obs, values):
        typ = obs["properties"].get("xsi:type")
        val = None

        if typ == "AddressObjectType":
            address_value = obs["properties"].get("address_value")
            if isinstance(address_value, str):
                val = address_value
            elif isinstance(address_value, dict):
                val = address_value.get("value")

        elif typ in ("URIObjectType", "DomainNameObjectType", "HostnameObjectType"):
            value = obs["properties"].get("value")
            if isinstance(value, dict):
                val = value.get("value")
            else:
                val = value

        elif typ == "UserAccountObjectType":
            val = obs["properties"].get("username")

        elif typ == "FileObjectType":
            hashes = obs["properties"].get("hashes", [])
            if hashes:
                hash_val = hashes[0].get("simple_hash_value")
                if isinstance(hash_val, dict):
                    val = hash_val.get("value")
                else:
                    val = hash_val

        if val:
            if isinstance(val, collections.abc.Iterable) and not isinstance(val, str):
                values.extend(val)
            else:
                values.append(val)

    def extract_observables(self, indicators):
        values = []

        for indicator in indicators:
            obs = indicator.get("observable", indicator)

            if "observable" in indicator:
                idref = indicator["observable"].get("idref", "")
                if "fsisac" in idref.lower() or "nccic" in idref.lower():
                    title = indicator.get("title", "")
                    description = indicator.get("description", "")
                    return "type1", self.parse_from_description(description, title)

            if "object" in obs:
                self.extract_observable(obs["object"], values)

            elif "observable_composition" in obs:
                for o in obs["observable_composition"].get("observables", []):
                    if "object" in o:
                        self.extract_observable(o["object"], values)

        return "other", values

    def process_stix_dict(self, stix_dict):
        iocs = {
            "title": "",
            "domain": [],
            "ip": [],
            "email": [],
            "hash": [],
            "url": [],
            "yara": [],
            "other": []
        }

        results = []

        if "observables" in stix_dict:
            results = self.extract_observables(stix_dict["observables"]["observables"])

        if "indicators" in stix_dict:
            results = self.extract_observables(stix_dict["indicators"])

        stix_type, values = results

        if stix_type == "type1":
            return values

        for item in values:
            if re.match(r"^https?://", item):
                iocs["url"].append(urlparse(item).netloc)
            elif re.match(r"[^@]+@[^@]+\.[^@]+", item):
                iocs["email"].append(item)
            elif re.match(r"\b\d{1,3}(\.\d{1,3}){3}\b", item):
                iocs["ip"].append(item)
            elif re.match(r"^[a-fA-F0-9]{32,64}$", item):
                iocs["hash"].append(item)
            else:
                iocs["other"].append(item)

        for key in iocs:
            if isinstance(iocs[key], list):
                iocs[key] = list(set(iocs[key]))

        return iocs

    def parse_from_description(self, description, title):
        iocs = {
            "title": title,
            "domain": [],
            "ip": [],
            "email": [],
            "hash": [],
            "url": [],
            "yara": [],
            "other": []
        }

        description = description.replace("[.]", ".").replace("hxxp", "http").replace("[@]", "@")

        for url in iocextract.extract_urls(description, refang=True):
            iocs["url"].append(url)

        for ip in iocextract.extract_ips(description, refang=True):
            iocs["ip"].append(ip)

        for email in iocextract.extract_emails(description):
            iocs["email"].append(email)

        for h in iocextract.extract_hashes(description):
            iocs["hash"].append(h)

        for y in iocextract.extract_yara_rules(description):
            iocs["yara"].append(y)

        for key in iocs:
            if isinstance(iocs[key], list):
                iocs[key] = list(set(iocs[key]))

        return iocs

    def convert_to_json(self, iocs):
        title = iocs.get("title", "")
        output = []

        for k, values in iocs.items():
            if k == "title":
                continue
            for v in values:
                output.append({
                    "title": title,
                    "type": k,
                    "value": v
                })

        return json.dumps({"IOCS": output})

    def parse_stix_file(self, filename):
        stix_package = STIXPackage.from_xml(filename)
        iocs = self.process_stix_dict(stix_package.to_dict())
        return self.convert_to_json(iocs)
