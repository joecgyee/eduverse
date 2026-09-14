from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User

from .serializers import UserSerializer, UserUpdateSerializer

TAGS = ["Users"]


class IsSelfOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.id == request.user.id


@extend_schema_view(
    list=extend_schema(
        summary="List / search users",
        description="Returns all users. Use `?search=` to filter by first name, last name, or email.",
        tags=TAGS,
        parameters=[
            OpenApiParameter(name="search", description="Search by name or email", required=False, type=str),
        ],
    ),
    retrieve=extend_schema(
        summary="Get a user's public profile",
        description="Returns a single user's profile, including their student or teacher profile details.",
        tags=TAGS,
    ),
    partial_update=extend_schema(
        summary="Update your own profile",
        description="Partially updates first name, last name, or photo. You can only edit your own account.",
        tags=TAGS,
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    REST interface for User data.

    list: search via ?search=<name or email>
    retrieve: GET /api/v1/users/{id}/
    me: GET/PATCH /api/v1/users/me/  (current user's own record)
    """

    queryset = User.objects.select_related("student_profile", "teacher_profile").order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )
        return qs

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    @extend_schema(
        summary="Get or update your own account",
        description="GET returns the current authenticated user's full profile. "
                     "PATCH partially updates first name, last name, or photo.",
        tags=TAGS,
        responses=UserSerializer,
    )
    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == "GET":
            return Response(UserSerializer(request.user).data)

        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)