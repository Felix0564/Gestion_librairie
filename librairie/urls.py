from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login_register/', views.login_register, name='login_register'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('livre/<int:id_livre>/', views.detail_livre, name='detail_livre'),
    path('emprunter/<int:id_livre>/', views.emprunter_livre, name='emprunter_livre'),
    path('mes_emprunts/', views.mes_emprunts, name='mes_emprunts'),
    path('retourner/<int:id_emprunt>/', views.retourner_livre, name='retourner_livre'),
    path('search/', views.search_livre, name='search'),
    path('tableau_de_bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('emprunter/<int:livre_id>/', views.emprunter_livre, name='emprunter_livre'),
]