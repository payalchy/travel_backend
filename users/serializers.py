from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, TravelStyle

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # Automatically create user profile
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    preferred_travel_style = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TravelStyle.objects.all(),
        style={'base_template': 'select_multiple.html'}
    )

    preferred_season = serializers.ChoiceField(
        choices=UserProfile.SEASON_CHOICES,
        style={'base_template': 'select.html'}
    )

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'preferred_travel_style', 'preferred_season',
            'budget_preference', 'preferred_duration']
        read_only_fields = ['user']

    def get_fields(self):
        fields = super().get_fields()
        # Show username in HTML form (read-only)
        fields['username'] = serializers.CharField(
            source='user.username',
            read_only=True,
            style={'input_type': 'text', 'template': 'rest_framework/readonly_field.html'}
        )
        return fields

    def validate_budget_preference(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0")
        return value