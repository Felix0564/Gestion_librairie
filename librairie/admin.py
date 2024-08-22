from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib.admin import AdminSite
from .models import Livre, Etudiant, Emprunt, Receptionniste, Rapport, RetourLivre

class LibrairieAdminSite(AdminSite):
    site_header = "Gestion de la Bibliotheque Scolaire"
    site_title = "Administration Bibliotheque"
    index_title = "Bienvenue dans l'administration de la Bibliotheque"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('tableau-de-bord/', self.admin_view(self.tableau_de_bord_view), name='admin_tableau_de_bord'),
        ]
        return custom_urls + urls

    def tableau_de_bord_view(self, request):
        # Redirection vers la vue du tableau de bord
        return HttpResponseRedirect(reverse('tableau_de_bord'))

    def each_context(self, request):
        context = super().each_context(request)
        context['dashboard_link'] = format_html(
            '<a href="{}" class="button" style="margin-top: 20px;">Aller au tableau de bord</a>',
            reverse('admin:admin_tableau_de_bord')
        )
        return context

# Création de l'instance personnalisée du site d'administration
librairie_admin = LibrairieAdminSite(name='librairie_admin')

# Enregistrement des modèles avec le site d'administration personnalisé
librairie_admin.register(Livre)
librairie_admin.register(Etudiant)
librairie_admin.register(Emprunt)
librairie_admin.register(RetourLivre)
librairie_admin.register(Receptionniste)
librairie_admin.register(Rapport)