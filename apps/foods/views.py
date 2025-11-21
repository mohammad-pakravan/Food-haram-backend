from rest_framework import mixins, permissions, viewsets

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import KitchenAccess

from .models import Dessert, Food
from .serializers import DessertSerializer, FoodManagementSerializer


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
    Only accessible to kitchen managers (or central users).
    """

    queryset = Food.objects.prefetch_related('ingredients__ingredient')
    serializer_class = FoodManagementSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary="List foods",
        operation_description="Retrieve a paginated list of all foods with their ingredients. Requires kitchen manager access.",
        responses={200: FoodManagementSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve food",
        operation_description="Retrieve a specific food with its ingredients. Requires kitchen manager access.",
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
