from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Etudiant, Chambre, Reservation, Paiement, MatriculeEnregistre

# -------------------------------------------------------------------
#----------------1. Coller le User ----------------------
# -------------------------------------------------------------------
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields' : ('is_admin', 'is_etudiant')}),
    )
    list_display = ('username', 'email','is_admin','is_etudiant','is_staff')
    

# -------------------------------------------------------------------
#----------------2. Fixation du chambre (CRUD admin feno)--------------------
# -------------------------------------------------------------------
@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('id','batiment_chambre','etage_chambre','prix_chambre','statut_chambre')
    list_filter = ('statut_chambre','batiment_chambre','etage_chambre')
    search_fields = ('batiment_chambre','id')
    actions = ['marquer_disponible']
    
    def marquer_disponible(self, request, queryset):
        queryset.update(statut_chambre='DISPO')
    marquer_disponible.short_description = "Marquer comme Disponible"
 
    
# -------------------------------------------------------------------
#----------------3. Fixation Etudiant-------------------------
# -------------------------------------------------------------------
@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('matricule_etudiant','nom_etudiant','prenom_etudiant','mention_etudiant','niveauactu_etudiant')
    search_fields = ('matricule_etudiant','nom_etudiant')
    
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj = None):
        return False
    def has_change_permission(self, request, obj = None):
        return False
    
    readonly_fields = ('nom_etudiant','prenom_etudiant','matricule_etudiant','mention_etudiant','niveauactu_etudiant','tel_etudiant')
    fieldsets = (
        ('Information Etudiant', {
            'fields' : ('user','nom_etudiant','prenom_etudiant','matricule_etudiant','mention_etudiant','niveauactu_etudiant','tel_etudiant'),
        }),
    )
    

# -------------------------------------------------------------------   
#----------------------4.reservation --------------------------------
# -------------------------------------------------------------------
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id','etudiant','chambre','date_voulu','statut_reserva')
    list_filter = ('statut_reserva','date_voulu')
    search_fields = ('etudiant__matricule_etudiant','chambre__id')
    
    readonly_fields = ('etudiant','chambre','niveau_cible','date_voulu','date_creation','periodfinal_paiement')
    
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj = None):
        return False
    
 
# -------------------------------------------------------------------   
#---------------5. paiement ------------------------
# -------------------------------------------------------------------
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id','reservation','montant_paiement','type_paiement','date_paiement','statut_paiement')
    list_filter = ('statut_paiement','type_paiement')
    
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj = None):
        return False
    
    readonly_fields = ('reservation','montant_paiement','type_paiement','date_paiement')
    
    
    
# -------------------------------------------------------------------
# ----------- 6.  MATRICULE ENREGISTRE 
# -------------------------------------------------------------------
@admin.register(MatriculeEnregistre)
class MatriculeEnregistreAdmin(admin.ModelAdmin):
    # Tsika no mameno ny lisitry ny matricule
    list_display = ('matricule','is_used')
    list_filter = ('is_used',)
    search_fields = ('matricule',)
    # Tsy azo ovaina (read-only) ny est_utilise rehefa manampy
    readonly_fields = ('is_used',) 
    
    # Azo ampidirina ny matricule amin'ny alalan'ny kopia/apetaka (copy/paste)
    # Azo ampiana action manao 'Marquer comme non utilisé' raha ilaina
    actions = ['marquer_non_utilise']

    def marquer_non_utilise(self, request, queryset):
        # Action ho an'ny Admin: Mamerina ny matricule ho tsy nampiasaina intsony
        queryset.update(is_used=False)
    marquer_non_utilise.short_description = "Marquer les matricules sélectionnés comme NON UTILISÉS"

    # Mba tsy havela hamafa matricule efa nampiasaina (tsy voatery, fa tsara)
    def has_delete_permission(self, request, obj = None):
        if obj and obj.is_used:
            return False # Tsy azo fafana raha efa nampiasaina
        return True