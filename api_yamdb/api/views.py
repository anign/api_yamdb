from random import randint

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from requests import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework import filters, mixins, pagination, permissions, viewsets, status

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import filters, mixins, pagination, permissions, viewsets
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenViewBase

# local
from reviews.models import Genre, Title, Category, User


from .permissions import(
    IsAuthenticatedOrReadOnlyPermission,
    IsAuthorOrReadOnly,
    AdminPermission,
    IsAdminOrReadOnly
)


from .filters import TitlesFilter
from .mixins import ListCreateDestroyViewSet
from .serializers import (
    GenreSerializer,
    TitleSerializer,
    CategorySerializer,
    UserSerializer,
    SignUpSerializer,
    TokenSerializer,
    ReadOnlyTitleSerializer
)


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return ReadOnlyTitleSerializer
        return TitleSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AdminPermission,)
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter,)

    lookup_field = 'username'
    search_fields = ('username',)


    @action(
        ['GET', 'PATCH'], permission_classes=(IsAuthenticated,),
        detail=False, url_path='me'
    )
    def me_user(self, request):
        if not request.data:
            serializer = self.serializer_class(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        if request.user.role == 'admin':
            serializer.update(request.user, serializer.validated_data)
        else:
            serializer.nonadmin_update(
                request.user, serializer.validated_data
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code_confirm = str(randint(1001, 9999))
    user = User.objects.get_or_create(
        username=serializer.data.get('username'),
        email=serializer.data.get('email'),
        confirmation_code=code_confirm
    )
    send_mail(
        subject='Регистрация на сайте',
        message=f'Ваш проверочный код: {code_confirm}',
        recipient_list=[user.email],
        fail_silently=False,
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_token(request):
    serializer = TokenSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        user = get_object_or_404(
            User, username=serializer.data['username'])
        if default_token_generator.check_token(
           user, serializer.data['confirmation_code']):
            token = AccessToken.for_user(user)
            return Response(
                {'token': str(token)}, status=status.HTTP_200_OK)
        return Response({
            'confirmation code': 'Некорректный код подтверждения!'},
            status=status.HTTP_400_BAD_REQUEST)
