from rest_framework import serializers
from .models import UserRestaurantPermission
from apps.accounts.models import AccessRole


class UserNestedSerializer(serializers.Serializer):
    """Nested user serializer for permissions"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)


class RestaurantNestedSerializer(serializers.Serializer):
    """Nested restaurant serializer for permissions"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class TimestampsSerializer(serializers.Serializer):
    """Timestamps serializer"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserRestaurantPermissionSerializer(serializers.ModelSerializer):
    """Serializer for user-restaurant permissions with custom format"""
    user = UserNestedSerializer(read_only=True)
    restaurant = RestaurantNestedSerializer(read_only=True)
    timestamps = TimestampsSerializer(source='*', read_only=True)
    roles = serializers.MultipleChoiceField(
        choices=AccessRole.choices,
        help_text='Access roles for the user in this restaurant'
    )
    
    class Meta:
        model = UserRestaurantPermission
        fields = ['id', 'user', 'restaurant', 'roles', 'timestamps']
        read_only_fields = ['id']

