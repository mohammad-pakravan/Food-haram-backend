from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.permissions import TokenIssuerAccess, DeliveryDeskAccess
from .models import Token, TokenItem
from .serializers import TokenCreateSerializer, TokenListSerializer, TokenStatusUpdateSerializer


class TokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tokens.
    TokenIssuer role required for all operations (create, read, delete).
    """
    queryset = Token.objects.all()
    permission_classes = [TokenIssuerAccess]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TokenCreateSerializer
        return TokenListSerializer
    
    @swagger_auto_schema(
        operation_summary="Create token",
        operation_description="Create a new token with food items. Requires token_issuer role.",
        request_body=TokenCreateSerializer,
        responses={
            201: TokenListSerializer(),
            400: 'Validation error'
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new token with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        
        # Return created token with items
        response_serializer = TokenListSerializer(token)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_summary="List issued tokens",
        operation_description="Retrieve all issued tokens. Requires token_issuer role.",
        responses={200: TokenListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all issued tokens - Only accessible by token_issuer role"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Retrieve token",
        operation_description="Retrieve a specific token by ID. Requires token_issuer role.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description='Token ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={200: TokenListSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific token - Only accessible by token_issuer role"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete token",
        operation_description="Delete a token. Requires token_issuer role.",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description='Token ID',
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={204: 'Token deleted'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], permission_classes=[DeliveryDeskAccess], url_path='mark-received')
    @swagger_auto_schema(
        operation_summary="Mark token as received",
        operation_description="Mark a token as received by token_code. Requires delivery_desk role. Prevents duplicate marking.",
        request_body=TokenStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description='Token marked as received',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Token details with updated status'
                )
            ),
            400: 'Validation error',
            404: 'Token not found'
        },
        tags=['Token Status']
    )
    def mark_received(self, request):
        """Mark token as received by token_code"""
        serializer = TokenStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.update_status()
        
        # Return token with updated status
        response_serializer = TokenListSerializer(token)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

