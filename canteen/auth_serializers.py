from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Жария тіркелу (POST /api/auth/register/) тек 'user' рөлін жасайды.

    'cashier' немесе 'admin' рөлін ешкім өзіне-өзі бере алмайды —
    мұндай рұқсаттарды тек admin /api/users/{id}/ арқылы (PATCH) тағайындай
    алады. Бұл артық құқық алуды (privilege escalation) болдырмайды.
    """
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role='user',
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
