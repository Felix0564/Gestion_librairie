from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from .models import Livre, Emprunt, Etudiant, RetourLivre
from .forms import CustomUserCreationForm, EmpruntConfirmationForm, EmpruntForm
from django.contrib.auth.forms import AuthenticationForm
#ygy
def home(request):
    if not request.user.is_authenticated:
        return redirect('login_register')
    livres = Livre.objects.all()
    return render(request, 'librairie/home.html', {'livres': livres})

def login_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()
    return render(request, 'librairie/login_register.html', {
        'login_form': login_form,
        'register_form': register_form
    })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue, {username}!')
                return redirect('home')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
        else:
            messages.error(request, "Formulaire invalide. Veuillez réessayer.")
    return redirect('login_register')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Etudiant.objects.create(
                user=user,
                nom_etudiant=form.cleaned_data.get('last_name'),
                prenom_etudiant=form.cleaned_data.get('first_name'),
                mail_etudiant=form.cleaned_data.get('email'),
                contact_etudiant=form.cleaned_data.get('contact', '')
            )
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Compte créé pour {username}. Vous êtes maintenant connecté.')
                return redirect('home')
            else:
                messages.error(request, "Une erreur s'est produite lors de l'authentification.")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    return redirect('login_register')



def logout_view(request):
    logout(request)
    return redirect('login_register')

@login_required
def detail_livre(request, id_livre):
    livre = get_object_or_404(Livre, id_livre=id_livre)
    return render(request, 'librairie/detail_livre.html', {'livre': livre})



from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Livre, Etudiant, Emprunt,RetourLivre
from .forms import EmpruntConfirmationForm

@login_required
def emprunter_livre(request, id_livre):
    livre = get_object_or_404(Livre, id_livre=id_livre)
    try:
        etudiant = request.user.etudiant
    except Etudiant.DoesNotExist:
        messages.error(request, "Vous devez être enregistré comme étudiant pour emprunter un livre.")
        return redirect('detail_livre', id_livre=id_livre)
    
    # Vérifier si l'étudiant a déjà un emprunt en cours
    emprunt_en_cours =Emprunt.objects.filter(etudiant=etudiant,retour__isnull=True).first()
    if emprunt_en_cours:
        #if emprunt_en_cours.date_retour_prevue > timezone.now().date():
            messages.error(request, "Vous avez déjà un livre emprunté. Vous ne pouvez pas emprunter un autre livre avant de retourner celui-ci.")
            return redirect('detail_livre', id_livre=id_livre)
    
    if not livre.etat_livre or livre.nombre_exemplaire <= 0:
        messages.error(request, "Ce livre n'est pas disponible pour l'emprunt.")
        return redirect('detail_livre', id_livre=id_livre)
    
    date_emprunt = timezone.now().date()
    date_recuperation = date_emprunt + timedelta(days=3)
    date_retour_prevue = date_emprunt + timedelta(days=14)
    
    if request.method == 'POST':
        form = EmpruntConfirmationForm(request.POST)
        if form.is_valid():
            emprunt = Emprunt.objects.create(
                etudiant=etudiant,
                livre=livre,
                date_emprunt=date_emprunt,
                date_recuperation=date_recuperation,
                date_retour_prevue=date_retour_prevue
            )
            livre.nombre_exemplaire -= 1
            if livre.nombre_exemplaire == 0:
                livre.etat_livre = False
            livre.save()
            
            messages.success(request, f"Vous avez emprunté '{livre.titre_livre}'. Date de récupération : {emprunt.date_recuperation}. Date de retour prévue : {emprunt.date_retour_prevue}")
            return redirect('detail_livre', id_livre=id_livre)
    else:
        form = EmpruntConfirmationForm()
    
    context = {
        'livre': livre,
        'form': form,
        'date_recuperation': date_recuperation,
        'date_retour_prevue': date_retour_prevue,
    }
    return render(request, 'librairie/emprunter_livre.html', context)
@login_required
def mes_emprunts(request):
    try:
        etudiant = request.user.etudiant
        emprunts = Emprunt.objects.filter(etudiant=etudiant, date_retour_prevue__gte=timezone.now())
        return render(request, 'librairie/mes_emprunts.html', {'emprunts': emprunts})
    except Etudiant.DoesNotExist:
        messages.error(request, "Vous n'êtes pas enregistré comme étudiant. Veuillez contacter l'administrateur.")
        return redirect('home')



def retourner_livre(request, id_emprunt):
    emprunt = get_object_or_404(Emprunt, id_emprunt=id_emprunt, etudiant=request.user.etudiant)
    livre = emprunt.livre
    
    livre.nombre_exemplaire += 1
    livre.etat_livre = True
    livre.save()
    
    retour = RetourLivre.objects.create(emprunt=emprunt)
    
    if retour.penalite > 0:
        messages.warning(request, f"Livre retourné avec succès! Une pénalité de {retour.penalite}€ a été appliquée pour retard.")
    else:
        messages.success(request, "Livre retourné avec succès!")
    
    return redirect('mes_emprunts')

def search_livre(request):
    query = request.GET.get('q')
    if query:
        livres = Livre.objects.filter(Q(titre_livre__icontains=query) | Q(auteur_livre__icontains=query))
    else:
        livres = Livre.objects.all()
    return render(request, 'librairie/home.html', {'livres': livres})

def tableau_de_bord(request):
    total_livres = Livre.objects.count()
    total_emprunts = Emprunt.objects.count()
    livres_plus_empruntes = Livre.objects.annotate(nombre_emprunts=Count('emprunts')).order_by('-nombre_emprunts')[:5]
    
    six_mois_avant = timezone.now() - timedelta(days=180)
    emprunts_par_mois = Emprunt.objects.filter(date_emprunt__gte=six_mois_avant).annotate(
        mois=TruncMonth('date_emprunt')
    ).values('mois').annotate(total=Count('id_emprunt')).order_by('mois')
    
    emprunts_en_retard = Emprunt.objects.filter(date_retour_prevue__lt=timezone.now()).count()
    
    context = {
        'total_livres': total_livres,
        'total_emprunts': total_emprunts,
        'livres_plus_empruntes': livres_plus_empruntes,
        'emprunts_par_mois': emprunts_par_mois,
        'emprunts_en_retard': emprunts_en_retard,
    }
    
    return render(request, 'librairie/tableau_de_bord.html', context)


# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth import login, authenticate, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.utils import timezone
# from datetime import timedelta
# from django.db.models import Q, Count
# from django.db.models.functions import TruncMonth
# from .models import Livre, Emprunt, Etudiant, Receptionniste
# from .forms import CustomUserCreationForm
# from django.contrib.auth.forms import AuthenticationForm

# def home(request):
#     if not request.user.is_authenticated:
#         return redirect('login_register')
#     livres = Livre.objects.all()
#     return render(request, 'librairie/home.html', {'livres': livres})

# def login_register(request):
#     if request.user.is_authenticated:
#         return redirect('home')
#     login_form = AuthenticationForm()
#     register_form = CustomUserCreationForm()
#     return render(request, 'librairie/login_register.html', {
#         'login_form': login_form,
#         'register_form': register_form
#     })

# # from django.contrib.auth import authenticate, login
# # from django.contrib.auth.forms import AuthenticationForm

# def login_view(request):
#     if request.method == 'POST':
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 messages.success(request, f'Bienvenue, {username}!')
#                 return redirect('home')
#             else:
#                 messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
#     else:
#         form = AuthenticationForm()
#     return render(request, 'librairie/login_register.html', {'login_form': form})

# # from django.shortcuts import render, redirect
# # from django.contrib import messages

# from .models import Etudiant

# def register(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             Etudiant.objects.create(user=user)  # Créer un objet Etudiant pour le nouvel utilisateur
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password1')  # Assurez-vous d'utiliser le bon champ pour récupérer le mot de passe
#             user = authenticate(username=username, password=password)  # Authentifier l'utilisateur
#             if user is not None:
#                 login(request, user)  # Connecter l'utilisateur automatiquement
#                 messages.success(request, f'Compte créé pour {username}. Vous êtes maintenant connecté.')
#                 return redirect('home')  # Rediriger vers la page d'accueil
#     else:
#         form = CustomUserCreationForm()
#     return render(request, 'librairie/login_register.html', {'register_form': form})

# # def register(request):
# #     if request.method == 'POST':
# #         form = CustomUserCreationForm(request.POST)
# #         if form.is_valid():
# #             user = form.save()
# #             Etudiant.objects.create(user=user)  # Créer un objet Etudiant pour le nouvel utilisateur
# #             username = form.cleaned_data.get('username')
# #             messages.success(request, f'Compte créé pour {username}. Vous pouvez maintenant vous connecter.')
# #             return redirect('login')
# #     else:
# #         form = CustomUserCreationForm()
# #     return render(request, 'librairie/login_register.html', {'register_form': form})

# def logout_view(request):
#     logout(request)
#     return redirect('login_register')

# @login_required
# def detail_livre(request, id_livre):
#     livre = get_object_or_404(Livre, id_livre=id_livre)
#     return render(request, 'librairie/detail_livre.html', {'livre': livre})



# from .forms import CustomUserCreationForm, EmpruntForm
# from .models import Livre, Emprunt

# #------------------------

# # def login_view(request):
# #     if request.method == 'POST':
# #         form = AuthenticationForm(request, data=request.POST)
# #         if form.is_valid():
# #             username = form.cleaned_data.get('username')
# #             password = form.cleaned_data.get('password')
# #             user = authenticate(username=username, password=password)
# #             if user is not None:
# #                 login(request, user)
# #                 messages.success(request, f'Bienvenue, {username}!')
# #                 return redirect('home')
# #             else:
# #                 messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
# #     else:
# #         form = AuthenticationForm()
# #     return render(request, 'librairie/login_register.html', {'login_form': form})

# @login_required
# def emprunter_livre(request, id_livre):
#     livre = get_object_or_404(Livre, id_livre=id_livre)
    
#     # Vérifiez si l'utilisateur a un objet Etudiant associé
#     try:
#         etudiant = request.user.etudiant
#     except Etudiant.DoesNotExist:
#         messages.error(request, "Vous devez être enregistré comme étudiant pour emprunter un livre.")
#         return redirect('detail_livre', id_livre=id_livre)
    
#     if request.method == 'POST':
#         form = EmpruntForm(request.POST)
#         if form.is_valid():
#             if livre.etat_livre and livre.nombre_exemplaire > 0:
#                 emprunt = Emprunt.objects.create(
#                     etudiant=etudiant,
#                     livre=livre,
#                     date_emprunt=timezone.now().date(),
#                     date_retour_prevue=form.cleaned_data['date_retour_prevue']
#                 )
#                 livre.nombre_exemplaire -= 1
#                 if livre.nombre_exemplaire == 0:
#                     livre.etat_livre = False
#                 livre.save()
#                 messages.success(request, f"Vous avez emprunté '{livre.titre_livre}'. Date de retour prévue : {emprunt.date_retour_prevue}")
#                 return redirect('detail_livre', id_livre=id_livre)
#             else:
#                 messages.error(request, "Ce livre n'est pas disponible pour l'emprunt.")
#     else:
#         form = EmpruntForm()
    
#     return render(request, 'librairie/emprunter_livre.html', {'livre': livre, 'form': form})




# @login_required
# def mes_emprunts(request):
#     try:
#         etudiant = request.user.etudiant
#         emprunts = Emprunt.objects.filter(etudiant=etudiant, date_retour_prevue__gte=timezone.now())
#         return render(request, 'librairie/mes_emprunts.html', {'emprunts': emprunts})
#     except Etudiant.DoesNotExist:
#         messages.error(request, "Vous n'êtes pas enregistré comme étudiant. Veuillez contacter l'administrateur.")
#         return redirect('home')

# @login_required
# def retourner_livre(request, id_emprunt):
#     emprunt = get_object_or_404(Emprunt, id_emprunt=id_emprunt, etudiant=request.user.etudiant)
#     livre = emprunt.livre
    
#     livre.nombre_exemplaire += 1
#     livre.etat_livre = True
#     livre.save()
    
#     emprunt.date_retour_emprunt = timezone.now()
#     emprunt.save()
    
#     messages.success(request, "Livre retourné avec succès!")
#     return redirect('mes_emprunts')

# def search_livre(request):
#     query = request.GET.get('q')
#     if query:
#         livres = Livre.objects.filter(Q(titre_livre__icontains=query) | Q(auteur_livre__icontains=query))
#     else:
#         livres = Livre.objects.all()
#     return render(request, 'librairie/home.html', {'livres': livres})


# def tableau_de_bord(request):
#     # if not hasattr(request.user, 'receptionniste'):
#     #     return redirect('home')

#     total_livres = Livre.objects.count()
#     total_emprunts = Emprunt.objects.count()
#     livres_plus_empruntes = Livre.objects.annotate(nombre_emprunts=Count('emprunts')).order_by('-nombre_emprunts')[:5]
    
#     six_mois_avant = timezone.now() - timedelta(days=180)
#     emprunts_par_mois = Emprunt.objects.filter(date_emprunt__gte=six_mois_avant).annotate(
#         mois=TruncMonth('date_emprunt')
#     ).values('mois').annotate(total=Count('id_emprunt')).order_by('mois')
    
#     emprunts_en_retard = Emprunt.objects.filter(date_retour_prevue__lt=timezone.now()).count()
    
#     context = {
#         'total_livres': total_livres,
#         'total_emprunts': total_emprunts,
#         'livres_plus_empruntes': livres_plus_empruntes,
#         'emprunts_par_mois': emprunts_par_mois,
#         'emprunts_en_retard': emprunts_en_retard,
#     }
    
#     return render(request, 'librairie/tableau_de_bord.html', context)





# # from django.shortcuts import render, get_object_or_404, redirect
# # from django.contrib.auth import login, authenticate, logout
# # from django.contrib.auth.decorators import login_required
# # from django.contrib import messages
# # from django.utils import timezone
# # from datetime import timedelta
# # from django.db.models import Q, Count
# # from django.db.models.functions import TruncMonth
# # from .models import Livre, Emprunt, Etudiant, Receptionniste
# # from .forms import CustomUserCreationForm

# # def home(request):
# #     livres = Livre.objects.all()
# #     return render(request, 'librairie/home.html', {'livres': livres})

# # def login_view(request):
# #     if request.method == 'POST':
# #         username = request.POST['username']
# #         password = request.POST['password']
# #         user = authenticate(request, username=username, password=password)
# #         if user is not None:
# #             login(request, user)
# #             return redirect('home')
# #         else:
# #             messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
# #     return render(request, 'librairie/login_register.html')

# # def register(request):
# #     if request.method == 'POST':
# #         form = CustomUserCreationForm(request.POST)
# #         if form.is_valid():
# #             user = form.save()
# #             Etudiant.objects.create(user=user)
# #             login(request, user)
# #             return redirect('home')
# #     else:
# #         form = CustomUserCreationForm()
# #     return render(request, 'librairie/login_register.html', {'form': form})

# # def logout_view(request):
# #     logout(request)
# #     return redirect('home')

# # @login_required
# # def detail_livre(request, id_livre):
# #     livre = get_object_or_404(Livre, id_livre=id_livre)
# #     return render(request, 'librairie/detail_livre.html', {'livre': livre})

# # @login_required
# # def emprunter_livre(request, id_livre):
# #     livre = get_object_or_404(Livre, id_livre=id_livre)
# #     if livre.etat_livre and livre.nombre_exemplaire > 0:
# #         livre.nombre_exemplaire -= 1
# #         if livre.nombre_exemplaire == 0:
# #             livre.etat_livre = False
# #         livre.save()
        
# #         Emprunt.objects.create(
# #             etudiant=request.user.etudiant,
# #             livre=livre,
# #             date_emprunt=timezone.now(),
# #             date_retour_emprunt=timezone.now() + timedelta(days=14)
# #         )
        
# #         messages.success(request, "Livre emprunté avec succès!")
# #     else:
# #         messages.error(request, "Ce livre n'est pas disponible pour l'emprunt.")
    
# #     return redirect('detail_livre', id_livre=id_livre)

# # @login_required
# # def mes_emprunts(request):
# #     emprunts = Emprunt.objects.filter(etudiant=request.user.etudiant, date_retour_emprunt__gte=timezone.now())
# #     return render(request, 'librairie/mes_emprunts.html', {'emprunts': emprunts})

# # @login_required
# # def retourner_livre(request, id_emprunt):
# #     emprunt = get_object_or_404(Emprunt, id_emprunt=id_emprunt, etudiant=request.user.etudiant)
# #     livre = emprunt.livre
    
# #     livre.nombre_exemplaire += 1
# #     livre.etat_livre = True
# #     livre.save()
    
# #     emprunt.date_retour_emprunt = timezone.now()
# #     emprunt.save()
    
# #     messages.success(request, "Livre retourné avec succès!")
# #     return redirect('mes_emprunts')

# # def search_livre(request):
# #     query = request.GET.get('q')
# #     if query:
# #         livres = Livre.objects.filter(Q(titre_livre__icontains=query) | Q(auteur_livre__icontains=query))
# #     else:
# #         livres = Livre.objects.all()
# #     return render(request, 'librairie/home.html', {'livres': livres})

# # @login_required
# # def tableau_de_bord(request):
# #     if not hasattr(request.user, 'receptionniste'):
# #         return redirect('home')

# #     total_livres = Livre.objects.count()
# #     total_emprunts = Emprunt.objects.count()
# #     livres_plus_empruntes = Livre.objects.annotate(nombre_emprunts=Count('emprunts')).order_by('-nombre_emprunts')[:5]
    
# #     six_mois_avant = timezone.now() - timedelta(days=180)
# #     emprunts_par_mois = Emprunt.objects.filter(date_emprunt__gte=six_mois_avant).annotate(
# #         mois=TruncMonth('date_emprunt')
# #     ).values('mois').annotate(total=Count('id')).order_by('mois')
    
# #     emprunts_en_retard = Emprunt.objects.filter(date_retour_emprunt__lt=timezone.now()).count()
    
# #     context = {
# #         'total_livres': total_livres,
# #         'total_emprunts': total_emprunts,
# #         'livres_plus_empruntes': livres_plus_empruntes,
# #         'emprunts_par_mois': emprunts_par_mois,
# #         'emprunts_en_retard': emprunts_en_retard,
# #     }
    
# #     return render(request, 'librairie/tableau_de_bord.html', context)