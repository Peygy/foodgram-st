from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .models import Subscription, User
from .pagination import LimitPagination
from .serializers import AvatarSerializer, SubscriptionSerializer


class AppUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Get details of the current user."""
        return super().me(request)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=("post", "delete"),
    )
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response(
                {"detail": "Невозможно подписаться/отписаться от себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.request.method == "POST":
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Подписка уже оформлена"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = Subscription.objects.create(author=author, user=user)
            serializer = SubscriptionSerializer(
                queryset, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            if not Subscription.objects.filter(
                user=user, author=author
            ).exists():
                return Response(
                    {"detail": "Вы уже отписаны"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = get_object_or_404(
                Subscription, user=user, author=author
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def update_avatar(self, request):
        """Update the avatar of the current user."""
        user = request.user
        if request.method == "PUT":
            avatar_data = request.data.get("avatar")
            if avatar_data is None or avatar_data == "":
                return Response(
                    {"detail": "Аватар не может быть пустым"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AvatarSerializer(
                user, data=request.data, partial=True, context={
                    "request": request
                }
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
