from django.urls import path
from chat.views import RegistrationView, chat_view
# from chat.views import LoginView, LogoutView

urlpatterns = [
    # Registration URL
    path('register/', RegistrationView.as_view(), name='register'),
    path('profile/', chat_view, name='chat-room'),
    path('chat/profile/<str:session_id>/', chat_view, name='chat_session'),
    # Additional URLs for login and logout
    # path('login/', LoginView.as_view(), name='login'),
    # path('logout/', LogoutView.as_view(), name='logout'),
]
