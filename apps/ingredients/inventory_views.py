from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Q, F
from django.db import transaction
from decimal import Decimal
import jdatetime
from datetime import date

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import KitchenAccess, WarehouseAccess,RestaurantOrKitchenAccess
from apps.menu.models import MenuPlan

from .models import InventoryStock, InventoryLog, MaterialConsumption, InventoryStockUpdate, Ingredient
from .inventory_serializers import (
    InventoryStockSerializer, 
    InventoryLogSerializer,
    MaterialConsumptionSerializer,
    InventoryStockUpdateSerializer
)


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


class MaterialConsumptionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing MaterialConsumption (مصرفی BOM).
    Kitchen managers can create, view, update, and delete material consumptions.
    """
    
    queryset = MaterialConsumption.objects.select_related(
        'menu_plan', 'menu_plan__food', 'ingredient', 'created_by'
    )
    serializer_class = MaterialConsumptionSerializer
    permission_classes = [KitchenAccess]
    lookup_field = 'id'
    
    def get_queryset(self):
        """فیلتر کردن queryset بر اساس پارامترهای query"""
        queryset = super().get_queryset()
        
        menu_plan = self.request.query_params.get('menu_plan', None)
        ingredient = self.request.query_params.get('ingredient', None)
        date_param = self.request.query_params.get('date', None)
        food = self.request.query_params.get('food', None)
        
        if menu_plan:
            queryset = queryset.filter(menu_plan_id=menu_plan)
        if ingredient:
            queryset = queryset.filter(ingredient_id=ingredient)
        if date_param:
            try:
                year, month, day = map(int, date_param.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                queryset = queryset.filter(menu_plan__date=gregorian_date)
            except (ValueError, AttributeError):
                pass
        if food:
            queryset = queryset.filter(menu_plan__food_id=food)
        
        return queryset
    
    @swagger_auto_schema(
        operation_summary="List material consumptions",
        operation_description="Retrieve all material consumptions (BOM). Requires kitchen manager access.",
        manual_parameters=[
            openapi.Parameter('menu_plan', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('ingredient', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description='Jalali date (YYYY-MM-DD)'),
            openapi.Parameter('food', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
        ],
        responses={200: MaterialConsumptionSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Retrieve material consumption",
        operation_description="Retrieve a specific material consumption. Requires kitchen manager access.",
        responses={200: MaterialConsumptionSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create material consumption",
        operation_description="Create a new material consumption entry. Requires kitchen manager access. Only for menu plans with cook_status='done'.",
        responses={201: MaterialConsumptionSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update material consumption",
        operation_description="Update a material consumption entry. Requires kitchen manager access.",
        responses={200: MaterialConsumptionSerializer()},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partially update material consumption",
        operation_description="Partially update a material consumption entry. Requires kitchen manager access.",
        responses={200: MaterialConsumptionSerializer()},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete material consumption",
        operation_description="Delete a material consumption entry. Requires kitchen manager access.",
        responses={204: 'Material consumption deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class InventoryStockUpdateViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing InventoryStockUpdate (ثبت موجودی واقعی).
    Warehouse managers can create and view inventory stock updates.
    """
    
    queryset = InventoryStockUpdate.objects.select_related('ingredient', 'created_by')
    serializer_class = InventoryStockUpdateSerializer
    permission_classes = [WarehouseAccess]
    lookup_field = 'id'
    
    def get_queryset(self):
        """فیلتر کردن queryset بر اساس پارامترهای query"""
        queryset = super().get_queryset()
        
        ingredient = self.request.query_params.get('ingredient', None)
        inspection_date_from = self.request.query_params.get('inspection_date_from', None)
        inspection_date_to = self.request.query_params.get('inspection_date_to', None)
        created_by = self.request.query_params.get('created_by', None)
        
        if ingredient:
            queryset = queryset.filter(ingredient_id=ingredient)
        if inspection_date_from:
            try:
                year, month, day = map(int, inspection_date_from.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                queryset = queryset.filter(inspection_date__gte=gregorian_date)
            except (ValueError, AttributeError):
                pass
        if inspection_date_to:
            try:
                year, month, day = map(int, inspection_date_to.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                queryset = queryset.filter(inspection_date__lte=gregorian_date)
            except (ValueError, AttributeError):
                pass
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        return queryset
    
    @swagger_auto_schema(
        operation_summary="List inventory stock updates",
        operation_description="Retrieve all inventory stock updates. Requires warehouse manager access.",
        manual_parameters=[
            openapi.Parameter('ingredient', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('inspection_date_from', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description='Jalali date (YYYY-MM-DD)'),
            openapi.Parameter('inspection_date_to', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description='Jalali date (YYYY-MM-DD)'),
            openapi.Parameter('created_by', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
        ],
        responses={200: InventoryStockUpdateSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Retrieve inventory stock update",
        operation_description="Retrieve a specific inventory stock update. Requires warehouse manager access.",
        responses={200: InventoryStockUpdateSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create inventory stock update",
        operation_description="Create a new inventory stock update. This will update the InventoryStock. Requires warehouse manager access. Date should be provided in Jalali format (YYYY-MM-DD).",
        responses={201: InventoryStockUpdateSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class InventoryComparisonView(APIView):
    """
    Endpoint برای مقایسه پیش‌بینی، مصرف واقعی، موجودی فعلی و موجودی قبلی
    برای مدیر مجموعه
    """
    from rest_framework.permissions import IsAuthenticated
    
    permission_classes = [RestaurantOrKitchenAccess]
    
    def dispatch(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().dispatch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Inventory comparison",
        operation_description="Compare predicted amounts, actual consumption, current stock, and previous stock. Requires central user access.",
        manual_parameters=[
            openapi.Parameter('ingredient_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description='Jalali date (YYYY-MM-DD), default: today'),
            openapi.Parameter('previous_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description='Jalali date (YYYY-MM-DD) for previous stock comparison'),
        ],
        responses={200: openapi.Response(description='Comparison data')},
    )
    def get(self, request):
        ingredient_id = request.query_params.get('ingredient_id', None)
        date_param = request.query_params.get('date', None)
        previous_date_param = request.query_params.get('previous_date', None)
        
        # تبدیل تاریخ‌ها
        if date_param:
            try:
                year, month, day = map(int, date_param.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                comparison_date = jalali_date.togregorian()
            except (ValueError, AttributeError):
                comparison_date = date.today()
        else:
            comparison_date = date.today()
        
        if previous_date_param:
            try:
                year, month, day = map(int, previous_date_param.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                previous_date = jalali_date.togregorian()
            except (ValueError, AttributeError):
                previous_date = None
        else:
            previous_date = None
        
        # فیلتر کردن ingredients
        ingredients = Ingredient.objects.all()
        if ingredient_id:
            ingredients = ingredients.filter(id=ingredient_id)
        
        results = []
        
        for ingredient in ingredients:
            # محاسبه پیش‌بینی (از MenuPlan‌ها)
            menu_plans = MenuPlan.objects.filter(
                food__ingredients__ingredient=ingredient,
                date__lte=comparison_date
            ).distinct()
            
            predicted_amount = Decimal('0')
            for menu_plan in menu_plans:
                food_ingredient = menu_plan.food.ingredients.filter(ingredient=ingredient).first()
                if food_ingredient:
                    required_amount = Decimal(str(food_ingredient.amount_per_serving)) * Decimal(str(menu_plan.capacity))
                    predicted_amount += required_amount
            comparison_date_j = jdatetime.date.fromgregorian(date=comparison_date)
            # محاسبه مصرف واقعی (از MaterialConsumption)
            consumptions = MaterialConsumption.objects.filter(
                ingredient=ingredient,
                menu_plan__date__lte=comparison_date_j
            )
            actual_consumption = consumptions.aggregate(
                total=Sum('consumed_amount')
            )['total'] or Decimal('0')
            
            # موجودی فعلی (از آخرین InventoryStockUpdate)
            latest_update = InventoryStockUpdate.objects.filter(
                ingredient=ingredient,
                inspection_date__lte=comparison_date
            ).order_by('-inspection_date', '-created_at').first()
            
            current_stock = Decimal('0')
            if latest_update:
                current_stock = Decimal(str(latest_update.actual_amount))
            
            # موجودی قبلی
            previous_stock = Decimal('0')
            if previous_date:
                previous_update = InventoryStockUpdate.objects.filter(
                    ingredient=ingredient,
                    inspection_date__lte=previous_date
                ).order_by('-inspection_date', '-created_at').first()
                if previous_update:
                    previous_stock = Decimal(str(previous_update.actual_amount))
            
            # محاسبه تفاوت‌ها
            consumption_difference = predicted_amount - actual_consumption
            stock_difference = current_stock - previous_stock if previous_date else Decimal('0')
            actual_consumed = previous_stock - current_stock if previous_date and previous_stock > 0 else Decimal('0')
            
            results.append({
                'ingredient': {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'code': ingredient.code,
                    'unit': ingredient.unit,
                },
                'predicted_amount': float(predicted_amount),
                'actual_consumption': float(actual_consumption),
                'current_stock': float(current_stock),
                'previous_stock': float(previous_stock) if previous_date else None,
                'consumption_difference': float(consumption_difference),
                'stock_difference': float(stock_difference) if previous_date else None,
                'actual_consumed': float(actual_consumed) if previous_date else None,
            })
        
        return Response(results, status=status.HTTP_200_OK)


