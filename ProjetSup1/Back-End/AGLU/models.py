from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone
import calendar 

# ------------------- 1 .Model de base : User ---------------------- 
# ------------ mot de passe pour admin et etudiant ---------------
class User(AbstractUser):
    # Field default ho an'ny Role (Admin na Etudiant)
    is_admin=models.BooleanField(default=False)
    is_etudiant=models.BooleanField(default=False)
    # Rehefa manao inscription ny admin/etudiant is_***=True

    
# ----------------- 2. Modely fanamarinana Matricule (LOGIQUE VAOVAO) ----------------
# Ity table ity no fenoen'ny programmeur mialoha
class MatriculeEnregistre(models.Model):
    # Ny Matricule tsy maintsy mitovy amin'ny an'ny Etudiant.
    matricule = models.CharField(max_length=20, unique=True, help_text="Matricule azo ekena")
    # Tsy maintsy False rehefa manao inscription vao avela handeha.
    is_used = models.BooleanField(default=False, help_text="Efa nampiasaina ve ity ho an'ny User iray")

    def __str__(self):
        return f"Matricule Enregistré: {self.matricule} (Used: {self.is_used})"
    


# ------------------3 . Liste deroulante (choix) --------------------
mention_choix=(
    ('INFO','Informatique'),
    ('MATHS','Mathematique'),
    ('COMM','Communication'),
    ('AGRO','Agronomie'),
)

niveau_choix=(
    (1,'L1'),
    (2,'L2'),
    (3,'L3'),
    (4,'M1'),
    (5,'M2'),
)

batiment_choix=(
    ('R+G1','R+G1'),
    ('R+F2','R+F2'),
    ('R+G3','R+G3'),
    ('R+F4','R+F4'),
    ('R+M1','R+M1'),
    ('R+GZ','R+GZ'),
)

statutchambre_choix=(
    ('DISPO','Disponible'),
    ('OCCUP','Occupee'),
    ('BPOS','Bientot Dispo'), # BPOS: Bientot Dispo
    ('HS','Hors Service'),
)

statutreserva_choix=(
    ('ATT','En attente'), # ATT: En attente
    ('VAL','Valide'),   # VAL: Valide
    ('ANNUL','Annule'), # ANNUL: Annule
)

statutpaiement_choix=(
    ('PAYE','Paye'),
    ('IMPAYE','Impaye'),
    ('PARTIEL','Partiel'),
)

typepaiement_choix=(
    ('MOIS','Mensuel'),
    ('ANNEE','Annuel'),
)




# -------------------------------------------------------------------------------------
#-----------4. ETUDIANTS (etudian-mifandray @User)---------------
# -------------------------------------------------------------------------------------

class Etudiant(models.Model):
    # cle primaire = id_etudiant (Auto par defaut @django)
    # Relation 1-to-1 amin'ny User, raha fafana ny User dia fafana koa ity
    user=models.OneToOneField(User, on_delete=models.CASCADE) 
    
    # Ny Matricule eto dia Unique, ampiasaina ho an'ny Login (username)
    # Tsy maintsy fenoina amin'ny inscription ity
    matricule_etudiant=models.CharField(max_length=20, unique=True, help_text="Tsy maintsy fenoina ity")
    
    # Field hafa manokana
    nom_etudiant=models.CharField(max_length=100, help_text="Anarana")
    prenom_etudiant=models.CharField(max_length=100, help_text="Fanampin'anarana")
    mention_etudiant=models.CharField(max_length=5, choices=mention_choix, help_text="Ny mention anao")
    niveauactu_etudiant=models.IntegerField(choices=niveau_choix)
    tel_etudiant=models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self): # affichage ao @interface admin
        return f"{self.nom_etudiant} {self.prenom_etudiant} ({self.matricule_etudiant})"
    





# -------------------------------------------------------------------------------------    
#-----------5. CHAMBRES (admin no mameno azy)---------------
# -------------------------------------------------------------------------------------

class Chambre(models.Model):
    # cle primaire = id_chambre (Auto par defaut @django)
    batiment_chambre=models.CharField(max_length=4, choices=batiment_choix, help_text="batiment aiza")
    caract_chambre=models.TextField(help_text="mombamonra an'ilay efitra.")
    etage_chambre=models.CharField(max_length=20)
    # Max 10 chiffres (2 aorian'ny faingo)
    prix_chambre=models.DecimalField(max_digits=10, decimal_places=2) 
    statut_chambre=models.CharField(max_length=5, choices=statutchambre_choix, default='DISPO')
    
    def __str__(self): 
        return f"chambre {self.id} - Bat.{self.batiment_chambre}"






# -------------------------------------------------------------------------------------    
#-----------6. RESERVATION (ireo calcul)---------------
# -------------------------------------------------------------------------------------

class Reservation(models.Model):
    # cle primaire = id_reserva
    # Relation Many-to-1 (Etudiant maro)
    etudiant=models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    # Arovy ny Chambre, tsy azo fafana raha misy reservation
    chambre=models.ForeignKey(Chambre, on_delete=models.PROTECT) 
    niveau_cible=models.IntegerField(choices=niveau_choix, help_text="Niveau tadiavina")
    date_voulu=models.DateField(help_text="Date tiana hidirana amun'ilay efitra")
    date_creation=models.DateTimeField(auto_now_add=True)
    statut_reserva=models.CharField(max_length=5, choices=statutreserva_choix, default='ATT')
    
    
    # -------------------------------------------------------------------------------------
    #-------calcul period final------------
    
    @property
    def periodfinal_paiement(self):
        # Kajy ny daty farany, mifototra amin'ny difference niveau
        niveau_actu =  self.etudiant.niveauactu_etudiant
        difference_niveau = self.niveau_cible - niveau_actu
        
        # Raha misy difference (tsy mitovy niveau)
        if difference_niveau > 0:
            return self.date_voulu + timedelta(days=365 * (difference_niveau + 1)) 
        # Raha mitovy niveau na ambany (ampiana herintaona fotsiny)
        return self.date_voulu + timedelta(days=365)
    
    
    # -------------------------------------------------------------------------------------
    #-------calcul pour les statu reservation------------
    def check_statut_resrva(self):
        # Ohatra: raha eo anelanelan'ny Septambra sy Novambra no daty
        mois = self.date_voulu.month
        
        if 8 <= mois <= 11 :
            return 'VAL' # Valide raha 08 hatramin'ny 11
        return 'ATT' # En attente raha ivelan'izany
    
    
    # -------------------------------------------------------------------------------------
    #-------mamerina statut reservation isaky ny misy mi-save----------------
    def save(self, *args, **kwargs):
        # Raha mbola en attente, dia kajina indray ny statut alohan'ny save
        if self.statut_reserva=='ATT':
            self.statut_reserva=self.check_statut_resrva()
        
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Reservation #{self.id} - Etudiant: {self.etudiant}"
    






# -------------------------------------------------------------------------------------    
#-----------7. PAIMENT (mifamatotra @Reservation)---------------
# -------------------------------------------------------------------------------------
class Paiement(models.Model):
    # cle primaire: id_paiment
    # Relation Many-to-1 amin'ny Reservation
    reservation=models.ForeignKey(Reservation, on_delete=models.CASCADE)
    montant_paiement=models.DecimalField(max_digits=10, decimal_places=2)
    type_paiement=models.CharField(max_length=5, choices=typepaiement_choix)
    date_paiement=models.DateField(default=timezone.now)
    statut_paiement=models.CharField(max_length=7, choices=statutpaiement_choix,default='IMPAYE')
    
    def calculer_prochain_paiement(self,base_date):
        # Kajy ny daty ho avy
        if self.type_paiement=='MOIS':
            return base_date + timedelta(days=30)
        elif self.type_paiement == 'ANNEE':
            # Raha annuel dia ny daty nidiran'ilay reservation no averina
            return self.reservation.date_voulu
        return timezone.now().date()
    
    def save(self, *args, **kwargs):
        # Loika: raha vaovao ilay Paiement (tsy mbola manana ID), dia ataovy PAYE
        if not self.id: 
            # Mametraka ny daty sy statut voalohany (azo soloina)
            self.date_paiement=self.reservation.date_voulu
            self.statut_paiement='PAYE'
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Paiement {self.montant_paiement} {self.type_paiement} ho an'ny R {self.reservation.id}"