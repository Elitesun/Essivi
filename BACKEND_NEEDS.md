# Spécifications des Besoins Backend - Projet Essivivi Dashboard

Ce document recense l'ensemble des besoins backend nécessaires pour le bon fonctionnement de l'application frontend (Next.js), basé sur l'analyse du code existant et de la collection Postman.

## 1. Standards Globaux (Transverses)

*   **Format de réponse** : JSON
*   **Pagination** : Tous les endpoints de liste (`GET /collection`) doivent supporter la pagination (ex: `?page=1&limit=10`).
*   **Filtres & Recherche** : Supporter des query params pour la recherche (ex: `?search=koffi`) et le filtrage (ex: `?status=ABORTED`).
*   **Authentification** : JWT (Access Token + Refresh Token). Le token doit être passé dans le header `Authorization: Bearer <token>`.

---

## 2. Module : Authentification (Auth)

Nécessaire pour sécuriser l'accès au dashboard.

| Méthode | Endpoint | Description | Paylod (Body) | Réponse Attendue |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/login/` | Connexion utilisateur (Admin/Staff) | `{ "email": "...", "password": "..." }` | `{ "access": "...", "refresh": "...", "user": { "id": "...", "role": "..." } }` |
| **POST** | `/api/auth/token/refresh/` | Rafraîchir le token d'accès | `{ "refresh": "..." }` | `{ "access": "..." }` |
| **POST** | `/api/auth/logout/` | Déconnexion (Blacklist refresh token) | `{ "refresh": "..." }` | `204 No Content` |

---

## 3. Module : Utilisateurs Admin (Admin Users)

Gestion des accès à la plateforme (Administrateurs, Gestionnaires, Superviseurs).
*Ref: `src/app/(main)/dashboard/admin-users/` et `schema.ts`*

**Modèle de Donnée (AdminUser)**
*   `id` (string/uuid)
*   `name` (string) : Nom complet
*   `email` (string)
*   `role` (enum) : `Super Admin` | `Gestionnaire` | `Superviseur`
*   `status` (enum) : `Actif` | `Inactif`
*   `lastConnection` (datetime, readonly)

**Endpoints Requis**

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/admin-users/` | Liste des admins (avec pagination/recherche). |
| **POST** | `/api/admin-users/` | Créer un nouvel admin. Body: `{ name, email, role, status }`. Mot de passe à générer ou envoyer par email. |
| **GET** | `/api/admin-users/{id}/` | Détails d'un admin. |
| **PUT** | `/api/admin-users/{id}/` | Modifier un admin (Role, Statut). |
| **DELETE** | `/api/admin-users/{id}/` | Supprimer un admin (soft delete recommandé). |

---

## 4. Module : Agents

Gestion des agents de terrain (livreurs/collecteurs).

**Modèle de Donnée (Agent)**
*   `id` (string/uuid)
*   `nom` (string)
*   `prenom` (string)
*   `telephone` (string)
*   `email` (string, optionnel)
*   `tricycle_assigne` (string) : Référence ou ID du véhicule
*   `statut` (enum) : `actif` | `inactif` | `en_tournee`
*   `date_embauche` (date)

**Endpoints Requis**

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/agents/` | Liste des agents. |
| **POST** | `/api/agents/` | Créer un agent. |
| **GET** | `/api/agents/{id}/` | Détails d'un agent (incluant historique simple). |
| **PUT** | `/api/agents/{id}/` | Mettre à jour (infos perso, statut). |
| **DELETE** | `/api/agents/{id}/` | Désactiver un agent. |

---

## 5. Module : Clients

Gestion des points de vente et clients finaux.

**Modèle de Donnée (Client)**
*   `id` (string/uuid)
*   `code_client` (string, auto-généré, ex: `CL-1234`)
*   `nom_point_vente` (string)
*   `responsable` (string) : Nom du contact
*   `telephone` (string)
*   `adresse` (string)
*   `localisation_gps` (string/json, optionnel) : `{ lat, lng }`
*   `status` (enum) : `actif` | `inactif`

**Endpoints Requis**

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/clients/` | Liste des clients. |
| **POST** | `/api/clients/` | Créer un client. |
| **GET** | `/api/clients/{id}/` | Détails client + Historique commandes récent. |
| **PUT** | `/api/clients/{id}/` | Mettre à jour client. |
| **DELETE** | `/api/clients/{id}/` | Désactiver client. |

---

## 6. Module : Commandes & Livraisons

Gestion du flux opérationnel.

**Modèle de Donnée (Commande/Livraison)**
*   `id` (string/uuid)
*   `client_id` (rel: Client)
*   `agent_id` (rel: Agent, peut être null au début)
*   `date_commande` (datetime)
*   `statut` (enum) : `en_attente` | `en_cours` | `livre` | `annule`
*   `montant` (decimal)
*   `volume_m3` (decimal)
*   `is_validated` (boolean) : Pour confirmation finale admin

**Endpoints Requis**

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/commandes/` | Liste des commandes (Filtres: statut, date). |
| **POST** | `/api/commandes/` | Créer une commande. Body: `{ client_id, items: [...], ... }` |
| **POST** | `/api/commandes/{id}/assign_agent/` | Assigner une commande à un agent. Body: `{ agent_id }` |
| **GET** | `/api/livraisons/` | Liste des livraisons (Vue orientée logistique). |
| **PATCH** | `/api/livraisons/{id}/validate/` | Valider une livraison (Changement statut -> livre + validation admin). |

---

## 7. Module : Statistiques & Rapports

Données pour les graphiques et KPI.
*Ref: `src/app/(main)/dashboard/statistiques/`*

**Endpoints Requis**

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/dashboard/stats/` | KPIs globaux (Total livraisons, CA, etc.) pour le haut de page. |
| **GET** | `/api/stats/production/` | Données pour graphiques production (Evolution volume/temps). |
| **GET** | `/api/stats/performance-agents/` | Classement des agents (Top performers, nombre courses, CA généré). |
| **GET** | `/api/stats/financial/` | Rapports financiers (CA par période, par zone). |

---

## Résumé des Types Enumérés (Frontend vs Backend)

Assurez-vous que ces valeurs correspondent exactement entre le front et le back.

*   `AdminRole`: `['Super Admin', 'Gestionnaire', 'Superviseur']`
*   `AdminStatus`: `['Actif', 'Inactif']`
*   `AgentStatus`: `['actif', 'inactif', 'en_tournee']`
*   `DeliveryStatus`: `['en_attente', 'en_cours', 'livre', 'annule']`
