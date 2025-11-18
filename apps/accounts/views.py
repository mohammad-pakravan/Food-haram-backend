from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, AccessRole
from .serializers import UserSerializer, UserUpdateSerializer, ChangePasswordSerializer
from .token_serializer import CustomTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    """
    Custom login view that sets JWT tokens in HTTP Only Cookies.
    
    Authenticates user with username, password, and panel (role).
    Checks if user has access to the specified panel.
    Sets access and refresh tokens as HTTP Only Cookies for enhanced security.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        operation_description="Login with username, password, and panel (role). Tokens are set as HTTP Only Cookies.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'panel'],
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Username for authentication',
                    example='admin'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Password for authentication',
                    example='admin123'
                ),
                'panel': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Panel (role) to access. Required.',
                    enum=['kitchen_manager', 'restaurant_manager', 'token_issuer', 'delivery_desk'],
                    example='kitchen_manager'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Login successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='ورود موفقیت آمیز بود'
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, example='admin'),
                                'active_role': openapi.Schema(type=openapi.TYPE_STRING, example='kitchen_manager'),
                                'roles': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    example=['kitchen_manager', 'token_issuer']
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request - Invalid panel or missing required fields',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Panel (role) is required for login.'
                        )
                    }
                )
            ),
            401: openapi.Response(
                description='Unauthorized - Invalid credentials',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='Invalid credentials'
                        )
                    }
                )
            ),
            403: openapi.Response(
                description='Forbidden - User does not have access to the specified panel',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='این سطح دسترسی وجود نداره'
                        )
                    }
                )
            )
        },
        tags=['auth']
    )
    def post(self, request, *args, **kwargs):
        # Panel is required
        panel = request.data.get('panel')
        if not panel:
            return Response(
                {'detail': 'Panel (role) is required for login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate panel is a valid role
        valid_roles = [role[0] for role in AccessRole.choices]
        if panel not in valid_roles:
            return Response(
                {'detail': f'Invalid panel. Valid panels are: {", ".join(valid_roles)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Call parent method with request context
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        try:
            serializer.is_valid(raise_exception=True)
        except PermissionDenied as e:
            return Response(
                {'detail': 'این سطح دسترسی وجود نداره'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get tokens and user data
        access_token = serializer.validated_data.get('access')
        refresh_token = serializer.validated_data.get('refresh')
        user_data = serializer.validated_data.get('user')
        
        # Create response with success message (tokens are in HTTP Only Cookies)
        response = Response({
            'message': 'ورود موفقیت آمیز بود',
            'user': user_data
        }, status=status.HTTP_200_OK)
        
        # Set tokens in HTTP Only Cookies
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,  # Only use secure in production
            samesite='Lax',
            max_age=60 * 60,  # 1 hour (matches ACCESS_TOKEN_LIFETIME)
            path='/',
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,  # Only use secure in production
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,  # 7 days (matches REFRESH_TOKEN_LIFETIME)
            path='/',
        )
        
        return response


class RefreshTokenView(TokenRefreshView):
    """
    Custom refresh token view that reads from HTTP Only Cookie and sets new tokens.
    
    Reads refresh token from HTTP Only Cookie and generates new access and refresh tokens.
    Sets new tokens as HTTP Only Cookies.
    """
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Set refresh token in request data
        request.data['refresh'] = refresh_token
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            new_refresh_token = response.data.get('refresh')
            
            # Set new tokens in HTTP Only Cookies
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=60 * 60,  # 1 hour
                path='/',
            )
            
            if new_refresh_token:
                response.set_cookie(
                    key='refresh_token',
                    value=new_refresh_token,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax',
                    max_age=60 * 60 * 24 * 7,  # 7 days
                    path='/',
                )
            
            # Remove tokens from response body
            response.data.pop('access', None)
            response.data.pop('refresh', None)
            response.data['message'] = 'Token refreshed successfully'
        
        return response


class LogoutView(APIView):
    """
    Logout view that clears HTTP Only Cookies.
    
    Invalidates the refresh token and clears access and refresh token cookies.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Blacklist the token if using token blacklist app
        except Exception as e:
            # If token blacklist is not configured, just continue
            pass
        
        # Clear cookies
        response = Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value='',
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=0,
            path='/',
        )
        response.set_cookie(
            key='refresh_token',
            value='',
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=0,
            path='/',
        )
        
        return response


class MeView(APIView):
    """
    Get current authenticated user information.
    
    Returns detailed information about the currently authenticated user,
    including their roles and central user status.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AccessRolesView(APIView):
    """
    Get list of available access roles.
    
    Returns a list of all available access roles in the system
    with their values and labels.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retrieve list of available access roles.
        
        Returns:
            Response: List of roles with value and label pairs
        """
        from .models import AccessRole
        roles = [
            {'value': role[0], 'label': role[1]}
            for role in AccessRole.choices
        ]
        return Response(roles)


class UpdateProfileView(APIView):
    """
    Update current authenticated user profile information.
    
    Allows users to update their email, first_name, and last_name.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update current authenticated user profile information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    example='user@example.com'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User first name',
                    example='John'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User last name',
                    example='Doe'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Profile updated successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='اطلاعات کاربری با موفقیت به‌روزرسانی شد'
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Updated user information'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request - Validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=['This email is already in use.']
                        )
                    }
                )
            )
        },
        tags=['User Profile']
    )
    def put(self, request):
        """Update user profile"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'اطلاعات کاربری با موفقیت به‌روزرسانی شد',
                'user': UserSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Partially update current authenticated user profile information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    example='user@example.com'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User first name',
                    example='John'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User last name',
                    example='Doe'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Profile updated successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='اطلاعات کاربری با موفقیت به‌روزرسانی شد'
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Updated user information'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request - Validation errors'
            )
        },
        tags=['User Profile']
    )
    def patch(self, request):
        """Partially update user profile"""
        return self.put(request)


class ChangePasswordView(APIView):
    """
    Change current authenticated user password.
    
    Requires old password and new password with confirmation.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change current authenticated user password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password', 'new_password_confirm'],
            properties={
                'old_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Current password',
                    example='current_password'
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='New password (must meet Django password validation requirements)',
                    example='new_secure_password'
                ),
                'new_password_confirm': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Confirm new password (must match new_password)',
                    example='new_secure_password'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Password changed successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example='رمز عبور با موفقیت تغییر کرد'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request - Validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'old_password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=['Current password is incorrect.']
                        ),
                        'new_password_confirm': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=['New passwords do not match.']
                        ),
                        'new_password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=['This password is too short. It must contain at least 8 characters.']
                        )
                    }
                )
            )
        },
        tags=['User Profile']
    )
    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'رمز عبور با موفقیت تغییر کرد'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
