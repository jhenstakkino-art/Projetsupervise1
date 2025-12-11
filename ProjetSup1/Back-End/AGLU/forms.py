from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
# Nampiana MatriculeEnregistre sy Chambre (ho an'ny Reservation)
from .models import User, Etudiant, Reservation, niveau_choix, mention_choix, MatriculeEnregistre, Chambre
from django.utils import timezone # Nampidirina ho an'ny clean_date_voulu

#----------------Formulaire inscription Etudiant-----------
class EtudiantSignUpForm(UserCreationForm):
    # Field ho an'ny User Modely
    email = forms.EmailField(required=True)
    
    # Field ho an'ny Etudiant Modely (Aza adino: ny username an'ny User no Matricule)
    # Tsy maintsy atao ho 'username' ity field ity mba hiasa tsara amin'ny UserCreationForm
    matricule_etudiant = forms.CharField(max_length=20, label='Matricule Etudiant') 
    
    nom_etudiant=forms.CharField(max_length=100, help_text="Anarana")
    prenom_etudiant=forms.CharField(max_length=100, help_text="Fanampin'anarana")
    # Fanitsiana: Nampiasaina forms.ChoiceField ho an'ny Mention sy Niveau
    mention_etudiant=forms.ChoiceField(choices=mention_choix, help_text="Ny mention anao")
    niveauactu_etudiant=forms.ChoiceField(choices=niveau_choix, label="Niveau actuel")
    tel_etudiant=forms.CharField(max_length=20, required=False) # required=False no tokony hampiasaina

    class Meta(UserCreationForm.Meta):
        model = User 
        # Nesorina ny username ao anatin'ny fields eto (soloina ny matricule ao anaty save)
        fields = ('matricule_etudiant', 'email', 'password1', 'password2') 
        
    # Ampiasaina ny clean() mba hanamarinana ny MATRICULE sy ny USERNAME (matricule)
    def clean(self):
        cleaned_data = super().clean()
        matricule = cleaned_data.get('matricule_etudiant')
        
        # 1. Hamarina raha misy ao anaty MatriculeEnregistre ilay Matricule
        try:
            matricule_obj = MatriculeEnregistre.objects.get(matricule=matricule)
        except MatriculeEnregistre.DoesNotExist:
            raise ValidationError("Matricule introuvable dans la liste, inscription non autorisée!")

        # 2. Hamarina raha efa nampiasaina ilay Matricule (is_used=True)
        if matricule_obj.is_used:
             # Fanitsiana: Hanamarina raha efa misy Etudiant manana io matricule io
            if Etudiant.objects.filter(matricule_etudiant=matricule).exists():
                raise ValidationError("Ce matricule a déjà un compte!")
            
            # Tsy tokony ho tonga eto raha toa ka ao anaty liste ary efa nampiasaina.
            # Mety misy olana amin'ny lojika raha misy mitranga toy izao
            raise ValidationError("Matricule déjà utilisé!")


        # Mampiasa ny 'matricule_etudiant' ho an'ny 'username' an'ny Django
        cleaned_data['username'] = matricule
        
        return cleaned_data
        
    def save(self, commit = True):
        # 1. Création de l'objet User
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"] 
        user.is_etudiant = True # ireo role 
        
        # Ny username no soloina ho lasa matricule_etudiant
        user.username = self.cleaned_data.get('matricule_etudiant')

        if commit :
            user.save()
            
            # 2. Création de l'objet Etudiant
            etudiant_data = {
                'user': user,
                'matricule_etudiant': self.cleaned_data.get('matricule_etudiant'),
                'nom_etudiant': self.cleaned_data.get('nom_etudiant'),
                'prenom_etudiant': self.cleaned_data.get('prenom_etudiant'),
                'mention_etudiant': self.cleaned_data.get('mention_etudiant'),
                'niveauactu_etudiant': self.cleaned_data.get('niveauactu_etudiant'),
                'tel_etudiant': self.cleaned_data.get('tel_etudiant'),
            }
            Etudiant.objects.create(**etudiant_data)
            
            # 3. Marquer le matricule comme utilisé (LOGIQUE VAOVAO)
            # Tsy maintsy atao eto ny fanovana ny is_used ho True
            matricule_obj = MatriculeEnregistre.objects.get(matricule=user.username)
            matricule_obj.is_used = True
            matricule_obj.save()
            
        return user
    
    

#----------------Formulaire Modification Etudiant-----------
class EtudiantUpdateForm(forms.ModelForm):
    # Field vaovao ho an'ny fanehoana ny Matricule (readonly)
    matricule_display = forms.CharField(
        label='Matricule Etudiant',
        max_length=20,
        required=False,
        # Nampiasa forms.TextInput mba hanehoana azy ho toy ny text box, miaraka amin'ny readonly
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    
    # Field vaovao ho an'ny fanehoana ny Email (readonly)
    email_display = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = Etudiant
        # Nampidirina ny matricule_display sy email_display ho an'ny fanehoana fotsiny
        fields = ['nom_etudiant','prenom_etudiant','mention_etudiant','niveauactu_etudiant','tel_etudiant'] 
        
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mameno ny sanda ho an'ny field 'matricule_display' sy 'email_display'
        if self.instance:
            self.fields['matricule_display'].initial = self.instance.matricule_etudiant
            self.fields['email_display'].initial = self.instance.user.email

#----------------Formulaire Reservation-----------
class ReservationForm(forms.ModelForm):
    # Nampiana Chambre Model Form eto
    chambre = forms.ModelChoiceField(
        queryset=Chambre.objects.filter(statut_chambre='DISPO'), 
        required=True,
        empty_label="--- Sélectionnez une Chambre Disponible ---",
        label="Chambre Horeservena"
    )
    
    class Meta:
        model = Reservation
        # Nampiasaina ny Field manokana fa tsy ModelChoiceField (jereo etsy ambony)
        fields = ['chambre','niveau_cible','date_voulu']
        widgets = {
            # Mampiasaa date input (tsara tokoa io)
            'date_voulu':forms.DateInput(attrs={'type':'date'}),
        }
        
    def clean_date_voulu(self):
        date_voulu = self.cleaned_data.get('date_voulu')
        if date_voulu < timezone.now().date():
             # Ohatra: tsy azo atao ny mireserva ho an'ny daty efa lasa
            raise ValidationError("Vous ne pouvez pas réserver pour une date passée.")
        return date_voulu