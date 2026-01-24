from rest_framework import serializers
from .models import AgentCommercial, Client, Commande, Livraison, LogActivite, Tricycle
from accounts.serializers import CustomUserDetailsSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class TricycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tricycle
        fields = ['id', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AgentCommercialSerializer(serializers.ModelSerializer):
    user_details = CustomUserDetailsSerializer(source='user', read_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    tricycle_details = TricycleSerializer(source='tricycle_assigne', read_only=True)

    class Meta:
        model = AgentCommercial
        fields = '__all__'
        read_only_fields = ['user', 'tricycle_assigne', 'created_at', 'updated_at']

class ClientSerializer(serializers.ModelSerializer):
    user_details = CustomUserDetailsSerializer(source='user', read_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class CommandeSerializer(serializers.ModelSerializer):
    client_details = ClientSerializer(source='client', read_only=True)
    agent_details = AgentCommercialSerializer(source='agent_assigne', read_only=True)

    class Meta:
        model = Commande
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class LivraisonSerializer(serializers.ModelSerializer):
    commande_details = CommandeSerializer(source='commande', read_only=True)
    agent_details = AgentCommercialSerializer(source='agent', read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)

    class Meta:
        model = Livraison
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DashboardStatsSerializer(serializers.Serializer):
    total_livraisons = serializers.IntegerField()
    total_reussi = serializers.IntegerField()
    total_echec = serializers.IntegerField()
    total_agents = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    chiffre_affaires = serializers.DecimalField(max_digits=12, decimal_places=2)

class LogActiviteSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LogActivite
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'user', 'user_email']
