# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta,datetime

class Membre(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    STATUT_BAPTISMAL_CHOICES = [
        ('baptise_eglise', 'Baptisé Église'),
        ('non_baptise', 'Non Baptisé'),
        ('baptise_autre_eglise', 'Baptisé Autre Église'),
    ]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    is_active = models.BooleanField(default=True)
    adresse = models.TextField()
    telephone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Numéro de téléphone invalide')]
    )
    email = models.EmailField(unique=True)
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        null=True,
        blank=True,
        verbose_name="Sexe"
    )
    statut_baptismal = models.CharField(
        max_length=25,
        choices=STATUT_BAPTISMAL_CHOICES,
        default='non_baptise'
    )
    date_adhesion = models.DateField()
    photo_profil_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Role(models.Model):
    ROLES_CHOICES = [
        ('pasteur', 'Pasteur'),
        ('diacre', 'Diacre'),
        ('protocole', 'Protocole'),
        ('evangeliste', 'Évangéliste'),
        ('membre_standard', 'Membre Standard'),
        ('administrateur', 'Administrateur'),
        ('tresorier', 'Trésorier'),
        ('coordinateur_programme', 'Coordinateur de Programme'),
    ]
    
    nom_role = models.CharField(max_length=50, choices=ROLES_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        ordering = ['nom_role']
    
    def __str__(self):
        return self.get_nom_role_display()


class MembreRole(models.Model):
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='membre_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='membre_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attribution de Rôle"
        verbose_name_plural = "Attributions de Rôles"
        unique_together = ['membre', 'role']
    
    def __str__(self):
        return f"{self.membre.nom_complet} - {self.role.get_nom_role_display()}"


class CompteUtilisateur(AbstractUser):
    membre = models.OneToOneField(
        Membre, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='compte_utilisateur'
    )
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compte Utilisateur"
        verbose_name_plural = "Comptes Utilisateurs"
    
    def __str__(self):
        if self.membre:
            return f"{self.username} ({self.membre.nom_complet})"
        return self.username


class Couple(models.Model):
    STATUT_CHOICES = [
        ('marie', 'Marié'),
        ('fiance', 'Fiancé'),
    ]
    
    membre_mari = models.ForeignKey(
        Membre, 
        on_delete=models.CASCADE, 
        related_name='couples_mari'
    )
    membre_femme = models.ForeignKey(
        Membre, 
        on_delete=models.CASCADE, 
        related_name='couples_femme'
    )
    is_active = models.BooleanField(default=True)
    statut_couple = models.CharField(max_length=10, choices=STATUT_CHOICES)
    date_mariage = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Couple"
        verbose_name_plural = "Couples"
        unique_together = ['membre_mari', 'membre_femme']
    
    def __str__(self):
        return f"{self.membre_mari.nom_complet} & {self.membre_femme.nom_complet}"
    
    def clean(self):
        
        # Si le couple existe déjà (modification)
        if self.pk:
            # Vérifie s'il y a des programmes actifs
            programmes_actifs = self.programmes_mariage.filter(
                statut__in=['planifie', 'en_cours']
            ).exists()
            
            if programmes_actifs:
                raise ValidationError(
                    "Impossible de supprimer ce couple car il a des programmes de mariage actifs. "
                    "Veuillez d'abord annuler ou terminer tous les programmes associés."
                )
    
    def delete(self, *args, **kwargs):
        self.clean()
        super().delete(*args, **kwargs)


class ProgrammeMariage(models.Model):
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='programmes_mariage')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=200, blank=True, null=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifie')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Programme de Mariage"
        verbose_name_plural = "Programmes de Mariage"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.couple}"
    
    @property
    def is_actif(self):
        return self.statut in ['planifie', 'en_cours']


class ProgrammeEglise(models.Model):
    CATEGORIE_CHOICES = [
        ('culte', 'Culte'),
        ('reunion_priere', 'Réunion de prière'),
        ('etude_biblique', 'Étude biblique'),
        ('evenement_special', 'Événement spécial'),
        ('formation', 'Formation'),
        ('jeunesse', 'Jeunesse'),
        ('enfants', 'Enfants'),
    ]
    RECURRENCE_CHOICES = [
        ('none', 'Pas de répétition'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateField(null=True, blank=True)
    heure_debut = models.TimeField(null=True, blank=True)
    
    date_fin = models.DateField(null=True, blank=True)
    heure_fin = models.TimeField(null=True, blank=True)
    lieu = models.CharField(max_length=200)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    recurrence = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default='none',
        verbose_name="Récurrence"
    )
    
    

    @property
    def next_date(self):
        """Calcule dynamiquement la prochaine date du programme."""
        if not self.date_debut:
            return None

        today = timezone.localdate()

        # Si aucune récurrence
        if self.recurrence == 'none':
            return self.date_debut

        # Si récurrence hebdomadaire
        if self.recurrence == 'weekly':
            original_weekday = self.date_debut.weekday()
            days_ahead = (original_weekday - today.weekday()) % 7
            if days_ahead == 0 and self.date_debut < today:
                days_ahead = 7
            next_date = today + timedelta(days=days_ahead)

        # Si récurrence mensuelle
        elif self.recurrence == 'monthly':
            next_date = self.date_debut
            while next_date <= today:
                month = next_date.month + 1
                year = next_date.year
                if month > 12:
                    month = 1
                    year += 1
                next_date = next_date.replace(year=year, month=month)

        else:
            return self.date_debut

        # Si on a une heure, on retourne un datetime complet, sinon juste la date
        if self.heure_debut:
            return timezone.make_aware(
                datetime.combine(next_date, self.heure_debut)
            )
        return next_date

    
    @property
    def is_next_occurrence(self):
        """Vérifie si c'est la prochaine occurrence."""
        next_date = self.next_date
        if not next_date:
            return False
        
        now = timezone.localtime(timezone.now())
        return (next_date > now and 
                next_date == self.next_date)

    def clean(self):
        """Validation personnalisée."""
        super().clean()
        if self.date_debut:
            # Définir automatiquement la récurrence si c'est un jeudi
            if self.date_debut.weekday() == 3:  # 3 = Jeudi
                self.recurrence = 'weekly'
    
    class Meta:
        verbose_name = "Programme d'Église"
        verbose_name_plural = "Programmes d'Église"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.get_categorie_display()}"


class Groupe(models.Model):
    nom_groupe = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    membres = models.ManyToManyField(Membre, through='MembreGroupe', related_name='groupes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        ordering = ['nom_groupe']
    
    def __str__(self):
        return self.nom_groupe


class MembreGroupe(models.Model):
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE)
    groupe = models.ForeignKey(Groupe, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Appartenance au Groupe"
        verbose_name_plural = "Appartenances aux Groupes"
        unique_together = ['membre', 'groupe']
    
    def __str__(self):
        return f"{self.membre.nom_complet} - {self.groupe.nom_groupe}"


class TransactionFinanciere(models.Model):
    TYPE_CHOICES = [
        ('offrande', 'Offrande'),
        ('don', 'Don'),
        ('depense', 'Dépense'),
    ]
    
    CATEGORIE_DEPENSE_CHOICES = [
        ('loyer', 'Loyer'),
        ('salaires', 'Salaires'),
        ('materiel', 'Matériel'),
        ('oeuvres_sociales', 'Œuvres sociales'),
        ('entretien', 'Entretien'),
        ('electricite', 'Électricité'),
        ('eau', 'Eau'),
        ('autres', 'Autres'),
    ]
    
    type_transaction = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_transaction = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    membre = models.ForeignKey(
        Membre, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )
    categorie_depense = models.CharField(
        max_length=20, 
        choices=CATEGORIE_DEPENSE_CHOICES,
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transaction Financière"
        verbose_name_plural = "Transactions Financières"
        ordering = ['-date_transaction']
    
    def __str__(self):
        membre_str = f" - {self.membre.nom_complet}" if self.membre else ""
        return f"{self.get_type_transaction_display()}: {self.montant}€{membre_str}"


class DonMateriel(models.Model):
    STATUT_CHOICES = [
        ('recu', 'Reçu'),
        ('utilise', 'Utilisé'),
        ('en_attente', 'En attente'),
    ]
    
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='dons_materiels')
    description_objet = models.TextField()
    valeur_estimee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    date_don = models.DateTimeField()
    statut_don = models.CharField(max_length=15, choices=STATUT_CHOICES, default='recu')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Don Matériel"
        verbose_name_plural = "Dons Matériels"
        ordering = ['-date_don']
    
    def __str__(self):
        valeur_str = f" ({self.valeur_estimee}€)" if self.valeur_estimee else ""
        return f"{self.membre.nom_complet} - {self.description_objet[:50]}{valeur_str}"
class DemandeAcces(models.Model):
    nom_complet = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role_souhaite = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    est_traitee = models.BooleanField(default=False)
    date_demande = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Demande de {self.nom_complet} ({self.email})"
