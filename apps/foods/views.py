from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Sum

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import KitchenAccess, RestaurantOrKitchenAccess, RestaurantOrTokenIssuerAccess

from .models import Dessert, Food
from .serializers import DessertSerializer, FoodManagementSerializer
from apps.ingredients.models import CATEGORY_TYPE_CHOICES, SUBCATEGORY_CHOICES
from apps.menu.models import MenuPlan


class FoodManagementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing foods (list/retrieve/create/update/delete) along with their ingredients.
    List and retrieve accessible to restaurant managers and kitchen managers.
    Create/update/delete require kitchen manager access.
    """

    queryset = Food.objects.prefetch_related('ingredients__ingredient')
    serializer_class = FoodManagementSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'

    def get_permissions(self):
        """Allow restaurant_manager and kitchen_manager for reads, kitchen_manager only for writes."""
        # For statistics action, allow all authenticated users
        if self.action == 'statistics':
            return [permissions.IsAuthenticated()]
        
        if self.request.method in permissions.SAFE_METHODS:
            # For read operations, allow restaurant_manager or kitchen_manager
            return [RestaurantOrKitchenAccess()]
        # For write operations, require kitchen_manager access
        return [KitchenAccess()]

    @swagger_auto_schema(
        operation_summary="List foods",
        operation_description="Retrieve a paginated list of all foods with their ingredients. Accessible to restaurant managers and kitchen managers.",
        responses={200: FoodManagementSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve food",
        operation_description="Retrieve a specific food with its ingredients. Accessible to restaurant managers and kitchen managers.",
        responses={200: FoodManagementSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create food",
        operation_description="Create a new food with its ingredients. Requires kitchen manager access.",
        responses={201: FoodManagementSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update food",
        operation_description="Replace an existing food (and optionally its ingredients) via PUT.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Food ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: FoodManagementSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update food",
        operation_description="Partially update a food record. Include ingredients to resync the BOM.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Food ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: FoodManagementSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete food",
        operation_description="Delete a food and its ingredient mappings.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Food ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={204: 'Food deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    @swagger_auto_schema(
        operation_summary="Food statistics by category and subcategory based on MenuPlan capacity",
        operation_description="Get statistics of food capacity from MenuPlan grouped by category and subcategory. Accessible to all authenticated users.",
        responses={
            200: openapi.Response(
                description='Food statistics based on MenuPlan capacity',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'by_category': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Total capacity grouped by category'
                        ),
                        'by_subcategory': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Total capacity grouped by subcategory'
                        ),
                        'by_category_and_subcategory': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description='Total capacity grouped by both category and subcategory'
                        ),
                        'total_capacity': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Total capacity across all MenuPlans'
                        )
                    }
                )
            )
        },
        tags=['Food Statistics']
    )
    def statistics(self, request):
        """Get food statistics based on MenuPlan capacity grouped by category and subcategory"""
        # Get capacity sum by category from MenuPlan
        category_stats = MenuPlan.objects.select_related('food').values(
            'food__category'
        ).annotate(
            total_capacity=Sum('capacity')
        ).order_by('food__category')
        
        # Get capacity sum by subcategory from MenuPlan
        subcategory_stats = MenuPlan.objects.select_related('food').values(
            'food__subcategory'
        ).annotate(
            total_capacity=Sum('capacity')
        ).order_by('food__subcategory')
        
        # Get capacity sum by category and subcategory from MenuPlan
        category_subcategory_stats = MenuPlan.objects.select_related('food').values(
            'food__category',
            'food__subcategory'
        ).annotate(
            total_capacity=Sum('capacity')
        ).order_by('food__category', 'food__subcategory')
        
        # Convert to dictionaries with labels
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        subcategory_dict = dict(SUBCATEGORY_CHOICES)
        
        by_category = {}
        for stat in category_stats:
            category_key = stat['food__category']
            category_label = category_dict.get(category_key, category_key)
            by_category[category_label] = stat['total_capacity'] or 0
        
        by_subcategory = {}
        for stat in subcategory_stats:
            subcategory_key = stat['food__subcategory']
            subcategory_label = subcategory_dict.get(subcategory_key, subcategory_key)
            by_subcategory[subcategory_label] = stat['total_capacity'] or 0
        
        by_category_and_subcategory = []
        for stat in category_subcategory_stats:
            category_key = stat['food__category']
            subcategory_key = stat['food__subcategory']
            category_label = category_dict.get(category_key, category_key)
            subcategory_label = subcategory_dict.get(subcategory_key, subcategory_key)
            
            by_category_and_subcategory.append({
                'category': category_key,
                'category_label': category_label,
                'subcategory': subcategory_key,
                'subcategory_label': subcategory_label,
                'capacity': stat['total_capacity'] or 0
            })
        
        # Calculate total capacity
        total_capacity = MenuPlan.objects.aggregate(
            total=Sum('capacity')
        )['total'] or 0
        
        return Response({
            'by_category': by_category,
            'by_subcategory': by_subcategory,
            'by_category_and_subcategory': by_category_and_subcategory,
            'total_capacity': total_capacity
        })


class DessertViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD for desserts. List accessible to authenticated users; writes require kitchen access.
    """

    queryset = Dessert.objects.all()
    serializer_class = DessertSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [KitchenAccess()]

    @swagger_auto_schema(
        operation_summary="List desserts",
        operation_description="Retrieve all desserts with full details. Requires authentication.",
        responses={200: DessertSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create dessert",
        operation_description="Create a dessert entry. Requires kitchen manager access.",
        responses={201: DessertSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update dessert",
        operation_description="Update a dessert entry via PUT.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Dessert ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: DessertSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update dessert",
        operation_description="Partially update a dessert entry via PATCH.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Dessert ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: DessertSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete dessert",
        operation_description="Delete a dessert entry. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Dessert ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={204: 'Dessert deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
