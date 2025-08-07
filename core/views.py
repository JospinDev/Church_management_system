import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse
from datetime import datetime, timedelta,date
from .models import *
from django.db import transaction
from django.utils.timezone import make_aware

@login_required
def membre_export_view(request):
    # Créer la réponse HTTP avec l'en-tête CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="membres_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # Créer le writer CSV
    writer = csv.writer(response)
    
    # Écrire l'en-tête
    writer.writerow(['Nom', 'Prénom', 'Email', 'Téléphone', 'Statut Baptismal','sexe', 'Date d\'adhésion'])
    
    # Appliquer les filtres comme dans la vue liste
    membres = Membre.objects.all()
    search = request.GET.get('search', '')
    statut_baptismal = request.GET.get('statut_baptismal', '')
    
    if search:
        membres = membres.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(email__icontains=search) |
            Q(telephone__icontains=search)
        )
    
    if statut_baptismal:
        membres = membres.filter(statut_baptismal=statut_baptismal)
    
    # Écrire les données
    for membre in membres:
        writer.writerow([
            membre.nom,
            membre.prenom,
            membre.email,
            membre.telephone,
            membre.get_statut_baptismal_display(),
            membre.get_sexe_display(),
            membre.date_adhesion.strftime("%d/%m/%Y") if membre.date_adhesion else ''
        ])
    
    return response
def request_access(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        message = request.POST.get('message')
        with transaction.atomic():
            if DemandeAcces.objects.filter(email=email, est_traitee=False).exists():
                messages.warning(request, "Une demande en attente existe déjà avec cet email.")
                return redirect('requestAccess')
            
            DemandeAcces.objects.create(
                nom_complet=name,
                email=email,
                role_souhaite=role,
                message=message,
            )
            messages.success(request, "Votre demande a été envoyée avec succès.")
            return redirect('requestAccess')

    return render(request, 'core/requestAccess.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'core/login.html')


def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

@login_required
def dashboard_view(request):
    """Tableau de bord principal"""
    # Statistiques générales
    total_membres = Membre.objects.count()
    total_couples = Couple.objects.filter(statut_couple='marie').count()
    programmes_semaine = ProgrammeEglise.objects.filter(
        date_debut__gte=timezone.now(),
        date_debut__lte=timezone.now() + timedelta(days=7)
    ).count()

    
    # Transactions du mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions_mois = TransactionFinanciere.objects.filter(
        date_transaction__gte=debut_mois
    )
    
    offrandes_mois = transactions_mois.filter(type_transaction='offrande').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    depenses_mois = transactions_mois.filter(type_transaction='depense').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Programmes à venir
    programmes_a_venir = ProgrammeEglise.objects.filter(
        date_debut__gte=timezone.now()
    ).order_by('date_debut')[:5]
    
    # Nouveaux membres (30 derniers jours)
    nouveaux_membres = Membre.objects.filter(
        date_adhesion__gte=timezone.now().date() - timedelta(days=30)
    ).order_by('-date_adhesion')[:5]

    nouveaux_membres_2jrs = Membre.objects.filter(
        created_at__gte=timezone.now()- timedelta(days=2)
    ).order_by('-created_at')[:5]
    
    # Nouveau couple (30 derniers jours)
    nouveaux_couples = Couple.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:5]
    
    context = {
        'total_membres': total_membres,
        'total_couples': total_couples,
        'programmes_semaine': programmes_semaine,
        'offrandes_mois': offrandes_mois,
        'depenses_mois': depenses_mois,
        'solde_mois': offrandes_mois - depenses_mois,
        'programmes_a_venir': programmes_a_venir,
        'nouveaux_membres': nouveaux_membres,
        'nouveaux_membres_2jrs': nouveaux_membres_2jrs,
        'nouveaux_couples': nouveaux_couples
    }
    
    return render(request, 'core/index.html', context)

@login_required
def membre_list_view(request):
    """Liste des membres avec recherche et filtres"""
    membres = Membre.objects.all().order_by('nom', 'prenom')
    
    # Statistiques rapides
    total_baptises = membres.filter(statut_baptismal='baptise_eglise').count()
    total_non_baptises = membres.filter(statut_baptismal='non_baptise').count()
    total_autre_eglise = membres.filter(statut_baptismal='baptise_autre_eglise').count()
    # Recherche
    search = request.GET.get('search')
    if search:
        membres = membres.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(email__icontains=search) |
            Q(telephone__icontains=search)
        )
    
    # Filtres
    statut_baptismal = request.GET.get('statut_baptismal')
    if statut_baptismal:
        membres = membres.filter(statut_baptismal=statut_baptismal)
    
    # Pagination
    paginator = Paginator(membres, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'statut_baptismal': statut_baptismal,
        'statut_choices': Membre.STATUT_BAPTISMAL_CHOICES,
        'total_baptises': total_baptises,
        'total_non_baptises': total_non_baptises,
        'total_autre_eglise': total_autre_eglise,
    }
    
    return render(request, 'membre/membre.html', context)

@login_required
def membre_detail_view(request, pk):
    """Détail d'un membre"""
    membre = get_object_or_404(Membre, pk=pk)
    
    # Rôles du membre
    roles = MembreRole.objects.filter(membre=membre).select_related('role')
    
    # Groupes du membre
    groupes = MembreGroupe.objects.filter(membre=membre).select_related('groupe')
    
    # Transactions du membre
    transactions = TransactionFinanciere.objects.filter(membre=membre).order_by('-date_transaction')[:10]
    
    # Dons matériels du membre
    dons_materiels = DonMateriel.objects.filter(membre=membre).order_by('-date_don')[:5]
    
    context = {
        'membre': membre,
        'roles': roles,
        'groupes': groupes,
        'transactions': transactions,
        'dons_materiels': dons_materiels,
    }
    
    return render(request, 'membre/membre_detail.html', context)

@login_required
def membre_create_view(request):
    """Vue pour créer un nouveau membre avec un formulaire HTML personnalisé"""
    errors = {} # Dictionnaire pour stocker les erreurs de validation
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        with transaction.atomic():
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            date_naissance_str = request.POST.get('date_naissance')
            adresse = request.POST.get('adresse')
            telephone = request.POST.get('telephone')
            email = request.POST.get('email')
            statut_baptismal = request.POST.get('statut_baptismal')
            sexe = request.POST.get('sexe')
            date_adhesion_str = request.POST.get('date_adhesion')
            photo_profil_url = request.POST.get('photo_profil_url')

            # --- Validation Manuelle ---
            if not nom:
                errors['nom'] = "Le nom est requis."
            if not prenom:
                errors['prenom'] = "Le prénom est requis."
            
            date_naissance = None
            if not date_naissance_str:
                errors['date_naissance'] = "La date de naissance est requise."
            else:
                try:
                    date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
                except ValueError:
                    errors['date_naissance'] = "Format de date de naissance invalide (YYYY-MM-DD)."
            
            if not adresse:
                errors['adresse'] = "L'adresse est requise."

            # Validation du téléphone (simple, vous pouvez améliorer avec Regex)
            if not telephone:
                errors['telephone'] = "Le numéro de téléphone est requis."
            elif not telephone.strip().replace(' ', '').replace('+', '').isdigit(): # Vérifie si c'est numérique
                errors['telephone'] = "Le numéro de téléphone ne doit contenir que des chiffres et le signe '+'. Example: +25779000000."
            elif not (8 <= len(telephone) <= 15):
                errors['telephone'] = "Le numéro de téléphone doit contenir entre 9 et 15 chiffres."
            
            if not email:
                errors['email'] = "L'adresse email est requise."
            elif '@' not in email or '.' not in email:
                errors['email'] = "Format d'adresse email invalide."
            elif Membre.objects.filter(email=email).exists():
                errors['email'] = "Cet email est déjà utilisé par un autre membre."

            if statut_baptismal not in [choice[0] for choice in Membre.STATUT_BAPTISMAL_CHOICES]:
                errors['statut_baptismal'] = "Statut baptismal invalide."
            if sexe not in [choice[0] for choice in Membre.SEXE_CHOICES]:
                errors['sexe'] = "Sexe is invaalide."
            date_adhesion = None
            if not date_adhesion_str:
                errors['date_adhesion'] = "La date d'adhésion est requise."
            else:
                try:
                    date_adhesion = datetime.strptime(date_adhesion_str, '%Y-%m-%d').date()
                except ValueError:
                    errors['date_adhesion'] = "Format de date d'adhésion invalide (YYYY-MM-DD)."

            # --- Si aucune erreur, sauvegarder le membre ---
            if not errors:
                try:
                    membre = Membre.objects.create(
                        nom=nom,
                        prenom=prenom,
                        date_naissance=date_naissance,
                        adresse=adresse,
                        telephone=telephone,
                        email=email,
                        statut_baptismal=statut_baptismal,
                        sexe=sexe,
                        date_adhesion=date_adhesion,
                        photo_profil_url=photo_profil_url if photo_profil_url else None # Gérer le cas où c'est vide
                    )
                    messages.success(request, f"Le membre {membre.nom_complet} a été ajouté avec succès !")
                    return redirect('membre_list')
                except Exception as e:
                    # Gérer les erreurs de base de données ou autres exceptions inattendues
                    messages.error(request, f"Une erreur inattendue est survenue : {e}")
                    errors['general'] = "Une erreur est survenue lors de l'enregistrement."
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

    # Si GET ou POST avec erreurs, afficher le formulaire
    context = {
        'title': 'Ajouter un nouveau membre',
        'statut_choices': Membre.STATUT_BAPTISMAL_CHOICES, # Pour le champ select
        'sexe_choice':Membre.SEXE_CHOICES, #Pour sexe
        'errors': errors, # Passer les erreurs au template
        # Passer les valeurs soumises pour pré-remplir le formulaire en cas d'erreur
        'nom_value': request.POST.get('nom', ''),
        'prenom_value': request.POST.get('prenom', ''),
        'date_naissance_value': request.POST.get('date_naissance', ''),
        'adresse_value': request.POST.get('adresse', ''),
        'telephone_value': request.POST.get('telephone', ''),
        'email_value': request.POST.get('email', ''),
        'statut_baptismal_value': request.POST.get('statut_baptismal', 'non_baptise'), # Valeur par défaut
        'sexe_value':request.POST.get('sexe','Masculin'),
        'date_adhesion_value': request.POST.get('date_adhesion', ''),
        'photo_profil_url_value': request.POST.get('photo_profil_url', ''),
    }
    return render(request, 'membre/membre_form.html', context)

@login_required
def membre_update_view(request, pk):
    """Vue pour modifier un membre existant"""
    # Récupérer le membre existant
    membre = get_object_or_404(Membre, pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
        # Traitement du formulaire soumis
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            date_naissance = request.POST.get('date_naissance')
            date_adhesion = request.POST.get('date_adhesion')
            statut_baptismal = request.POST.get('statut_baptismal')
            sexe = request.POST.get('sexe')
            is_active = request.POST.get('status') == 'on'
            
            # Mettre à jour les données du membre
            membre.nom = nom
            membre.prenom = prenom
            membre.email = email
            membre.telephone = telephone
            membre.adresse = adresse
            membre.date_naissance = date_naissance
            membre.date_adhesion = date_adhesion
            membre.statut_baptismal = statut_baptismal
            membre.sexe = sexe
            membre.is_active = is_active
            
            try:
                membre.save()
                messages.success(request, "Le membre a été modifié avec succès!")
                return redirect('membre_detail', pk=membre.pk)
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification: {str(e)}")
    
    # Préparer le contexte avec les données existantes
    context = {
        'membre': membre,
        'form': {
            'nom': {'value': membre.nom},
            'prenom': {'value': membre.prenom},
            'email': {'value': membre.email},
            'telephone': {'value': membre.telephone},
            'adresse': {'value': membre.adresse},
            'date_naissance': {'value': membre.date_naissance},
            'date_adhesion': {'value': membre.date_adhesion},
            'statut_baptismal': {'value': membre.statut_baptismal},
            'sexe': {'value':membre.sexe},
            'status': {'value': membre.is_active},
        }
    }
    
    return render(request, 'membre/membre_update.html', context)

@login_required
def membre_delete_view(request, pk):
    membre = get_object_or_404(Membre, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                membre.delete()
                messages.success(request, "Le couple a été supprimé avec succès!")
                return redirect('membre_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('membre_detail', pk=pk)
    
    return redirect('membre_list')

@login_required
def couple_list_view(request):
    """Liste des couples"""
    couples = Couple.objects.all().select_related('membre_mari', 'membre_femme').order_by('-date_mariage')
    
     # Statistiques
    total_maries = couples.filter(statut_couple='marie').count()
    total_fiances = couples.filter(statut_couple='fiance').count()
    debut_mois = timezone.now().replace(day=1)
    mariages_ce_mois = couples.filter(date_mariage__gte=debut_mois).count()

    # Filtre par statut
    statut = request.GET.get('statut')
    if statut:
        couples = couples.filter(statut_couple=statut)
    
    # Pagination
    paginator = Paginator(couples, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'statut': statut,
        'statut_choices': Couple.STATUT_CHOICES,
         # Statistiques
        'total_maries': total_maries,
        'total_fiances': total_fiances,
        'mariages_ce_mois': mariages_ce_mois,
    }
    
    return render(request, 'couple/couples.html', context)

@login_required
def couple_detail_view(request, pk):
    """Détail d'un couple"""
    couple = get_object_or_404(Couple, pk=pk)
    
    # Programmes de mariage du couple
    programmes_mariage = ProgrammeMariage.objects.filter(couple=couple).order_by('-date_debut')
    
    context = {
        'couple': couple,
        'programmes_mariage': programmes_mariage,
    }
    
    return render(request, 'couple/detail.html', context)

@login_required
def couple_form_view(request, pk=None):
    """Vue pour créer ou modifier un couple"""
    couple = None
    if pk:
        couple = get_object_or_404(Couple, pk=pk)
    
    # Get all male and female members
    membres_hommes = Membre.objects.filter(sexe='M').order_by('nom', 'prenom')
    membres_femmes = Membre.objects.filter(sexe='F').order_by('nom', 'prenom')
    
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'membre_mari_id': request.POST.get('mari'),
                'membre_femme_id': request.POST.get('femme'),
                'statut_couple': request.POST.get('statut_couple'),
                'date_mariage': request.POST.get('date_mariage') or None,
            }
            
            # Validate required fields
            if not data['membre_mari_id'] or not data['membre_femme_id'] or not data['statut_couple']:
                messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                return redirect('couple_create')
            
            if couple:  # Update existing couple
                for key, value in data.items():
                    setattr(couple, key, value)
                couple.save()
                messages.success(request, "Le couple a été modifié avec succès!")
            else:  # Create new couple
                couple = Couple.objects.create(**data)
                messages.success(request, "Le couple a été créé avec succès!")
            
            return redirect('couple_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")
    
    context = {
        'couple': couple,
        'membres_hommes': membres_hommes,
        'membres_femmes': membres_femmes,
        'statut_choices': Couple.STATUT_CHOICES,
        'form': {
            'mari': {'value': couple.membre_mari_id if couple else None},
            'femme': {'value': couple.membre_femme_id if couple else None},
            'statut_couple': {'value': couple.statut_couple if couple else None},
            'date_mariage': {'value': couple.date_mariage if couple else None},
        }
    }
    
    return render(request, 'couple/couples_form.html', context)

@login_required
def couple_delete_view(request, pk):
    couple = get_object_or_404(Couple, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                couple.delete()
                messages.success(request, "Le couple a été supprimé avec succès!")
                return redirect('couple_list')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('couple_detail', pk=pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('couple_detail', pk=pk)
    
    return redirect('couple_detail', pk=pk)



def combine_date_time(date_str, time_str):
    """Combine date and time strings into a timezone-aware datetime.
       If date is empty, use today's date."""
    if not date_str or not time_str:
        return None
    dt_str = f"{date_str} {time_str}"
    dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    return make_aware(dt_obj)

@login_required
def programme_eglise_list_view(request):
    """Liste des programmes d'église"""
    programmes = ProgrammeEglise.objects.all().order_by('-date_debut')
    all_programmes = ProgrammeEglise.objects.all()

    # Filtres
    categorie = request.GET.get('categorie')
    if categorie:
        all_programmes = all_programmes.filter(categorie=categorie)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        all_programmes = all_programmes.filter(
            Q(titre__icontains=search) |
            Q(description__icontains=search) |
            Q(lieu__icontains=search)
        )
    stats = {
        'programmes': programmes,
        'total': all_programmes.count(),
        'culte': all_programmes.filter(categorie='culte').count(),
        'reunion_priere': all_programmes.filter(categorie='reunion_priere').count(),
        'etude_biblique': all_programmes.filter(categorie='etude_biblique').count(),
        'evenement_special': all_programmes.filter(categorie='evenement_special').count(),
        'formation': all_programmes.filter(categorie='formation').count(),
        'jeunesse': all_programmes.filter(categorie='jeunesse').count(),
        'enfants': all_programmes.filter(categorie='enfants').count(),
    }

    programmes = sorted(
        all_programmes,
        key=lambda p: p.next_date or timezone.make_aware(timezone.datetime.max)
    )
    # Pagination
    paginator = Paginator(programmes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'categorie': categorie,
        'categorie_choices': ProgrammeEglise.CATEGORIE_CHOICES,
        'stats':stats
    }
    
    return render(request, 'programmes/programme.html', context)

@login_required
def programme_eglise_detail_view(request, pk):
    """Détail d'un programme d'église"""
    programme = get_object_or_404(ProgrammeEglise, pk=pk)
    
    context = {
        'programme': programme,
    }
    
    return render(request, 'programmes/detail.html', context)

@login_required
def programme_eglise_create_view(request):
    if request.method == 'POST':
        
        data = {
            'titre': request.POST.get('titre'),
            'description': request.POST.get('description'),
            'date_debut': request.POST.get('date_debut') or None,
            'heure_debut': request.POST.get('heure_debut') or None,
            'date_fin': request.POST.get('date_fin') or None,
            'heure_fin': request.POST.get('heure_fin') or None,
            'lieu': request.POST.get('lieu'),
            'categorie': request.POST.get('categorie'),
            'recurrence': request.POST.get('recurrence')
        }
        programme = ProgrammeEglise.objects.create(**data)
        messages.success(request, "Le programme a été créé avec succès!")
        return redirect('programme_detail', pk=programme.pk)

    return render(request, 'programmes/form.html', {
        'categorie_choices': ProgrammeEglise.CATEGORIE_CHOICES,
        'recurrence_choices': ProgrammeEglise.RECURRENCE_CHOICES,
    })

@login_required
def programme_eglise_update_view(request, pk):
    programme = get_object_or_404(ProgrammeEglise, pk=pk)

    if request.method == 'POST':
        try:
            programme.titre = request.POST.get('titre')
            programme.description = request.POST.get('description')
            programme.date_debut = request.POST.get('date_debut'),
            programme.heure_debut = request.POST.get('heure_debut')
            programme.date_fin = request.POST.get('date_fin'),
            programme.heure_fin = request.POST.get('heure_fin')
            programme.lieu = request.POST.get('lieu')
            programme.categorie = request.POST.get('categorie')
            programme.recurrence = request.POST.get('recurrence')
            programme.save()

            messages.success(request, "Le programme a été modifié avec succès!")
            return redirect('programme_detail', pk=programme.pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")

    return render(request, 'programmes/form.html', {
        'programme': programme,
        'categorie_choices': ProgrammeEglise.CATEGORIE_CHOICES,
        'recurrence_choices': ProgrammeEglise.RECURRENCE_CHOICES
    })

@login_required
def programme_eglise_delete_view(request, pk):
    """Supprimer un programme d'église"""
    programme = get_object_or_404(ProgrammeEglise, pk=pk)
    
    if request.method == 'POST':
        try:
            programme.delete()
            messages.success(request, "Le programme a été supprimé avec succès!")
            return redirect('programme_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('programme_detail', pk=pk)
    
    context = {
        'programme': programme
    }
    
    return render(request, 'programmes/delete_confirm.html', context)

@login_required
def programme_eglise_calendar_view(request):
    """Vue calendrier des programmes"""
    # Récupérer tous les programmes
    programmes = ProgrammeEglise.objects.all()
    
    # Filtrer par catégorie si spécifiée
    categorie = request.GET.get('categorie')
    print(f"Catégorie reçue: {categorie}")  # Debug
    
    if categorie:
        programmes = programmes.filter(categorie=categorie)
        print(f"Nombre de programmes filtrés: {programmes.count()}")  # Debug
    
    # Statistiques par catégorie (toujours calculées sur tous les programmes)
    all_programmes = ProgrammeEglise.objects.all()
    stats = {
        cat[0]: all_programmes.filter(categorie=cat[0]).count()
        for cat in ProgrammeEglise.CATEGORIE_CHOICES
    }
    
    # Convertir les programmes en événements pour le calendrier
    events = []
    for prog in programmes:
        color = {
            'culte': '#9333ea',  # purple-600
            'reunion_priere': '#16a34a',  # green-600
            'etude_biblique': '#ca8a04',  # yellow-600
            'evenement_special': '#dc2626',  # red-600
            'formation': '#2563eb',  # blue-600
            'jeunesse': '#db2777',  # pink-600
            'enfants': '#0891b2',  # cyan-600
        }.get(prog.categorie, '#4b5563')
        
        events.append({
            'id': prog.pk,
            'title': prog.titre,
            'start': prog.date_debut.isoformat() if prog.date_debut else None,
            'end': prog.date_fin.isoformat() if prog.date_fin else None,
            'backgroundColor': color,
            'borderColor': color,
            'url': reverse('programme_detail', args=[prog.pk]),
            'extendedProps': {
                'categorie': prog.categorie,
                'lieu': prog.lieu or '',
                'description': prog.description or '',
                'editUrl': reverse('programme_update', args=[prog.pk])
            }
        })
    
    print(f"Nombre d'événements générés: {len(events)}")  # Debug
    
    context = {
        'events': json.dumps(events),
        'categorie_choices': ProgrammeEglise.CATEGORIE_CHOICES,
        'categorie': categorie,
        'stats': stats,
    }
    return render(request, 'programmes/calendar.html', context)

@login_required
def groupe_list_view(request):
    """Liste des groupes"""
    groupes = Groupe.objects.annotate(
        nombre_membres=Count('membres')
    ).order_by('nom_groupe')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        groupes = groupes.filter(
            Q(nom_groupe__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'groupes': groupes,
        'search': search,
    }
    
    return render(request, 'groupes/groupe.html', context)

@login_required
def groupe_detail_view(request, pk):
    """Détail d'un groupe"""
    groupe = get_object_or_404(Groupe, pk=pk)
    
    # Membres du groupe
    membres_groupe = MembreGroupe.objects.filter(groupe=groupe).select_related('membre')
    
    context = {
        'groupe': groupe,
        'membres_groupe': membres_groupe,
    }
    
    return render(request, 'groupes/detail.html', context)

@login_required
def transaction_list_view(request):
    """Liste des transactions financières"""
    transactions = TransactionFinanciere.objects.all().select_related('membre').order_by('-date_transaction')
    
    # Filtres
    type_transaction = request.GET.get('type')
    if type_transaction:
        transactions = transactions.filter(type_transaction=type_transaction)
    
    categorie_depense = request.GET.get('categorie')
    if categorie_depense:
        transactions = transactions.filter(categorie_depense=categorie_depense)
    
    # Recherche par membre
    membre = request.GET.get('membre')
    if membre:
        transactions = transactions.filter(membre__id=membre)
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculs pour les totaux
    total_offrandes = transactions.filter(type_transaction='offrande').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    total_depenses = transactions.filter(type_transaction='depense').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'type_transaction': type_transaction,
        'categorie_depense': categorie_depense,
        'membre': membre,
        'type_choices': TransactionFinanciere.TYPE_CHOICES,
        'categorie_choices': TransactionFinanciere.CATEGORIE_DEPENSE_CHOICES,
        'total_offrandes': total_offrandes,
        'total_depenses': total_depenses,
        'solde': total_offrandes - total_depenses,
        'tous_membres': Membre.objects.all().order_by('nom', 'prenom'),
    }
    
    return render(request, 'finances/transactions.html', context)

@login_required
def don_materiel_list_view(request):
    """Liste des dons matériels"""
    dons = DonMateriel.objects.all().select_related('membre').order_by('-date_don')
    
    # Filtres
    statut = request.GET.get('statut')
    if statut:
        dons = dons.filter(statut_don=statut)
    
    membre = request.GET.get('membre')
    if membre:
        dons = dons.filter(membre__id=membre)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        dons = dons.filter(description_objet__icontains=search)
    
    # Pagination
    paginator = Paginator(dons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'statut': statut,
        'membre': membre,
        'search': search,
        'statut_choices': DonMateriel.STATUT_CHOICES,
        'tous_membres': Membre.objects.all().order_by('nom', 'prenom'),
    }
    
    return render(request, 'dons/list.html', context)

@login_required
def role_list_view(request):
    """Liste des rôles"""
    roles = Role.objects.annotate(
        nombre_membres=Count('membre_roles')
    ).order_by('nom_role')
    
    context = {
        'roles': roles,
    }
    
    return render(request, 'roles/list.html', context)

@login_required
def role_detail_view(request, pk):
    """Détail d'un rôle"""
    role = get_object_or_404(Role, pk=pk)
    
    # Membres ayant ce rôle
    membres_role = MembreRole.objects.filter(role=role).select_related('membre')
    
    context = {
        'role': role,
        'membres_role': membres_role,
    }
    
    return render(request, 'roles/detail.html', context)

@login_required
def statistiques_view(request):
    """Page des statistiques générales"""
    # Statistiques membres
    total_membres = Membre.objects.count()
    membres_baptises = Membre.objects.filter(statut_baptismal='baptise_eglise').count()
    nouveaux_membres_30j = Membre.objects.filter(
        date_adhesion__gte=timezone.now().date() - timedelta(days=30)
    ).count()
    
    # Statistiques couples
    total_couples = Couple.objects.count()
    couples_maries = Couple.objects.filter(statut_couple='marie').count()
    couples_fiances = Couple.objects.filter(statut_couple='fiance').count()
    
    # Statistiques financières (année courante)
    debut_annee = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions_annee = TransactionFinanciere.objects.filter(date_transaction__gte=debut_annee)
    
    total_offrandes = transactions_annee.filter(type_transaction='offrande').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    total_depenses = transactions_annee.filter(type_transaction='depense').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Statistiques par groupe
    groupes_stats = Groupe.objects.annotate(
        nombre_membres=Count('membres')
    ).order_by('-nombre_membres')[:5]
    
    context = {
        'total_membres': total_membres,
        'membres_baptises': membres_baptises,
        'pourcentage_baptises': round((membres_baptises / total_membres * 100), 2) if total_membres > 0 else 0,
        'nouveaux_membres_30j': nouveaux_membres_30j,
        'total_couples': total_couples,
        'couples_maries': couples_maries,
        'couples_fiances': couples_fiances,
        'total_offrandes': total_offrandes,
        'total_depenses': total_depenses,
        'solde_annee': total_offrandes - total_depenses,
        'groupes_stats': groupes_stats,
    }
    
    return render(request, 'statistiques.html', context)

@login_required
def programme_mariage_list_view(request):
    """Liste des programmes de mariage"""
    programmes = ProgrammeMariage.objects.all().select_related('couple').order_by('-date_debut')
    
    # Filtres
    statut = request.GET.get('statut')
    if statut:
        programmes = programmes.filter(statut=statut)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        programmes = programmes.filter(
            Q(titre__icontains=search) |
            Q(description__icontains=search) |
            Q(lieu__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(programmes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'statut': statut,
        'statut_choices': ProgrammeMariage.STATUT_CHOICES,
    }
    
    return render(request, 'programme_mariage/list.html', context)

@login_required
def programme_mariage_detail_view(request, pk):
    """Détail d'un programme de mariage"""
    programme = get_object_or_404(ProgrammeMariage, pk=pk)
    
    context = {
        'programme': programme,
    }
    
    return render(request, 'programme_mariage/detail.html', context)

@login_required
def programme_mariage_create_view(request, couple_pk):
    """Créer un programme de mariage"""
    couple = get_object_or_404(Couple, pk=couple_pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = {
                    'couple': couple,
                    'titre': request.POST.get('titre'),
                    'description': request.POST.get('description'),
                    'date_debut': request.POST.get('date_debut'),
                    'date_fin': request.POST.get('date_fin'),
                    'lieu': request.POST.get('lieu'),
                    'statut': request.POST.get('statut', 'planifie')
                }
                
                programme = ProgrammeMariage.objects.create(**data)
                messages.success(request, "Le programme a été créé avec succès!")
                return redirect('couple_detail', pk=couple.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création: {str(e)}")
    
    context = {
        'couple': couple,
        'statut_choices': ProgrammeMariage.STATUT_CHOICES
    }
    
    return render(request, 'programme_mariage/form.html', context)

@login_required
def programme_mariage_update_view(request, pk):
    """Modifier un programme de mariage"""
    programme = get_object_or_404(ProgrammeMariage, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                programme.titre = request.POST.get('titre')
                programme.description = request.POST.get('description')
                programme.date_debut = request.POST.get('date_debut')
                programme.date_fin = request.POST.get('date_fin')
                programme.lieu = request.POST.get('lieu')
                programme.statut = request.POST.get('statut')
                programme.save()
                
                messages.success(request, "Le programme a été modifié avec succès!")
                return redirect('programme_mariage_detail', pk=programme.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
    
    context = {
        'programme': programme,
        'statut_choices': ProgrammeMariage.STATUT_CHOICES
    }
    
    return render(request, 'programme_mariage/form.html', context)

@login_required
def programme_mariage_couple_select(request):
    """Sélection du couple pour créer un programme"""
    couples = Couple.objects.all().select_related('membre_mari', 'membre_femme').order_by('-date_mariage')
    
    context = {
        'couples': couples,
        'title': 'Sélectionner un couple'
    }
    
    return render(request, 'programme_mariage/select_couple.html', context)

@login_required
def programme_mariage_delete_view(request, pk):
    """Supprimer un programme de mariage"""
    programme = get_object_or_404(ProgrammeMariage, pk=pk)
    couple_pk = programme.couple.pk
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                programme.delete()
                messages.success(request, "Le programme a été supprimé avec succès!")
                return redirect('couple_detail', pk=couple_pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('programme_mariage_detail', pk=pk)
    
    context = {
        'programme': programme
    }
    
    return render(request, 'programme_mariage/delete_confirm.html', context)