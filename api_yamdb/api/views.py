from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import filters, mixins, pagination, permissions, viewsets
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from django.shortcuts import get_object_or_404
# local
from reviews.models import Genre, Title, Category, Review, Comment, User
from .permissions import (
    is_authenticated_Or_ReadOnlyPermission, IsAuthorOrReadOnly
)

from .serializers import (
    GenreSerializer,
    TitleSerializer,
    CategorySerializer,
    UserSerializer,
    SignUpSerializer,
    ReviewSerializer,
    CommentSerializer,
)


class GenreviewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (is_authenticated_Or_ReadOnlyPermission,)

    def perform_create(self, serializer):
        pass


class CategoryviewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (is_authenticated_Or_ReadOnlyPermission,)

    def perform_create(self, serializer):
        pass


class TitleviewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (is_authenticated_Or_ReadOnlyPermission,)

    def perform_create(self, serializer):
        pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'username'
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    pagination_class = PageNumberPagination
    #permission_classes = (AllowAny ,)


class SignUpViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        title = Title.objects.get(id=self.kwargs.get('title_id'))
        return title.reviews

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title_obj = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title_obj)

    def partial_update(self, request, *args, **kwargs):
        review = get_object_or_404(
            Review,
            title_id=self.kwargs.get('title_id'),
            id=self.kwargs.get('review_id')
        )
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        serializer.save()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        review_obj = get_object_or_404(Review, id=review_id)
        return review_obj.comments
