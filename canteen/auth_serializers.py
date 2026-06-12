from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {
            'role': {'default': 'user'},
        }

    def validate_role(self, value):
        if value not in ('user', 'cashier'):
            raise serializers.ValidationError(
                "Рөл тек 'user' немесе 'cashier' болуы мүмкін."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'user'),
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError("Логин немесе құпия сөз қате!")
        if not user.is_active:
            raise serializers.ValidationError("Аккаунт белсендірілмеген.")
        attrs['user'] = user
        return attrs
