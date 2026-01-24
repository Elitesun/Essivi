from django.contrib import admin
from .models import AgentCommercial, Client, Commande, Livraison, LogActivite, Zone

@admin.register(AgentCommercial)
class AgentCommercialAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'statut', 'tricycle_assigne', 'zone_assigned')
    list_filter = ('statut', 'date_embauche', 'zone_assigned')
    search_fields = ('nom', 'prenom', 'telephone')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom_point_vente', 'responsable', 'telephone', 'type_client', 'statut', 'zone')
    list_filter = ('type_client', 'statut', 'zone')
    search_fields = ('nom_point_vente', 'responsable')

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'qt_commandee', 'statut', 'date_commande', 'agent_assigne')
    list_filter = ('statut', 'date_commande')
    search_fields = ('client__nom_point_vente', 'id')

@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'client', 'statut', 'date_heure', 'montant_total')
    list_filter = ('statut', 'date_heure')
    search_fields = ('agent__nom', 'client__nom_point_vente')

@admin.register(LogActivite)
class LogActiviteAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'zone_type', 'radius', 'color', 'is_active')
    list_filter = ('zone_type', 'is_active')
    search_fields = ('id', 'name')
    readonly_fields = ('created_at', 'updated_at')
