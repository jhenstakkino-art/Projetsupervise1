from django.shortcuts import render 
from django.http import HttpResponse # Tena ilaina ho an'ny index_view
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError 

# --- FANAFARANA AVY AMIN'NY MODELY SY FORMS ---
# Tokony ho efa voafaritra ao anaty models.py sy forms.py ireo rehetra ireo
from .models import (
    User, Etudiant, Chambre, Reservation, Paiement, 
    mention_choix, niveau_choix, MatriculeEnregistre, 
    statutpaiement_choix, typepaiement_choix
)
from .forms import EtudiantSignUpForm, ReservationForm








# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------1. FRONT-END ROOT VIEW---------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

def index_view(request):
    return render(request, 'AGLU/index.html') 




# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 2. SERIALIZERS -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class EtudiantSerializer(serializers.ModelSerializer):
    """ Serializer ho an'ny fanehoana sy fanovana ny profil Etudiant. """
    email = serializers.ReadOnlyField(source='user.email')
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Etudiant
        fields = (
            'id', 'matricule_etudiant', 'nom_etudiant', 'prenom_etudiant', 
            'mention_etudiant', 'niveauactu_etudiant', 'tel_etudiant', 
            'email', 'username'
        )
        read_only_fields = ['matricule_etudiant'] 

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
class ChambreSerializer(serializers.ModelSerializer):
    """ Serializer ho an'ny fanehoana ny Chambre. """
    class Meta:
        model = Chambre
        fields = '__all__'

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------        
class ReservationSerializer(serializers.ModelSerializer):
    """ Serializer ho an'ny fanehoana sy famoronana Reservation. """
    chambre_id = serializers.IntegerField(source='chambre.id', read_only=True)
    etudiant_matricule = serializers.CharField(source='etudiant.matricule_etudiant', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'etudiant', 'chambre', 'chambre_id', 'etudiant_matricule', 
            'date_creation', 'statut_reserva', 'niveau_cible', 
            'date_voulu', 'periodfinal_paiement'
        ]
        read_only_fields = ['etudiant', 'date_creation', 'statut_reserva', 'periodfinal_paiement']

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------        
class PaiementSerializer(serializers.ModelSerializer):
    """ Serializer ho an'ny famoronana Paiement vaovao sy fanehoana ny Paiement efa misy. """
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True)
    etudiant_matricule = serializers.CharField(source='etudiant.matricule_etudiant', read_only=True)
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'reservation', 'reservation_id', 'etudiant', 'etudiant_matricule',
            'montant_paiement', 'mode_paiement', 'date_paiement', 'statut_paiement',
            'ref_transaction'
        ]
        # Ny etudiant dia raisina avy amin'ny mpampiasa tafiditra, 
        # fa ny reservation kosa dia tsy maintsy apetraky ny mpampiasa rehefa mamorona.
        read_only_fields = ['etudiant', 'date_paiement', 'statut_paiement']

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
class MatriculeEnregistreSerializer(serializers.ModelSerializer):
    """ Serializer ho an'ny fitantanan-draharaha ny matricules voasoratra (Admin). """
    class Meta:
        model = MatriculeEnregistre
        fields = '__all__'
        read_only_fields = ('is_used',)










# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 3. API AUTHENTICATION (LOGIN / SIGNUP) -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class EtudiantSignUpSerializer(serializers.Serializer):
    """ Serializer mampiasa ny EtudiantSignUpForm mba hanamarinana sy hamoronana. """
    matricule_etudiant = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password1 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    nom_etudiant = serializers.CharField(max_length=100)
    prenom_etudiant = serializers.CharField(max_length=100)
    mention_etudiant = serializers.ChoiceField(choices=mention_choix)
    niveauactu_etudiant = serializers.ChoiceField(choices=niveau_choix)
    tel_etudiant = serializers.CharField(max_length=20, required=False)

    def validate(self, data):
        # Fanamarinana ny tenimiafina sy ny EtudiantSignUpForm
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Les deux mots de passe ne correspondent pas."})
            
        form = EtudiantSignUpForm(data=data)
        if not form.is_valid():
            errors = {k: v[0] for k, v in form.errors.items()}
            raise serializers.ValidationError(errors)
        
        self.form = form
        return data

    def create(self, validated_data):
        user = self.form.save(commit=True) 
        token, created = Token.objects.get_or_create(user=user)
        return user, token.key
        
@api_view(['POST'])
@permission_classes([AllowAny])
def etudiant_signup_api(request):
    """ API ho an'ny fisoratana anarana Etudiant. """
    serializer = EtudiantSignUpSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user, token = serializer.create(serializer.validated_data)
            return Response({
                'message': "L'étudiant a été inscrit(e) avec succès.",
                'token': token,
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"error": "Ce matricule ou cet e-mail est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Une erreur est survenue lors de l'inscription :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
class CustomAuthToken(ObtainAuthToken):
    """ API ho an'ny fidirana sy fahazoana Token. """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        if not user.is_etudiant:
            return Response({'error': "Accès refusé! Ce compte n'est pas un compte Étudiant."}, status=status.HTTP_403_FORBIDDEN)
            
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'is_etudiant': user.is_etudiant,
            'is_admin': user.is_admin,
            'username': user.username
        })











# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 4. API PROFILE (ETUDIANT) -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class EtudiantProfileView(APIView):
    """ GET: Raiso ny profil. PUT: Ovao ny profil an'ny Etudiant efa tafiditra. """
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        try:
            return Etudiant.objects.get(user=user)
        except Etudiant.DoesNotExist:
            raise ObjectDoesNotExist("Aucun étudiant ne correspond à cet utilisateur.")

    def get(self, request, format=None):
        try:
            etudiant = self.get_object(request.user)
            serializer = EtudiantSerializer(etudiant)
            return Response(serializer.data)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Une erreur est survenue lors de la récupération du profil :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, format=None):
        try:
            etudiant = self.get_object(request.user)
            serializer = EtudiantSerializer(etudiant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Problème lors de la mise à jour du profil : " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)











# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 5. API CHAMBRE (READ-ONLY) -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chambre_list_api(request):
    """ Mamerina ny lisitry ny Efitrano misy. """
    chambres = Chambre.objects.filter(statut_chambre='DISPO')
    serializer = ChambreSerializer(chambres, many=True)
    return Response(serializer.data)











# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 6. API RESERVATION -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class ReservationListCreateAPIView(APIView):
    """ GET: Lisitry ny reservation an'ny mpianatra. POST: Mamorona reservation vaovao. """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            reservations = Reservation.objects.filter(etudiant=etudiant)
            serializer = ReservationSerializer(reservations, many=True)
            return Response(serializer.data)
        except Etudiant.DoesNotExist:
            return Response({"error": "Étudiant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Problème lors de l'accès à la réservation :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            
            # Fanamarinana mialoha: Etudiant iray = Reservation iray MANDRITRA NY MANDRAY
            if Reservation.objects.filter(etudiant=etudiant, statut_reserva='EN_ATTENTE').exists():
                 return Response({"error": "Vous avez déjà une réservation EN_ATTENTE. Une seule est autorisée à la fois"}, status=status.HTTP_400_BAD_REQUEST)
                 
            data = request.data.copy()
            data['etudiant'] = etudiant.id 
            
            form = ReservationForm(data=data)
            
            if form.is_valid():
                # Fanamarinana fanampiny: Hita ve ny Chambre?
                chambre_id = form.cleaned_data.get('chambre').id
                try:
                    chambre = Chambre.objects.get(id=chambre_id, statut_chambre='DISPO')
                except Chambre.DoesNotExist:
                    return Response({"error": "Chambre introuvable ou déjà prise."}, status=status.HTTP_400_BAD_REQUEST)
                    
                reservation = form.save(commit=False)
                reservation.etudiant = etudiant
                reservation.save() 
                
                # Manova ny statut an'ny Chambre ho 'EN_COURS'
                chambre.statut_chambre = 'EN_COURS'
                chambre.save()
                
                serializer = ReservationSerializer(reservation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                errors = {k: v[0] for k, v in form.errors.items()}
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Etudiant.DoesNotExist:
            return Response({"error": "Problème interne : L'étudiant n'a pas été trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Problème lors de la création de la réservation :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)











# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 7. API ADMIN (CRUD MATRICULE) -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class MatriculeEnregistreAdminView(APIView):
    """ CRUD ho an'ny Matricules voasoratra (Vue Admin). """
    permission_classes = [IsAuthenticated] # Mbola mila manampy IsAdminUser eto

    def get_object(self, pk):
        try:
            return MatriculeEnregistre.objects.get(pk=pk)
        except MatriculeEnregistre.DoesNotExist:
            raise ObjectDoesNotExist("Aucun Matricule Enregistré ne correspond à cet ID.")
            
    # GET: Lisitra na antsipiriany
    def get(self, request, pk=None, format=None):
        if pk:
            try:
                matricule = self.get_object(pk)
                serializer = MatriculeEnregistreSerializer(matricule)
                return Response(serializer.data)
            except ObjectDoesNotExist as e:
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        matricules = MatriculeEnregistre.objects.all()
        serializer = MatriculeEnregistreSerializer(matricules, many=True)
        return Response(serializer.data)

    # POST: Mamorona matricule vaovao
    def post(self, request, format=None):
        serializer = MatriculeEnregistreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT: Manova (mila PK)
    def put(self, request, pk, format=None):
        try:
            matricule = self.get_object(pk)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = MatriculeEnregistreSerializer(matricule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Mamafa (mila PK)
    def delete(self, request, pk, format=None):
        try:
            matricule = self.get_object(pk)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        matricule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)











# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# ----------------- 8. API PAIEMENT -----------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

class PaiementListCreateAPIView(APIView):
    """ GET: Lisitry ny paiement-n'ny Etudiant. POST: Manamafy Paiement. """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """ Raiso ny lisitry ny paiement rehetra nataon'ity Etudiant ity. """
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            paiements = Paiement.objects.filter(etudiant=etudiant).order_by('-date_paiement')
            serializer = PaiementSerializer(paiements, many=True)
            return Response(serializer.data)
        except Etudiant.DoesNotExist:
            return Response({"error": "Étudiant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Une erreur est survenue lors de la récupération du paiement :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        """ Manamafy Paiement vaovao. """
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            
            # Hanamboatra ny data ho an'ny serializer
            data = request.data.copy()
            data['etudiant'] = etudiant.id # Ataovy automatique ny Etudiant ID
            
            # Fanamarinana manokana ho an'ny Paiement
            serializer = PaiementSerializer(data=data)
            if serializer.is_valid():
                reservation_id = serializer.validated_data.get('reservation').id
                montant_paiement = serializer.validated_data.get('montant_paiement')
                type_paiement = serializer.validated_data.get('type_paiement')
                
                # 1. Tadiavo ny Reservation EN_ATTENTE mifanaraka aminy
                try:
                    reservation = Reservation.objects.get(
                        id=reservation_id, 
                        etudiant=etudiant, 
                        statut_reserva='EN_ATTENTE'
                    )
                except Reservation.DoesNotExist:
                    return Response({"error": "Réservation EN_ATTENTE associée introuvable."}, status=status.HTTP_404_NOT_FOUND)
                    
                # 2. Fanamarinana Montant (Lojika tsotra: mifanaraka amin'ny saram-pidirana)
                # Tsy maintsy apetrakao ao anaty settings na modely ny saram-pidirana tena izy
                SARA_FIDIIRANA = 100000 # Ohatra: 100 000 Ar
                if montant_paiement < SARA_FIDIIRANA:
                    return Response({"error": f"Le montant est insuffisant. Il devrait être d'au moins {SARA_FIDIIRANA} Ar."}, status=status.HTTP_400_BAD_REQUEST)
                
                # 3. Mamorona ny Paiement
                paiement = Paiement.objects.create(
                    reservation=reservation,
                    etudiant=etudiant,
                    montant_paiement=montant_paiement,
                    type_paiement=type_paiement,
                    statut_paiement='VALIDE' # Lojika tsotra: raisina fa VALIDE avy hatrany
                )
                
                # 4. Manova ny Statut an'ny Reservation
                reservation.statut_reserva = 'PAYE'
                reservation.save()
                
                # 5. Mamerina ny valiny
                response_serializer = PaiementSerializer(paiement)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Etudiant.DoesNotExist:
            return Response({"error": "Étudiant introuvable (Problème interne)."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Problème lors du paiement :" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)