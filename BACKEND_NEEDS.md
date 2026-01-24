1. Onglet : Rapports de Production
Cet onglet utilise deux endpoints distincts.

A. Cartes de résumé (Haut de page)
Endpoint : GET /dashboard/stats/ Description : Retourne les totaux globaux et les pourcentages de croissance.

json
{
  "total_deliveries": 1250,       // Nombre total de livraisons
  "total_quantity": 45000,        // Quantité totale (ex: litres/m3)
  "total_amount": 15000000,       // Montant total en FCFA
  "delivery_growth": 12.5,        // Croissance livraisons vs mois dernier (%)
  "quantity_growth": 8.4,         // Croissance quantité vs mois dernier (%)
  "amount_growth": -2.1           // Croissance montant vs mois dernier (%)
}
B. Performance par Agent (Tableau)
Endpoint : GET /dashboard/performance-agents/ Description : Retourne la liste des agents et leurs performances individuelles.

json
[
  {
    "agent_id": "AGT-001",
    "agent_name": "Kouamé Jean",
    "deliveries_count": 145,
    "quantity_delivered": 5200,
    "total_amount": 1800000,
    "status": "Top Performer"     // Valeurs acceptées: "Top Performer", "Excellent", "Bon", "Moyen", "Faible"
  },
  {
    "agent_id": "AGT-002",
    "agent_name": "Diallo Moussa",
    "deliveries_count": 98,
    "quantity_delivered": 3400,
    "total_amount": 1100000,
    "status": "Bon"
  }
]
(Note : Le service gère aussi si ces données sont encapsulées dans un objet { "results": [...] } ou { "data": [...] })

2. Onglet : Analyses Statistiques
Cet onglet affiche des graphiques et combine des données de production et financières.

A. Données des Graphiques (Heures de pointe & Zones)
Endpoint : GET /dashboard/production/?period=30 Description : Données pour les graphiques à barres.

json
{
  "peak_hours": [                 // Pour le graphique "Heures de Pointe"
    { "hour": "08:00", "sales": 45 },
    { "hour": "09:00", "sales": 120 },
    { "hour": "10:00", "sales": 80 },
    { "hour": "14:00", "sales": 60 }
  ],
  "top_zones": [                  // Pour le graphique "Zones Géographiques"
    { "zone": "Cocody", "value": 1500 },
    { "zone": "Yopougon", "value": 1200 },
    { "zone": "Marcory", "value": 950 }
  ],
  "sales_over_time": []           // (Optionnel, non utilisé par le composant actuel mais prévu dans l'interface)
}
B. Données du Graphique "Évolution du Chiffre d'Affaires"
Le graphique "Évolution du Chiffre d'Affaires" utilise les données revenue_history provenant de l'endpoint financier ci-dessous (GET /dashboard/financial/).

3. Onglet : Rapports Financiers
Cet onglet gère tout l'aspect financier, les créances et les prévisions.

Endpoint : GET /dashboard/financial/?period=daily (ou monthly) Description : Retourne un objet complexe contenant trois sections principales.

json
{
  "revenue_vs_target": {          // Pour les barres de progression "Prévisions de Ventes"
    "global": {
      "current": 15000000,        // Réalisé
      "target": 20000000          // Objectif
    },
    "tricycles": {
      "current": 8000000,
      "target": 10000000
    },
    "wholesale": {
      "current": 7000000,
      "target": 10000000
    }
  },
  "debts": [                      // Pour le tableau "Créances Clients"
    {
      "client_name": "Maquis La Paix",
      "amount_due": 50000,
      "due_date": "2024-05-15"
    },
    {
      "client_name": "Hôtel Ivoire",
      "amount_due": 125000,
      "due_date": "2024-05-10"
    }
  ],
  "revenue_history": [            // Pour le tableau "Détail" ET le graphique "Évolution CA"
    {
      "period": "Jan 2024",       // Ou une date "2024-01-01"
      "revenue": 4500000,
      "target": 4000000,
      "variation": 12.5           // Pourcentage
    },
    {
      "period": "Feb 2024",
      "revenue": 4200000,
      "target": 4000000,
      "variation": 5.0
    }
  ]
}
Résumé pour le développeur Backend
Uniformiser le format de réponse : Idéalement, retournez toujours les données directement ou encapsulées dans une clé standard (ex: data). Le frontend gère actuellement res.data, res.data.data, res.data.stats ou res.data.results.
Gestion des erreurs : Si une section est vide (exemple : pas de créances), retournez un tableau vide [] plutôt que null ou une erreur 404, afin que l'interface affiche "Aucune donnée" proprement au lieu de planter.
Snake_case vs CamelCase : Le code TypeScript s'attend principalement à du snake_case (ex: total_amount, agent_name, peak_hours), assurez-vous que le backend respecte cette convection pour éviter des valeurs undefined.