from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import AgentCommercial, Client, Commande, Livraison, LogActivite
from .serializers import (
    AgentCommercialSerializer, ClientSerializer, CommandeSerializer,
    LivraisonSerializer, DashboardStatsSerializer, LogActiviteSerializer
)

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.user_type == 'admin'

class AgentCommercialViewSet(viewsets.ModelViewSet):
    queryset = AgentCommercial.objects.all()
    serializer_class = AgentCommercialSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'prenom', 'telephone', 'tricycle_assigne']

    def perform_create(self, serializer):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        email = serializer.validated_data.pop('email', None)
        nom = serializer.validated_data.get('nom', 'Agent')
        prenom = serializer.validated_data.get('prenom', 'User')
        
        if not email:
            import random
            # Generate unique email
            email = f"{nom.lower()}.{prenom.lower()}.{random.randint(100,999)}@agent.essivivi.com"
            
        # Check if user exists
        if User.objects.filter(email=email).exists():
             raise filters.ValidationError({'email': 'User with this email already exists.'})

        user = User.objects.create_user(
            email=email,
            password='password123', # Default password for agents
            user_type='agent',
            first_name=prenom,
            last_name=nom,
            is_active=True,
            is_verified=True
        )
        
        serializer.save(user=user)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom_point_vente', 'responsable', 'telephone', 'type_client']

    def perform_create(self, serializer):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        email = serializer.validated_data.pop('email', None)
        responsable = serializer.validated_data.get('responsable', 'Responsable')
        nom_point_vente = serializer.validated_data.get('nom_point_vente', 'Client')
        
        if not email:
            import random
            sanitized_nom = "".join(e for e in nom_point_vente if e.isalnum()).lower()
            email = f"{sanitized_nom}.{random.randint(100,999)}@client.essivivi.com"
            
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'user_type': 'client',
                'first_name': responsable,
                'last_name': nom_point_vente,
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            
        serializer.save(user=user)

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_commande', 'statut']

    @action(detail=True, methods=['post'])
    def assign_agent(self, request, pk=None):
        commande = self.get_object()
        agent_id = request.data.get('agent_id')
        try:
            agent = AgentCommercial.objects.get(id=agent_id)
            commande.agent_assigne = agent
            commande.statut = Commande.Status.EN_COURS
            commande.save()
            return Response({'status': 'agent assigned'})
        except AgentCommercial.DoesNotExist:
            return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.all()
    serializer_class = LivraisonSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_agent(self, request):
        agent_id = request.query_params.get('agent_id')
        if agent_id:
            livraisons = self.queryset.filter(agent__id=agent_id)
            serializer = self.get_serializer(livraisons, many=True)
            return Response(serializer.data)
        return Response({'error': 'agent_id required'}, status=status.HTTP_400_BAD_REQUEST)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total_livraisons = Livraison.objects.count()
        total_reussi = Livraison.objects.filter(statut=Livraison.Status.LIVRE).count()
        total_echec = Livraison.objects.filter(statut=Livraison.Status.ECHEC).count()
        total_agents = AgentCommercial.objects.count()
        total_clients = Client.objects.count()
        
        ca_agg = Livraison.objects.filter(statut=Livraison.Status.LIVRE).aggregate(total=Sum('montant_total'))
        chiffre_affaires = ca_agg['total'] or 0

        data = {
            'total_livraisons': total_livraisons,
            'total_reussi': total_reussi,
            'total_echec': total_echec,
            'total_agents': total_agents,
            'total_clients': total_clients,
            'chiffre_affaires': chiffre_affaires
        }
        return Response(data)

class LogActiviteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogActivite.objects.all()
    serializer_class = LogActiviteSerializer
    permission_classes = [permissions.IsAuthenticated]
