from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowDocumentViewSet, CustomTokenObtainPairView, CurrentUserView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'documents', WorkflowDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/current-user/', CurrentUserView.as_view(), name='current_user'),
]