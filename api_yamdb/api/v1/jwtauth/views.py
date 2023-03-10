from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.v1.jwtauth.serializers import SignUpSerializer, ObtainTokenSerializer
from users.models import CustomUser


class SignUpView(generics.CreateAPIView):
    """View-класс для регистрации новых пользователей."""
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny, )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK,
                        headers=headers)

    def perform_create(self, serializer):
        new_user = serializer.save()
        unique_code = default_token_generator.make_token(new_user)
        serializer.save(confirmation_code=unique_code)
        new_user.email_user(
            subject='Код подтверждения от YaMDB',
            message=(f'Здравствуйте, {new_user.username}!\n\n'
                     f'Ваш код подтверждения для регистрации'
                     f' на сайте YaMDB: {unique_code}')
        )


@api_view(['POST'])
@permission_classes((AllowAny, ))
def obtain_token(request):
    """View-функция для получения токена авторизации."""
    serializer = ObtainTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    asking_user = get_object_or_404(
        CustomUser, username=serializer.data['username']
    )
    if not default_token_generator.check_token(
            asking_user, token=serializer.data['confirmation_code']):
        return HttpResponseBadRequest('Неверный код подтверждения.')
    refresh = RefreshToken.for_user(asking_user)
    token_data = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    return Response({'token': token_data['access']}, status.HTTP_200_OK)
