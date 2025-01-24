from django.urls import path

from backend.views import PartnerUpdate, RegisterAccount, ConfirmAccount, LoginAccount

app_name = 'backend'
urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
]