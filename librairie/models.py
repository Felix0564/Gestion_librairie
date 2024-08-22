from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User

class Livre(models.Model):
    id_livre = models.AutoField(primary_key=True)
    titre_livre = models.CharField(max_length=100)
    auteur_livre = models.CharField(max_length=100)
    date_publication_livre = models.DateField()
    etat_livre = models.BooleanField(default=True)
    nombre_exemplaire = models.IntegerField()
    nombre_page = models.IntegerField()
    image_couverture_livre = models.ImageField(upload_to='livres', null=True, blank=True)

    def __str__(self):
        return self.titre_livre

class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_etudiant=models.CharField(max_length=15)
    prenom_etudiant=models.CharField(max_length=20)
    mail_etudiant=models.EmailField()
    contact_etudiant = models.CharField(max_length=15)
    emprunter_livre = models.ManyToManyField(Livre, through='Emprunt', related_name='etudiants_emprunts')
    rechecher_livre = models.ManyToManyField(Livre, related_name='etudiants_recherches')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
def date_recuperation_default():
    return timezone.now().date() + timedelta(days=3)

def date_retour_prevue_default():
    return timezone.now().date() + timedelta(days=14)

class Emprunt(models.Model):
    id_emprunt = models.AutoField(primary_key=True)
    date_emprunt = models.DateField(auto_now_add=True)
    date_recuperation = models.DateField(default=date_recuperation_default)
    date_retour_prevue = models.DateField(default=date_retour_prevue_default)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='emprunts')
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='emprunts')

    def __str__(self):
        return f"{self.etudiant} - {self.livre}"
    
class RetourLivre(models.Model):
    id_retour = models.AutoField(primary_key=True)
    emprunt = models.OneToOneField(Emprunt, on_delete=models.CASCADE, related_name='retour')
    date_retour_effective = models.DateField(default=timezone.now)
    penalite = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.date_retour_effective > self.emprunt.date_retour_prevue:
            jours_retard = (self.date_retour_effective - self.emprunt.date_retour_prevue).days
            self.penalite = jours_retard * 1.0 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Retour de {self.emprunt}"

class Receptionniste(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_receptionniste=models.CharField(max_length=15)
    prenom_receptionniste=models.CharField(max_length=20)
    mail_receptionniste=models.EmailField()
    contact_receptionniste = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Rapport(models.Model):
    id_rapport = models.AutoField(primary_key=True)
    date_rapport = models.DateField()
    livres_plus_empruntes = models.ManyToManyField(Livre, related_name='rapports_plus_empruntes')
    livres_moins_empruntes = models.ManyToManyField(Livre, related_name='rapports_moins_empruntes')
    receptionniste = models.ForeignKey(Receptionniste, on_delete=models.CASCADE, related_name='rapports')

    def __str__(self):
        return f"Rapport du {self.date_rapport}"