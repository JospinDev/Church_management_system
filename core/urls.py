# from django.urls import path
# from core import views
# urlpatterns = [
#     # path('home/',views.list,name = 'home'),

# ]

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('demande-acces/', views.request_access, name='requestAccess'),
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Membres
    path('membres/', views.membre_list_view, name='membre_list'),
    path('membres/ajouter/', views.membre_create_view, name='membre_create'), 
    path('membres/<int:pk>/', views.membre_detail_view, name='membre_detail'),
    path('membres/<int:pk>/modifier/', views.membre_update_view, name='membre_update'),
    path('membres/<int:pk>/supprimer/', views.membre_delete_view, name='membre_delete'),
    path('membres/export/', views.membre_export_view, name='membre_export'),
    
    # Couples
    path('couples/', views.couple_list_view, name='couple_list'),
    path('couples/<int:pk>/', views.couple_detail_view, name='couple_detail'),
    path('couples/ajouter/', views.couple_form_view, name='couple_create'),
    path('couples/<int:pk>/modifier/', views.couple_form_view, name='couple_update'),
    path('couples/<int:pk>/supprimer/', views.couple_delete_view, name='couple_delete'),

    
    # Programmes d'église
    path('programmes/', views.programme_eglise_list_view, name='programme_list'),
    path('programmes/calendrier/', views.programme_eglise_calendar_view, name='programme_calendar'),
    path('programmes/creer/', views.programme_eglise_create_view, name='programme_create'),
    path('programmes/<int:pk>/', views.programme_eglise_detail_view, name='programme_detail'),
    path('programmes/<int:pk>/modifier/', views.programme_eglise_update_view, name='programme_update'),
    path('programmes/<int:pk>/supprimer/', views.programme_eglise_delete_view, name='programme_delete'),

    # Programmes de marriage
    path('programmes-mariage/', views.programme_mariage_list_view, name='programme_mariage_list'),
    path('programmes-mariage/<int:pk>/', views.programme_mariage_detail_view, name='programme_mariage_detail'),
    path('couples/<int:couple_pk>/programmes-mariage/create/', views.programme_mariage_create_view, name='programme_mariage_create'),
    path('programmes-mariage/ajouter/', views.programme_mariage_couple_select, name='programme_mariage_create'),
    path('programmes-mariage/<int:pk>/update/', views.programme_mariage_update_view, name='programme_mariage_update'),
    path('programmes-mariage/<int:pk>/delete/', views.programme_mariage_delete_view, name='programme_mariage_delete'),
    
    # Groupes
    path('groupes/', views.groupe_list_view, name='groupe_list'),
    path('groupes/<int:pk>/', views.groupe_detail_view, name='groupe_detail'),
    
    # Finances
    path('finances/transactions/', views.transaction_list_view, name='transaction_list'),
    path('dons-materiels/', views.don_materiel_list_view, name='don_materiel_list'),
    
    # Rôles
    path('roles/', views.role_list_view, name='role_list'),
    path('roles/<int:pk>/', views.role_detail_view, name='role_detail'),
    
    # Statistiques
    path('statistiques/', views.statistiques_view, name='statistiques'),
]