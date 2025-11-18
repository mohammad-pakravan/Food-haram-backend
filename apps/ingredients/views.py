from rest_framework import mixins, viewsets

from drf_yasg.utils import swagger_auto_schema

from apps.accounts.permissions import KitchenAccess

from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientManagementViewSet(
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
    http_method_names = ['post', 'put', 'patch', 'delete']

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
        responses={200: IngredientSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update ingredient",
        operation_description="Partially update an ingredient via PATCH. Requires kitchen manager access.",
        responses={200: IngredientSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete ingredient",
        operation_description="Delete an ingredient record. Requires kitchen manager access.",
        responses={204: 'Ingredient deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
