#!/usr/bin/env python3

import json
import re
from datetime import datetime

# Chemins des fichiers
status_file = '/var/log/openvpn/status.log'
output_file = '/home/maxime/docker-apps/dashy/public/openvpn_logs.json'

# Fonction pour lire le fichier
def read_status_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read().strip().split('\n')
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {filepath}: {e}")
        return None

# Fonction pour extraire les informations
def parse_openvpn_status(lines):
    result = {
        "updated": "",
        "clients": []
    }
    
    client_info = {}
    routing_info = []
    global_stats = {}
    
    section = None
    
    for line in lines:
        line = line.strip()
        
        # Détecter le début des sections
        if line == "OpenVPN CLIENT LIST":
            section = "header"
            continue
        elif line == "ROUTING TABLE":
            section = "routing"
            continue
        elif line == "GLOBAL STATS":
            section = "stats"
            continue
        elif line == "END":
            break
            
        if section == "header":
            if line.startswith("Updated,"):
                result["updated"] = line.split(",")[1]
            elif line.startswith("Common Name,Real Address,"):
                continue
            elif "," in line:
                parts = line.split(",")
                if len(parts) >= 5:
                    common_name = parts[0]
                    real_address = parts[1]
                    bytes_received = parts[2]
                    bytes_sent = parts[3]
                    connected_since = parts[4]
                    
                    client_info[common_name] = {
                        "common_name": common_name,
                        "real_address": real_address,
                        "bytes_received": bytes_received,
                        "bytes_sent": bytes_sent,
                        "connected_since": connected_since,
                        "virtual_addresses": []
                    }
                    
        elif section == "routing":
            if line.startswith("Virtual Address,Common Name,"):
                continue
            elif "," in line:
                parts = line.split(",")
                if len(parts) >= 4:
                    virtual_address = parts[0]
                    common_name = parts[1]
                    real_address = parts[2]
                    last_ref = parts[3]
                    
                    routing_info.append({
                        "virtual_address": virtual_address,
                        "common_name": common_name,
                        "real_address": real_address,
                        "last_ref": last_ref
                    })
                    
        elif section == "stats":
            if "," in line:
                parts = line.split(",")
                if len(parts) == 2:
                    global_stats[parts[0]] = parts[1]
    
    # Associer les adresses virtuelles aux clients
    for route in routing_info:
        common_name = route["common_name"]
        if common_name in client_info:
            client_info[common_name]["virtual_addresses"].append({
                "address": route["virtual_address"],
                "last_ref": route["last_ref"]
            })
    
    # Regrouper les clients par adresse réelle
    clients_by_real_address = {}
    for name, client in client_info.items():
        real_addr = client["real_address"]
        if real_addr in clients_by_real_address:
            # Fusionner les adresses virtuelles si le client existe déjà
            clients_by_real_address[real_addr]["virtual_addresses"].extend(client["virtual_addresses"])
        else:
            clients_by_real_address[real_addr] = client
    
    # Convertir en liste
    result["clients"] = list(clients_by_real_address.values())
    result["global_stats"] = global_stats
    
    return result

# Principal
def main():
    # Lire le fichier
    lines = read_status_file(status_file)
    if not lines:
        return
    
    # Parser les données
    openvpn_data = parse_openvpn_status(lines)
    
    # Écrire les données dans le fichier JSON
    try:
        with open(output_file, 'w') as f:
            json.dump(openvpn_data, f, indent=2)
        print(f"Les données ont été écrites avec succès dans {output_file}")
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier JSON: {e}")

if __name__ == "__main__":
    main()