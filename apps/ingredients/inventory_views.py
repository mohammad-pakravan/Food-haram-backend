from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import KitchenAccess

from .models import InventoryStock, InventoryLog
from .inventory_serializers import InventoryStockSerializer, InventoryLogSerializer


class InventoryStockViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing kitchen inventory stock.
    Kitchen managers can view and update inventory stock.
    """

    queryset = InventoryStock.objects.select_related('ingredient')
    serializer_class = InventoryStockSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary="List inventory stock",
        operation_description="Retrieve all inventory stock items with details. Requires kitchen manager access.",
        responses={200: InventoryStockSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve inventory stock",
        operation_description="Retrieve a specific inventory stock item. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Inventory stock ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: InventoryStockSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create inventory stock",
        operation_description="Create a new inventory stock entry. Requires kitchen manager access.",
        responses={201: InventoryStockSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update inventory stock",
        operation_description="Update an inventory stock entry via PUT. Requires kitchen manager access. Date should be provided in Jalali format (YYYY-MM-DD, e.g., 1404-08-27).",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Inventory stock ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ingredient': openapi.Schema(type=openapi.TYPE_INTEGER, description='Ingredient ID'),
                'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total amount in stock'),
                'last_received_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Last received date in Jalali format (YYYY-MM-DD, e.g., 1404-08-27)',
                    example='1404-08-27'
                ),
            },
            required=['ingredient', 'total_amount']
        ),
        responses={200: InventoryStockSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update inventory stock",
        operation_description="Partially update an inventory stock entry via PATCH. Requires kitchen manager access. Date should be provided in Jalali format (YYYY-MM-DD, e.g., 1404-08-27).",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Inventory stock ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ingredient': openapi.Schema(type=openapi.TYPE_INTEGER, description='Ingredient ID'),
                'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total amount in stock'),
                'last_received_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Last received date in Jalali format (YYYY-MM-DD, e.g., 1404-08-27)',
                    example='1404-08-27'
                ),
            },
        ),
        responses={200: InventoryStockSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class InventoryLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing inventory logs (items received from warehouse).
    Kitchen managers can view and create inventory logs.
    """

    queryset = InventoryLog.objects.select_related('inventory__ingredient')
    serializer_class = InventoryLogSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary="List inventory logs",
        operation_description="Retrieve all inventory logs (items received from warehouse). Requires kitchen manager access.",
        responses={200: InventoryLogSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve inventory log",
        operation_description="Retrieve a specific inventory log. Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                description='Inventory log ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: InventoryLogSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create inventory log",
        operation_description="Create a new inventory log entry (item received from warehouse). This will update the inventory stock. Requires kitchen manager access. Date should be provided in Jalali format (YYYY-MM-DD, e.g., 1404-08-27).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'inventory': openapi.Schema(type=openapi.TYPE_INTEGER, description='Inventory stock ID'),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='Amount received'),
                'unit': openapi.Schema(type=openapi.TYPE_STRING, description='Unit of measurement'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='Code'),
                'date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Date in Jalali format (YYYY-MM-DD, e.g., 1404-08-27)',
                    example='1404-08-27'
                ),
            },
            required=['inventory', 'amount', 'unit', 'code', 'date']
        ),
        responses={201: InventoryLogSerializer()},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the inventory stock
        inventory_stock = serializer.validated_data['inventory']
        amount = serializer.validated_data['amount']
        
        # Update inventory stock
        inventory_stock.total_amount += amount
        inventory_stock.save()
        
        # Create the log entry
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


