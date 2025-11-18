from rest_framework import mixins, viewsets

from drf_yasg.utils import swagger_auto_schema

from apps.accounts.permissions import KitchenAccess

from .models import Food
from .serializers import FoodManagementSerializer


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
        responses={200: FoodManagementSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update food",
        operation_description="Partially update a food record. Include ingredients to resync the BOM.",
        responses={200: FoodManagementSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete food",
        operation_description="Delete a food and its ingredient mappings.",
        responses={204: 'Food deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
