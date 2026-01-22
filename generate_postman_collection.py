import json
import uuid

COLLECTION_NAME = "Essivivi Admin API"
BASE_URL = "{{base_url}}"

def create_item(name, method, url, body=None):
    item = {
        "name": name,
        "request": {
            "method": method,
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json",
                    "type": "text"
                },
                {
                    "key": "Authorization",
                    "value": "Bearer {{access_token}}",
                    "type": "text"
                }
            ],
            "url": {
                "raw": f"{BASE_URL}/{url}",
                "host": ["{{base_url}}"],
                "path": url.split('/')
            }
        },
        "response": []
    }
    if body:
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=4)
        }
    return item

def generate_collection():
    collection = {
        "info": {
            "name": COLLECTION_NAME,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8001/api",
                "type": "string"
            },
            {
                "key": "access_token",
                "value": "",
                "type": "string"
            }
        ]
    }

    # Auth Folder
    auth_folder = {
        "name": "Auth",
        "item": [
            {
                "name": "Login",
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "pm.environment.set(\"access_token\", jsonData.access);"
                            ],
                            "type": "text/javascript"
                        }
                    }
                ],
                "request": {
                    "method": "POST",
                    "header": [
                        {"key": "Content-Type", "value": "application/json", "type": "text"}
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "admin@essivivi.com",
                            "password": "password123"
                        }, indent=4)
                    },
                    "url": {
                        "raw": f"{BASE_URL}/auth/login/",
                        "host": ["{{base_url}}"],
                        "path": ["auth", "login", ""]
                    }
                },
                "response": []
            },
            create_item("Refresh Token", "POST", "auth/token/refresh/", {"refresh": "{{refresh_token}}"})
        ]
    }
    collection["item"].append(auth_folder)

    # Agents Folder
    agents_folder = {
        "name": "Agents",
        "item": [
            create_item("List Agents", "GET", "agents/"),
            create_item("Create Agent", "POST", "agents/", {
                "nom": "Doe",
                "prenom": "John", 
                "telephone": "+22890909090",
                "tricycle_assigne": "TRI-001"
            }),
            create_item("Get Agent", "GET", "agents/{{agent_id}}/"),
            create_item("Update Agent", "PUT", "agents/{{agent_id}}/", {"statut": "actif"}),
            create_item("Delete Agent", "DELETE", "agents/{{agent_id}}/")
        ]
    }
    collection["item"].append(agents_folder)

    # Clients Folder
    clients_folder = {
        "name": "Clients",
        "item": [
            create_item("List Clients", "GET", "clients/"),
            create_item("Create Client", "POST", "clients/", {
                "nom_point_vente": "Super Boutique",
                "responsable": "Alice",
                "telephone": "+22891919191",
                "adresse": "Lome, Agoe"
            }),
             create_item("Get Client", "GET", "clients/{{client_id}}/"),
        ]
    }
    collection["item"].append(clients_folder)

    # Commandes Folder
    orders_folder = {
        "name": "Commandes",
        "item": [
            create_item("List Commandes", "GET", "commandes/"),
            create_item("Create Commande", "POST", "commandes/", {
                "client": "{{client_id}}",
                "qt_commandee": 50
            }),
            create_item("Assign Agent", "POST", "commandes/{{commande_id}}/assign_agent/", {"agent_id": "{{agent_id}}"})
        ]
    }
    collection["item"].append(orders_folder)

    # Livraisons Folder
    deliveries_folder = {
        "name": "Livraisons",
        "item": [
            create_item("List Livraisons", "GET", "livraisons/"),
            create_item("Validate Delivery", "PATCH", "livraisons/{{livraison_id}}/", {"statut": "livre", "is_validated": True})
        ]
    }
    collection["item"].append(deliveries_folder)
    
    # Dashboard
    collection["item"].append(create_item("Dashboard Stats", "GET", "dashboard/stats/"))

    with open('essivi_custom_collection.json', 'w') as f:
        json.dump(collection, f, indent=4)
    print("Collection generated: essivi_custom_collection.json")

if __name__ == "__main__":
    generate_collection()
