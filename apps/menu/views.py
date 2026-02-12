from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import jdatetime
from datetime import date

from rest_framework import permissions
from apps.accounts.permissions import KitchenAccess, KitchenOrTokenIssuerAccess , RestaurantOrKitchenAccess

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
    Kitchen managers can create, update, delete menu plans, and modify cook_status.
    Token issuers can view menu plans (read-only).
    Central users have full access.
    """

    queryset = MenuPlan.objects.select_related('food', 'dessert')
    serializer_class = MenuPlanSerializer
    permission_classes = [KitchenAccess]
    
    def get_permissions(self):
        """Allow token_issuer for read operations, kitchen_manager for write operations"""
        if self.request.method in permissions.SAFE_METHODS:
            return [KitchenOrTokenIssuerAccess()]
        # Allow restaurant_manager , kitchen_manager for DELETE operations
        if self.request.method == 'DELETE':
            return [RestaurantOrKitchenAccess()]
        # other write operations
        return [KitchenAccess()]

    def get_queryset(self):
        """Get base queryset. Filtering by date is handled in list() method."""
        return super().get_queryset()

    @swagger_auto_schema(
        operation_summary="List menu plans",
        operation_description="Retrieve a paginated list of all menu plans. Returns all menu plans if no date filter is provided. Accessible to kitchen managers and token issuers.",
        manual_parameters=[
            openapi.Parameter(
                name='date',
                in_=openapi.IN_QUERY,
                description='Filter by date (Jalali format: YYYY-MM-DD, example: 1404-08-27). Optional.',
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
        """List menu plans, optionally filtered by date."""
        queryset = self.get_queryset()
        date_param = request.query_params.get('date', None)
        
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
        
        # Apply pagination and serialization
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Retrieve menu plan",
        operation_description="Retrieve a specific menu plan. Accessible to kitchen managers and token issuers.",
        responses={200: MenuPlanSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create menu plan",
        operation_description="Create a new menu plan. cook_status defaults to 'pending' if not provided. Requires kitchen manager access.",
        responses={201: MenuPlanSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update menu plan",
        operation_description="Replace an existing menu plan. Requires kitchen manager access.",
        responses={200: MenuPlanSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update menu plan",
        operation_description="Partially update a menu plan. Requires kitchen manager access.",
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

    @action(detail=True, methods=['patch'], permission_classes=[KitchenAccess])
    @swagger_auto_schema(
        operation_summary="Update cook status",
        operation_description="Update the cook status of a menu plan. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Menu plan ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cook_status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['pending', 'cooking', 'done'],
                    description='Cook status: pending, cooking, or done'
                ),
            },
            required=['cook_status']
        ),
        responses={
            200: MenuPlanSerializer(),
            400: openapi.Response(description='Invalid cook_status value'),
        },
        tags=['Menu Plans'],
    )
    def update_cook_status(self, request, pk=None):
        """Update the cook status of a menu plan."""
        menu_plan = self.get_object()
        cook_status = request.data.get('cook_status')
        
        if cook_status not in ['pending', 'cooking', 'done']:
            return Response(
                {'error': 'وضعیت پخت نامعتبر است. مقادیر مجاز: pending, cooking, done'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        menu_plan.cook_status = cook_status
        menu_plan.save()
        
        serializer = self.get_serializer(menu_plan)
        return Response(serializer.data)

