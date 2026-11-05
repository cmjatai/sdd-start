from django.conf import settings
from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _
from image_cropping.utils import get_backend
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drfautoapi.drfautoapi import ApiViewSetConstrutor


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.filter(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({'message': 'Token recriado com sucesso!', 'token': token.key})


class AppSessionAuthView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'detail': _('Autenticação efetuada com sucesso!')})

    def delete(self, request):
        logout(request)
        return Response({'detail': _('Desconexão efetuada com sucesso!')})


class AppVersionView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        content = {
            'name': 'Backend',
            'description': 'Plataforma ...',
            'version': settings.PROJECT_VERSION,
        }

        if request.user.is_authenticated:
            # token = Token.objects.filter(user=request.user).first()
            #    'token': token.key,
            user = {
                'username': request.user.username,
                'fullname': request.user.get_full_name(),
                'avatar': '/static/imgs/perfil.png'
                if not request.user.avatar
                else get_backend().get_thumbnail_url(
                    request.user.avatar,
                    {
                        'size': (128, 128),
                        'box': request.user.avatar_cropping,
                        'crop': True,
                        'detail': True,
                    },
                ),
            }
            content.update({'user': user})

        return Response(content)


BackendApiViewSetConstrutor = ApiViewSetConstrutor
BackendApiViewSetConstrutor.import_modules(
    [
        'backend.api.views_eauth',
    ]
)
