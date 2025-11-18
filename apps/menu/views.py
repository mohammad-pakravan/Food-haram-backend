from rest_framework import mixins, viewsets
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import jdatetime
from datetime import date

from apps.accounts.permissions import KitchenAccess

from .models import MenuPlan
from .serializers import MenuPlanSerializer


class MenuPlanViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing menu plans.
    Kitchen managers can create, update, and delete menu plans,
    but cannot modify cook_status (only view it).
    Central users have full access including cook_status.
    """

    queryset = MenuPlan.objects.select_related('food', 'dessert')
    serializer_class = MenuPlanSerializer
    permission_classes = [KitchenAccess]

    def get_queryset(self):
        """Filter menu plans by date (Jalali or Gregorian)"""
        queryset = super().get_queryset()
        date_param = self.request.query_params.get('date', None)
        
        if date_param:
            try:
                # Try to parse as Jalali date first (YYYY-MM-DD)
                year, month, day = map(int, date_param.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                queryset = queryset.filter(date=gregorian_date)
            except (ValueError, AttributeError):
                # If parsing fails, try as Gregorian date
                try:
                    gregorian_date = date.fromisoformat(date_param)
                    queryset = queryset.filter(date=gregorian_date)
                except ValueError:
                    # Invalid date format, return empty queryset
                    queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List menu plans",
        operation_description="Retrieve a paginated list of all menu plans. Filter by date using 'date' query parameter (Jalali format: YYYY-MM-DD). Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='date',
                in_=openapi.IN_QUERY,
                description='Filter by date (Jalali format: YYYY-MM-DD, example: 1404-08-27)',
                type=openapi.TYPE_STRING,
                required=False,
                example='1404-08-27',
            ),
        ],
        responses={
            200: openapi.Response(
                description='Menu plans list',
                schema=MenuPlanSerializer(many=True)
            ),
        },
        tags=['Menu Plans'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve menu plan",
        operation_description="Retrieve a specific menu plan. Requires kitchen manager access.",
        responses={200: MenuPlanSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create menu plan",
        operation_description="Create a new menu plan. Kitchen managers cannot set cook_status (defaults to 'pending'). Requires kitchen manager access.",
        responses={201: MenuPlanSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update menu plan",
        operation_description="Replace an existing menu plan. Kitchen managers cannot modify cook_status. Requires kitchen manager access.",
        responses={200: MenuPlanSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update menu plan",
        operation_description="Partially update a menu plan. Kitchen managers cannot modify cook_status. Requires kitchen manager access.",
        responses={200: MenuPlanSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete menu plan",
        operation_description="Delete a menu plan. Requires kitchen manager access.",
        responses={204: 'Menu plan deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

