from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Tricycle(models.Model):
    """Tricycle vehicles assigned to agents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Unique tricycle code (e.g., TR-001)")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="Vehicle description or plate number")
    is_active = models.BooleanField(default=True, help_text="Whether the tricycle is in service")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class AgentCommercial(models.Model):
    class Status(models.TextChoices):
        ACTIF = 'actif', 'Actif'
        INACTIF = 'inactif', 'Inactif'
        EN_TOURNEE = 'en_tournee', 'En Tournée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_profile')
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=20)
    tricycle_assigne = models.ForeignKey(Tricycle, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    statut = models.CharField(max_length=20, choices=Status.choices, default=Status.INACTIF)
    date_embauche = models.DateField(default=timezone.localdate)
    
    # GPS tracking for cartography
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Current GPS latitude")
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Current GPS longitude")
    last_location_update = models.DateTimeField(null=True, blank=True, help_text="Last GPS update timestamp")
    zone_assigned = models.CharField(max_length=50, null=True, blank=True, help_text="Assigned zone (e.g., Zone-1)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        tricycle_str = self.tricycle_assigne.code if self.tricycle_assigne else 'Aucun'
        return f"{self.nom} {self.prenom} ({tricycle_str})"

class Client(models.Model):
    class TypeClient(models.TextChoices):
        REVENDEUR = 'revendeur', 'Revendeur'
        PARTICULIER = 'particulier', 'Particulier'
        ENTREPRISE = 'entreprise', 'Entreprise'

    class Status(models.TextChoices):
        ACTIF = 'actif', 'Actif'
        INACTIF = 'inactif', 'Inactif'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Allows linking to a User for login, but Client might strictly be a point of sale managed by admins initially?
    # Requirements say "Client (point de distribution)". Often they might have a login.
    # We'll make it OneToOne with User optionally (if they have login) or just standalone?
    # The `User` model has a 'client' type. So likely they have a login.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile')
    code_client = models.CharField(max_length=50, unique=True, db_index=True, null=True, blank=True, help_text="Auto-generated unique code (e.g., CL-1234)")
    
    nom_point_vente = models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    zone = models.CharField(max_length=50, null=True, blank=True, help_text="Assigned zone (e.g., Zone-1)")
    type_client = models.CharField(max_length=20, choices=TypeClient.choices, default=TypeClient.REVENDEUR)
    statut = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom_point_vente} ({self.responsable})"

class Commande(models.Model):
    class Status(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En Attente'
        EN_COURS = 'en_cours', 'En Cours'
        LIVRE = 'livre', 'Livré'
        ANNULE = 'annule', 'Annulé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    qt_commandee = models.PositiveIntegerField(help_text="Quantité commandée")
    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Montant en CFA")
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=3, default=0, help_text="Volume en m³")
    date_commande = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=Status.choices, default=Status.EN_ATTENTE)
    is_validated = models.BooleanField(default=False, help_text="Admin validation flag")
    agent_assigne = models.ForeignKey(AgentCommercial, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_assignees')
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_validees')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cmd {self.id} - {self.client.nom_point_vente}"

class Livraison(models.Model):
    class Status(models.TextChoices):
        EN_PREPARATION = 'en_preparation', 'En Préparation'
        EN_ROUTE = 'en_route', 'En Route'
        LIVRE = 'livre', 'Livré'
        ECHEC = 'echec', 'Échec'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='livraison', null=True, blank=True)
    # Sometimes delivery is without order? Requirements listed them separately.
    # But usually a delivery fulfills an order or stock replenishment.
    # We will allow standalone deliveries too.
    
    agent = models.ForeignKey(AgentCommercial, on_delete=models.CASCADE, related_name='livraisons')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='livraisons')
    
    quantite_livree = models.PositiveIntegerField()
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_heure = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=Status.choices, default=Status.EN_PREPARATION)
    
    # GPS tracking
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS latitude at delivery")
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS longitude at delivery")
    proximity_validated = models.BooleanField(default=False, help_text="2-meter proximity check passed")
    
    # Proof & validation
    photo_preuve = models.ImageField(upload_to='preuves_livraison/%Y/%m/', null=True, blank=True)
    signature_url = models.ImageField(upload_to='signatures/%Y/%m/', null=True, blank=True)
    is_validated = models.BooleanField(default=False, help_text="Admin validation")
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='livraisons_validees')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Liv {self.id} - {self.agent.nom} -> {self.client.nom_point_vente}"

class LogActivite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class Zone(models.Model):
    """Service zones for delivery areas on map"""
    class ZoneType(models.TextChoices):
        CIRCLE = 'circle', 'Circle'
        POLYGON = 'polygon', 'Polygon'

    id = models.CharField(max_length=50, primary_key=True, help_text="Unique zone ID (e.g., Zone-1)")
    name = models.CharField(max_length=255, help_text="Descriptive name")
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Center latitude")
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Center longitude")
    radius = models.PositiveIntegerField(help_text="Radius in meters (for circle type)")
    zone_type = models.CharField(max_length=10, choices=ZoneType.choices, default=ZoneType.CIRCLE)
    color = models.CharField(max_length=7, default='#3b82f6', help_text="Hex color code")
    polygon_points = models.JSONField(null=True, blank=True, help_text="Array of [lat, lng] points for polygon")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.name}"
