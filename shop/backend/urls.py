from django.urls import path

from backend.views import PartnerUpdate, RegisterAccount, ConfirmAccount, LoginAccount, AccountDetails, ContactView

app_name = 'backend'
urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', LoginAccount.as_view(), name='user-login'),


    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
]