from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import DeliveryDeskAccess
from .models import DirectSale, DirectSaleItem
from .serializers import DirectSaleCreateSerializer, DirectSaleListSerializer


class DirectSaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DirectSales.
    Delivery desk role required for all operations (create, read, delete).
    """
    queryset = DirectSale.objects.all()
    permission_classes = [DeliveryDeskAccess]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DirectSaleCreateSerializer
        return DirectSaleListSerializer
    
    @swagger_auto_schema(
        operation_summary="Create sale",
        operation_description="Create a new sale with food items. Requires delivery_desk role.",
        request_body=DirectSaleCreateSerializer,
        responses={
            201: DirectSaleListSerializer(),
            400: 'Validation error'
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new sale with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        direct_sale = serializer.save()
        
        # Return created sale with items
        response_serializer = DirectSaleListSerializer(direct_sale)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_summary="List sales",
        operation_description="Retrieve all sales. Requires delivery_desk role.",
        responses={200: DirectSaleListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all sales - Only accessible by delivery_desk role"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Retrieve sale",
        operation_description="Retrieve a specific sale by ID. Requires delivery_desk role.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description='Sale ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: DirectSaleListSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific sale - Only accessible by delivery_desk role"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete sale",
        operation_description="Delete a sale. Requires delivery_desk role.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description='Sale ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={204: 'Sale deleted'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

