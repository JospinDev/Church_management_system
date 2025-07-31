# admin.py
from django.contrib import admin
from .models import (
    Membre, Role, MembreRole, CompteUtilisateur, Couple, ProgrammeMariage,
    ProgrammeEglise, Groupe, MembreGroupe, TransactionFinanciere, DonMateriel,
    DemandeAcces
)

@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone', 'statut_baptismal', 'date_adhesion')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('statut_baptismal', 'date_adhesion')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom_role', 'description')
    search_fields = ('nom_role',)
    list_filter = ('nom_role',)

@admin.register(MembreRole)
class MembreRoleAdmin(admin.ModelAdmin):
    list_display = ('membre', 'role')
    search_fields = ('membre__nom', 'role__nom_role')

@admin.register(CompteUtilisateur)
class CompteUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'last_login', 'membre')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')

@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    list_display = ('membre_mari', 'membre_femme', 'statut_couple', 'date_mariage')
    search_fields = ('membre_mari__nom', 'membre_femme__nom')
    list_filter = ('statut_couple',)

@admin.register(ProgrammeMariage)
class ProgrammeMariageAdmin(admin.ModelAdmin):
    list_display = ('titre', 'couple', 'date_debut', 'date_fin', 'statut')
    list_filter = ('statut', 'date_debut')
    search_fields = ('titre', 'couple__membre_mari__nom', 'couple__membre_femme__nom')

@admin.register(ProgrammeEglise)
class ProgrammeEgliseAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'date_debut', 'lieu')
    list_filter = ('categorie', 'date_debut')
    search_fields = ('titre', 'lieu')

@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ('nom_groupe', 'description')
    search_fields = ('nom_groupe',)

@admin.register(MembreGroupe)
class MembreGroupeAdmin(admin.ModelAdmin):
    list_display = ('membre', 'groupe')
    search_fields = ('membre__nom', 'groupe__nom_groupe')

@admin.register(TransactionFinanciere)
class TransactionFinanciereAdmin(admin.ModelAdmin):
    list_display = ('type_transaction', 'montant', 'date_transaction', 'membre', 'categorie_depense')
    list_filter = ('type_transaction', 'categorie_depense', 'date_transaction')
    search_fields = ('membre__nom',)

@admin.register(DonMateriel)
class DonMaterielAdmin(admin.ModelAdmin):
    list_display = ('membre', 'description_objet', 'valeur_estimee', 'statut_don', 'date_don')
    list_filter = ('statut_don', 'date_don')
    search_fields = ('membre__nom', 'description_objet')

@admin.register(DemandeAcces)
class DemandeAccesAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'role_souhaite', 'est_traitee', 'date_demande')
    list_filter = ('est_traitee', 'role_souhaite')
    search_fields = ('nom_complet', 'email')
