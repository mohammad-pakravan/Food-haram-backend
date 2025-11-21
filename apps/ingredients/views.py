from rest_framework import mixins, permissions, viewsets

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import KitchenAccess

from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientManagementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for creating, updating, and deleting ingredients.
    Restricted to kitchen managers (or central users).
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [KitchenAccess()]

    @swagger_auto_schema(
        operation_summary="List ingredients",
        operation_description="Retrieve all ingredients with full details. Requires authentication.",
        responses={200: IngredientSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create ingredient",
        operation_description="Create a new ingredient record. Requires kitchen manager access.",
        responses={201: IngredientSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update ingredient",
        operation_description="Replace an existing ingredient record via PUT. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Ingredient ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: IngredientSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update ingredient",
        operation_description="Partially update an ingredient via PATCH. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Ingredient ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: IngredientSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete ingredient",
        operation_description="Delete an ingredient record. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Ingredient ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={204: 'Ingredient deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
