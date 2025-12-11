from django.urls import path
#from rest_framework.authtoken import views as auth_views

# Django LogoutView
from django.contrib.auth import views as auth_views

# Django REST Framework Token Login
from rest_framework.authtoken import views as drf_auth_views

# Ampidiro avy eto ireo Views vaovao
from .views import (
    index_view,
    etudiant_signup_api,
    CustomAuthToken,
    EtudiantProfileView,
    chambre_list_api,
    ReservationListCreateAPIView,
    MatriculeEnregistreAdminView
    
)

urlpatterns = [
    # ------------------ FRONT-END CONTAINER (REACT) ------------------
    # Ity no route voalohany mamerina ny index.html ho an'ny React
    path('', index_view, name='index'), 
    
    
    
    # -----------------DECONNEXION----------------------
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    


    # ------------------ API AUTHENTICATION ------------------
    # Login
    path('api/login/', CustomAuthToken.as_view(), name='api_login'), 
    # Signup
    path('api/signup/', etudiant_signup_api, name='api_signup'),



    # ------------------ API ETUDIANT ------------------
    # Profil Etudiant (GET/PUT)
    path('api/profile/', EtudiantProfileView.as_view(), name='api_etudiant_profile'),
    
    
    
    # ------------------ API CHAMBRE (READ) ------------------
    # Lisitry ny Chambre DISPO
    path('api/chambres/', chambre_list_api, name='api_chambre_list'),
    
    
    
    # ------------------ API RESERVATION ------------------
    # Lisitry ny Reservation (GET) ary Mamorona Reservation (POST)
    path('api/reservations/', ReservationListCreateAPIView.as_view(), name='api_reservation_list_create'),
    
    
    
    # ------------------ API ADMIN (CRUD MATRICULE) ------------------
    # CRUD ho an'ny MatriculeEnregistre
    path('api/admin/matricules/', MatriculeEnregistreAdminView.as_view(), name='api_admin_matricules_list_create'),
    # Delete/Detail manokana
    path('api/admin/matricules/<int:pk>/', MatriculeEnregistreAdminView.as_view(), name='api_admin_matricules_detail'),
]