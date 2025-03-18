from django.contrib.auth import views as auth_views
from django.urls import path

urlpatterns = [
    # Vue pour demander une réinitialisation de mot de passe
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    # Vue affichant un message confirmant que l'email a été envoyé
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),

    # Vue contenant le formulaire pour entrer un nouveau mot de passe
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Vue affichant un message confirmant que le mot de passe a été réinitialisé avec succès
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
