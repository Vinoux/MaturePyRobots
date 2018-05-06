import json
import random

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import logout as system_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from channels import Group
from pure_pagination.mixins import PaginationMixin

from .constants import NotificationMessage
from .forms import SignUpForm, ChangeDataForm, CodeForm, ChampionshipForm
from .funct.funct import getItemByType,getBoolInventory
from .game.Game import Game
from .models import Weapon, Armor, Caterpillar, NavSystem, TypeItem, Inventory, DefaultIa
from .models import UserProfile, Tank, Ia, BattleHistory, Notification, FAQ, Championship
from .utils import validate_ai_script, award_battle




def index(request):
    if request.user.is_authenticated:

        current_user = UserProfile.objects.get(user=request.user)

        champ_pk = UserProfile.objects.get(user=request.user).championship_set.all()[0].pk

        '''
        champ_pk = UserProfile.objects.get(user=request.user).championship_set.all()[0].pk
        print(champ_pk)

        players = Championship.objects.get(pk=champ_pk).players.all()
        for obj in players:
            print(obj.exp)

        champ = Championship.objects.all()
        for c in champ:
            print(c.name)
        '''


        context = {'money' : UserProfile.objects.get(user=request.user).money,
                   'username' : request.user,
                   'pageIn' : 'accueil' ,
                   #'point' : UserProfile.objects.get(user=request.user).exp,
                   'agression': UserProfile.objects.get(user=request.user).agression,
                   'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user)),
                   'scripts' : request.user.userprofile.ia_set.all(),
                   'active_script' : request.user.userprofile.get_active_ai_script(),
                   'players' : UserProfile.objects.exclude(pk=current_user.pk),
                   # 'classement' : UserProfile.objects.order_by('-exp'),
                   'classement' : Championship.objects.get(pk=champ_pk).players.all().order_by('-exp'),
                   'all_championship': Championship.objects.all(),
                   'championnat' : UserProfile.objects.get(user=request.user).championship_set.all()[0].name}
        return render(request, "backend/accueil.html", context)
    else:
        form = SignUpForm()
        context = { 'form' : form }
        return render(request, "backend/index.html",context)


@never_cache
def login(request):
    if request.user.is_authenticated:
        return redirect(reverse('backend:index'))
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is not None:
            from django.contrib.auth import login
            login(request, user)
            urlnext = request.POST.get('next', reverse('backend:index'))
            return redirect(urlnext)
        else:
            form = SignUpForm()
            context = {
                'form': form,
                'next': request.GET.get('next'),
                'error': 'Votre Pseudo et/ou votre mot de passe ne correspond pas, veuillez réessayer. Merci'
            }
            return render(request, 'backend/index.html', context)
    return render(request, 'backend/index.html',  {'next': request.GET.get('next')})


@never_cache
def logout(request):
    system_logout(request)
    return redirect(reverse('backend:index'))


class SignUp (FormView):
    template_name = 'backend/index.html'
    form_class = SignUpForm

    def get_success_url(self):

        self.success_url = reverse('backend:login')

        return super().get_success_url()

    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            user = User.objects.create_user(username, email, password)

            #create User
            UserProfile(user=user, money=0, next_level_exp=int(1/settings.EXP_CONSTANT), agression=True).save()

            #create ia file default
            userProfile = UserProfile.objects.get(user=user)
            i = Ia.objects.create(owner=userProfile,
                                  name="%s Default AI" % username,
                                  text=DefaultIa.objects.get(pk=1).text,
                                  active=True)

            Championship.objects.get(pk=1).add_user(userProfile)

            #default Inventory
            Inventory.objects.create(owner=userProfile, item=1, typeItem=TypeItem(pk=1))
            Inventory.objects.create(owner=userProfile, item=1, typeItem=TypeItem(pk=2))
            Inventory.objects.create(owner=userProfile, item=1, typeItem=TypeItem(pk=3))
            Inventory.objects.create(owner=userProfile, item=1, typeItem=TypeItem(pk=4))

            #init tank
            w = getItemByType(1,TypeItem(pk=1))
            a = getItemByType(1,TypeItem(pk=2))
            c = getItemByType(1,TypeItem(pk=3))
            n = getItemByType(1,TypeItem(pk=4))
            Tank.objects.create(owner=userProfile, ia=i,weapon=w,armor=a,caterpillar=c,navSystem=n)


            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)

            from django.contrib.auth import login
            login(self.request, user)

            return super(SignUp, self).form_valid(form)

        context = {
            'form': form,
            'error': 'Pseudo déjà utilisé, veuillez en choisir un autre. Merci'
        }

        return render(None, "backend/index.html", context)


def thanks(request):
    return index(request)


@login_required
def fight(request, player_pk=''):
    """
    Process a battle
    """
    user1 = UserProfile.objects.get(user=request.user)
    battle = user1.get_running_battle()

    champ = UserProfile.objects.get(user=request.user).championship_set.all()[0]
    champ_pk = champ.pk

    # New battle
    if not battle:
        users1 = UserProfile.objects.exclude(pk=user1.pk)
        # Get list of players which have level = the current player level +/- 5
        users = Championship.objects.get(pk=champ_pk).players.all()
        if not users:
            messages.error(request, "Aucun joueur disponible pour une battle.")
            context = {
                "battle_err": True
            }
            return render(request, "backend/fight.html", context)
        # Get opponent by a random choice from the list above
        if player_pk == '':
            user2 = random.choice(list(users))
        else:
            user2 = UserProfile.objects.get(pk=player_pk)
            is_in_champ = user2.championship_set.all()[0].pk
            if champ_pk != is_in_champ:
                user2 = random.choice(list(users))
                messages.warning(request, "L'adversaire choisie n'est pas dans votre championnat. Une battle contre un joueur au hasard a été démarré")


        # Send realtime notification to the opponent if he's online
        notify = NotificationMessage()
        notify.msg_content = "%s vient de démarrer un combat contre toi" % user1.user.username
        Group(user2.user.username + '-notifications').send(
            {'text': notify.dumps()})

        # Notification objects. Not in use in this phase
        Notification.objects.create(user=user1.user, content="Vous démarrer un combat face à %s" % user2.user.username,
                                    is_read=True)
        Notification.objects.create(user=user2.user,
                                    content="%s vient de démarrer un combat contre toi" % user1.user.username)

        # Get players's tanks and start the battle
        tank1 = user1.get_tank()
        tank2 = user2.get_tank()
        ia1 = user1.get_active_ai_script()
        ia2 = user2.get_active_ai_script()
        game = Game(tank1, tank2, ia1, ia2, champ.name)
        res = game.run(0)

        opponent = user2.user.username
        player_x = settings.PLAYER_INITIAL_POS_X
        player_y = settings.PLAYER_INITIAL_POS_Y
        opponent_x = settings.OPPONENT_INITIAL_POS_X
        opponent_y = settings.OPPONENT_INITIAL_POS_Y
        script_user = ia1.pk
        step = 0
        map_name = random.choice(settings.BATTLE_MAP_NAMES)
        bh_pk = game.set_history(map_name, False)
    # Continue current battle
    else:
        res_stats = battle.result_stats
        try:
            res = json.loads(res_stats)
        except ValueError:
            print ("ValueError - battle result: %s" % res_stats)
            res = []

        opponent = battle.opponent.username
        player_x = battle.player_x
        player_y = battle.player_y
        opponent_x = battle.opponent_x
        opponent_y = battle.opponent_y
        script_user = battle.used_script.pk
        step = battle.step
        map_name = battle.map_name
        bh_pk = battle.pk
        messages.warning(request, "Vous avez déjà une battle en cours...")


    context = {
        'result': res,
        'pageIn': 'accueil',
        'opponent': opponent,
        'player_x': player_x,
        'player_y': player_y,
        'opponent_x': opponent_x,
        'opponent_y': opponent_y,
        'step': step,
        'map_name': map_name,
        'history_pk': bh_pk,
        'is_versus': 'no',
        'script_used': script_user,
        'championnat': user1.championship_set.all()[0].name
    }
    return render(request, "backend/fight.html", context)


@login_required
def testcpu(request, player_pk='', script_pk=''):
    user1 = UserProfile.objects.get(user=request.user)

    champ = UserProfile.objects.get(user=request.user).championship_set.all()[0]
    champ_pk = champ.pk

    # print("player_pk: ", player_pk)
    # print("script_pk: ", script_pk)

    battle = user1.get_running_battle()
    if not battle:
        # users1 = UserProfile.objects.exclude(pk=user1.pk)

        users = Championship.objects.get(pk=champ_pk).players.all()

        if not users:
            messages.error(request, "Aucun joueur disponible pour le training battle")
            context = {
                "battle_err": True
            }
            return render(request, "backend/fight.html", context)

        #user2 = UserProfile.objects.get(user=request.user)

        if script_pk != '':
            user2 = UserProfile.objects.get(user=request.user)
            opponent = user2.user
            tank1 = Tank.objects.get(owner=user1)
            tank2 = Tank.objects.get(owner=user2)
            ia1 = user1.get_active_ai_script()  # Ia.objects.get(owner=user1)


            script_1 = user1.ia_set.filter(name=ia1) # for pk -> list(script_1)[0].pk
            old_selected = list(script_1)[0].pk
            old_ia = Ia.objects.get(pk=old_selected)

            # print("retour ", ia1.text)

            # script_2 = user2.ia_set.filter(pk=script_pk)
            selected = Ia.objects.get(pk=script_pk)

            # selected = Ia.objects.get(pk=selected_pk)
            user1.change_active_ai(selected)

            ia2 = user1.get_active_ai_script()

            user1.change_active_ai(old_ia)
            # print(selected.text," - ", script_2, " - ", list(script_1)[0])
            # ia2 = selected
            # print("retour ", ia2)
        else:
            if player_pk != '':
                user2 = UserProfile.objects.get(pk=player_pk)
                is_in_champ = user2.championship_set.all()[0].pk
                if champ_pk == is_in_champ:
                    opponent = user2.user
                    tank1 = Tank.objects.get(owner=user1)
                    tank2 = Tank.objects.get(owner=user2)
                    ia1 = user1.get_active_ai_script()  # Ia.objects.get(owner=user1)
                    ia2 = user2.get_active_ai_script()  # Ia.objects.get(owner=CPU)
                    # print("choix: ", user2.user, ia2.name)
                else:
                    user2 = random.choice(list(users))
                    opponent = user2.user
                    tank1 = Tank.objects.get(owner=user1)
                    tank2 = Tank.objects.get(owner=user2)
                    ia1 = user1.get_active_ai_script()  # Ia.objects.get(owner=user1)
                    ia2 = user2.get_active_ai_script()  # Ia.objects.get(owner=CPU)
                    messages.warning(request, "L'adversaire choisie n'est pas dans votre championnat. Une battle contre un joueur au hasard a été démarré")
            else:
                user2 = random.choice(list(users))
                opponent = user2.user
                tank1 = Tank.objects.get(owner=user1)
                tank2 = Tank.objects.get(owner=user2)
                ia1 = user1.get_active_ai_script()  # Ia.objects.get(owner=user1)
                ia2 = user2.get_active_ai_script()  # Ia.objects.get(owner=CPU)


        game = Game(tank1, tank2, ia1, ia2, champ.name)

        res = game.run(0)

        # print(res)
        # print("\n")
        # print(game)

        if game.is_victorious():                #launcher WIN
            is_victorious = "yes"
        else:                                   #launcher LOSE
            is_victorious = "no"
        # opponent = "CPU"
        script_user = ia1.pk
        player_x = 0
        player_y = 0
        opponent_x = 31
        opponent_y = 31
        step = 0
        map_name = random.choice(settings.BATTLE_MAP_NAMES)

        if script_pk != '':
            selected = Ia.objects.get(pk=script_pk)
            bh_pk = game.set_history_itself(map_name, True, selected)
        else:
            bh_pk = game.set_history(map_name, True)
    else:
        res_stats = battle.result_stats
        try:
            res = json.loads(res_stats)
        except ValueError:
            print ("ValueError - battle result: %s" % res_stats)
            res = []

        opponent = battle.opponent.username
        is_victorious = "no"
        if battle.is_victorious:
            is_victorious = "yes"
        player_x = battle.player_x
        player_y = battle.player_y
        opponent_x = battle.opponent_x
        opponent_y = battle.opponent_y
        script_user = battle.used_script.pk
        step = battle.step
        map_name = battle.map_name
        bh_pk = battle.pk
        messages.warning(request, "Vous avez déjà une battle en cours...")

    context = {
        'result': res,
        'pageIn': 'battle',
        'opponent': opponent,
        'is_victorious':is_victorious,
        'player_x': player_x,
        'player_y': player_y,
        'opponent_x': opponent_x,
        'opponent_y': opponent_y,
        'step': step,
        'map_name': map_name,
        'history_pk': bh_pk,
        'is_versus' : 'yes',
        'script_used': script_user,
        'championnat': UserProfile.objects.get(user=request.user).championship_set.all()[0].name
    }
    return render(request, "backend/fight.html", context)

@login_required
def replay(request):
    '''
    Replay animation without gains
    :param request:
    :return: replay battle againt user= p_id
    '''
    bh_pk = request.GET.get('bh_pk')
    try:
        battle = BattleHistory.objects.get(pk=bh_pk)
    except:
        messages.error(request, "Battle not found")
        return render(request, "backend/fight.html")

    if battle.user != request.user:
        if battle.opponent != request.user:
            messages.error(request, "You dont have permission to view this battle")
            return render(request, "backend/fight.html")

    res_stats = battle.result_stats
    try:
        res = json.loads(res_stats)
    except ValueError:
        print("ValueError - battle result: %s" % res_stats)
        res = []

    opponent = battle.opponent.username
    map_name = battle.map_name
    bh_pk = battle.pk
    player_x = 0
    player_y = 0
    opponent_x = 31
    opponent_y = 31
    step = 0

    context = {
        'result': res,
        'pageIn': 'accueil',
        'opponent': opponent,
        'player_x': player_x,
        'player_y': player_y,
        'opponent_x': opponent_x,
        'opponent_y': opponent_y,
        'step': step,
        'map_name': map_name,
        'history_pk': bh_pk,
        'is_replay': 'yes',
        'championnat': UserProfile.objects.get(user=request.user).championship_set.all()[0].name
    }

    return render(request, "backend/fight.html", context)

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        print("ICI")
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            context = {'money': UserProfile.objects.get(user=request.user).money,
                       'username': request.user,
                       'pageIn': 'accueil',
                       'agression': UserProfile.objects.get(user=request.user).agression,
                       'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user))}
            messages.success(request, "Changement de mot de passe effectué.")
            return render(request, "backend/accueil.html", context)
        else:
            context = {'money': UserProfile.objects.get(user=request.user).money,
                       'username': request.user,
                       'pageIn': 'accueil',
                       'agression': UserProfile.objects.get(user=request.user).agression,
                       'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user))}
            messages.error(request, "Les mots de passe ne sont pas identiques. Veuillez réessayer.")
            return render(request, "backend/accueil.html", context)

@login_required
def editor(request):
    userprofile = UserProfile.objects.get(user=request.user)
    ia = Ia.objects.get(owner=userprofile)
    if request.method == 'POST':
        code_form = CodeForm(request.POST)
        if code_form.is_valid():
            useria = code_form.cleaned_data['ia']
            ia.text = useria
            ia.save()

    context = {
        'money': UserProfile.objects.get(user=request.user).money,
        'username': request.user,
        'pageIn': 'editor',
        'code': ia.text,
        'name': request.user,
        'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user)),
        'championnat': UserProfile.objects.get(user=request.user).championship_set.all()[0].name
    }
    return render(request, 'backend/editeur.html', context)

@login_required
def createscript(request):
    userProfile = UserProfile.objects.get(user=request.user)

    ia = Ia.objects.create(owner=userProfile, name=request.user+ "\'s Ia", text=DefaultIa.objects.get(pk=1).text)
    ia.save()

    context = {
        'money': UserProfile.objects.get(user=request.user).money,
        'username': request.user,
        'pageIn': 'editor',
        'code': ia.text,
        'name': request.user
    }

    return render(request, 'backend/editeur.html', context)

@login_required
def editorDetail(request, pk):
    return HttpResponse('page de l editor pour ' + pk)


@login_required
def market(request):
    currentUser = UserProfile.objects.get(user=request.user)

    context = {'money' : currentUser.money,
               'username' : request.user,
               'pageIn': 'market',
               'weapons': Weapon.objects.all(),
               'armors': Armor.objects.all(),
               'caterpillars': Caterpillar.objects.all(),
               'navSys': NavSystem.objects.all(),
               }
    return render(request, 'backend/boutique.html',context)

@login_required
def inventory(request):
    inventory = UserProfile.objects.get(user=request.user).__getInventory__()
    weapon = inventory [0]
    armor = inventory [1]
    caterpillar = inventory [2]
    navSys = inventory [3]
    context = {'money' : UserProfile.objects.get(user=request.user).money,
               'username' : request.user,
               'pageIn': 'inventory',
               'weaponInv': weapon,
               'armorInv': armor,
               'caterInv': caterpillar,
               'navInv': navSys,
               'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user))
               }
    return render(request, 'backend/inventaire.html',context)

@login_required
def parameter(request):

    form = ChangeDataForm()
    form.fields['email'].initial = request.user.email
    form.fields['username'].initial= request.user.username
    context = {'money': UserProfile.objects.get(user=request.user).money,
               'username': request.user,
               'pageIn': 'accueil',
               'agression': UserProfile.objects.get(user=request.user).agression,
               'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user)),
               'form': form}
    return render(request, 'backend/parameter.html',context)

@login_required
def help(request):
    context = {'money' : UserProfile.objects.get(user=request.user).money,
               'username' : request.user,
               'pageIn': 'help'}
    return render(request, 'backend/aide.html',context)

@login_required
def agression(request):
    userProfile = UserProfile.objects.get(user=request.user)
    agressionValue = userProfile.agression
    userProfile.agression = not agressionValue
    userProfile.save()
    return redirect(reverse('backend:index'))

@login_required
def changeStuff(request):
    userProfile = request.user.userprofile
    tank = Tank.objects.get(owner=userProfile)
    itemIn = request.POST.get("item")
    typeIn = request.POST.get("typeItem")
    if int(typeIn) == 1:
        w = getItemByType(itemIn, TypeItem(pk=1))
        if w.attackCost > tank.navSystem.actionValue:
            messages.error(request, "This weapon need %d of PA. Your current PA is: %d" % (w.attackCost, tank.navSystem.actionValue))
        else:
            tank.weapon = w
            tank.save()
    elif int(typeIn) == 2:
        a = getItemByType(itemIn, TypeItem(pk=2))
        tank.armor = a
        tank.save()
    elif int(typeIn) == 3:
        c = getItemByType(itemIn, TypeItem(pk=3))
        tank.caterpillar = c
        tank.save()
    elif int(typeIn) == 4:
        n = getItemByType(itemIn, TypeItem(pk=4))
        tank.navSystem = n
        if tank.weapon.attackCost > n.actionValue:
            inventory = userProfile.__getInventory__()
            weapons = inventory[0]
            avail_wps = []
            for wp in weapons:
                if wp.pk !=  tank.weapon.pk:
                    if wp.attackCost <= n.actionValue:
                        avail_wps.append(wp)
            wps = sorted(avail_wps, key=lambda x: x.attackValue, reverse=True)
            tank.weapon = wps[0]
        tank.save()


    return redirect(reverse('backend:inventory'))

@login_required
def buyStuff (request):
    user = UserProfile.objects.get(user=request.user)
    itemIn = int(request.POST.get("item"))
    typeIn = int(request.POST.get("typeItem"))
    price = int(request.POST.get("price"))

    boolTab = getBoolInventory(user)

    if boolTab[typeIn-1][itemIn-1]:
        context = {'money': UserProfile.objects.get(user=request.user).money,
                   'username': request.user,
                   'pageIn': 'market',
                   'weapons': Weapon.objects.all(),
                   'armors': Armor.objects.all(),
                   'caterpillars': Caterpillar.objects.all(),
                   'navSys': NavSystem.objects.all()
                   }
        messages.error(request, "Équipement déjà acheter")
        return render(request, 'backend/boutique.html', context)
    elif price > user.money :
        context = {'money': UserProfile.objects.get(user=request.user).money,
                   'username': request.user,
                   'pageIn': 'market',
                   'weapons': Weapon.objects.all(),
                   'armors': Armor.objects.all(),
                   'caterpillars': Caterpillar.objects.all(),
                   'navSys': NavSystem.objects.all()
                   }
        messages.error(request, "Vous n'avez pas assez d'argent")
        return render(request, 'backend/boutique.html', context)
    else :
        user.money = user.money - price
        user.save()
        Inventory.objects.create(owner=user,item=itemIn,typeItem=TypeItem(pk=typeIn))
        context = {'money': UserProfile.objects.get(user=request.user).money,
                   'username': request.user,
                   'pageIn': 'market',
                   'weapons': Weapon.objects.all(),
                   'armors': Armor.objects.all(),
                   'caterpillars': Caterpillar.objects.all(),
                   'navSys': NavSystem.objects.all()
                   }
        messages.success(request, "Achat éffectué. Retrouvez l'équipement dans votre inventaire")
        return render(request, 'backend/boutique.html', context)

@login_required
def documentation (request):
    context = {
        'pageIn': 'documentation',
    }
    return render (request,"backend/documentation.html", context)

def faq (request):
    faqs = FAQ.objects.all().order_by('pk')
    context = {
        'pageIn': 'faq',
        'faqs': faqs
    }
    return render (request,"backend/faq_updated.html", context)

@login_required
def tutoriel (request):
    context = {
        'pageIn': 'tutoriels',
    }
    return render(request,"backend/tutorial.html", context)

@login_required
def recherche(request):
    context = {
        'pageIn': 'recherche',
    }
    return render(request,"backend/research.html", context)

@login_required
def developpement (request):
    context = {
        'pageIn': 'developpement',
    }
    return render(request,"backend/developpement.html", context)


class HistoriesView(LoginRequiredMixin, PaginationMixin, ListView):
    """
    History of battles of a user
    """
    template_name = "backend/histories.html"
    model = BattleHistory
    paginate_by = 10

    def get_queryset(self):
        queryset = BattleHistory.objects.filter(Q(user=self.request.user) | Q(opponent=self.request.user))
        queryset = queryset.filter(is_finished=True)
        # queryset = queryset.exclude(opponent=self.request.user) # not display test mode result
        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super(HistoriesView, self).get_context_data(**kwargs)
        context['pageIn'] = 'battle_histories'
        context['championnat'] = UserProfile.objects.get(user=self.request.user).championship_set.all()[0].name
        return context


class AIScriptView(LoginRequiredMixin, ListView):
    """
    Editeur page.
    Using of ListView is not necessary ^^
    """
    template_name = "backend/editeur.html"
    model = Ia

    def get_context_data(self, **kwargs):
        context = super(AIScriptView, self).get_context_data(**kwargs)
        context['pageIn'] = 'editor'
        context['scripts'] = self.request.user.userprofile.ia_set.all()
        context['active_script'] = self.request.user.userprofile.get_active_ai_script()
        context['scripts_count'] = self.request.user.userprofile.ia_set.count()
        context['tank'] = Tank.objects.get(owner=UserProfile.objects.get(user=self.request.user))
        context['championnat'] = UserProfile.objects.get(user=self.request.user).championship_set.all()[0].name

        selected_script_id = self.request.GET.get('script')
        try:
            selected = Ia.objects.get(pk=selected_script_id)
        except:
            selected = context['active_script']

        # Initiate view for adding new AI script
        addnew = self.request.GET.get("addnew", context.get("addnew"))
        if addnew in ["yes", "yes1"]:
            selected = None
            context['addnew'] = "active"
            if addnew == "yes":
                # context['temporary_text'] = DefaultIa.objects.all()[0].text
                context['temporary_text'] = '# Votre code ici \n # Vous pouvez aussi charger un fichier depuis votre ordinateur'
                messages.warning(self.request,"Vous venez de créer un nouveau code. Pensez à le [SAUVEGARDER] ! ")

        context['selected'] = selected
        return context

    def get(self, request, *args, **kwargs):
        """
        Overwrite this func to customize context data
        """
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = len(self.object_list) == 0
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.") % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get("action")

        # When user clicks on Sauvgarder button
        if action == "Sauvegarder":
            addnew = self.request.POST.get("addnew_flag")
            selected_pk = self.request.POST.get("selected_pk")
            ia_name = request.POST.get('ai_name', '')
            text = request.POST.get('ia', '')
            if validate_ai_script(text):
                if addnew == "yes":
                    if request.user.userprofile.ia_set.count() < 5:
                        if text.strip() == '':
                            messages.error(request, "Veuillez taper le code de votre IA")
                        else:
                            Ia.objects.create(
                                owner = request.user.userprofile,
                                name = ia_name,
                                text = text
                            )
                            messages.success(request, "L'Intelligence Artificielle %s a bien été ajoutée" % ia_name)
                    else:
                        messages.error(request, "Vous avez atteint le nombre maximum d'IA autorisé (5)")
                else:
                    try:
                        selected = Ia.objects.get(pk=selected_pk)
                        selected.name = ia_name
                        selected.text = text
                        selected.save()
                        messages.success(request, "L'Intelligence Artificielle [%s] a été mise à jour" % ia_name)
                    except:
                        messages.error(request, "Invalid AI (validate)")
            else:
                # If the valiation is failed, return user's entered data to him
                kwargs['temporary_text'] = text
                kwargs['temporary_name'] = ia_name
                if addnew == "yes":
                    kwargs["addnew"] = "yes1"
                messages.error(request, "Votre code est vide ou contient un contenu bloqué")

        # When user clicks on Activer button
        elif action == "Activer":
            selected_pk = self.request.POST.get("selected_pk")
            try:
                selected = Ia.objects.get(pk=selected_pk)
                request.user.userprofile.change_active_ai(selected)
                messages.success(request, "L'Intelligence Artificielle [%s] a bien été activée" % selected.name)
            except:
                import traceback; print (traceback.format_exc())
                messages.error(request, "Invalid AI (active)")
        # Other action is invalid, just pass through
        else:
            messages.error(request, "Votre code ne correspond pas à la syntaxe Python")
            pass
        return self.get(request, *args, **kwargs)


@login_required
def finish_battle(request):
    """
    Finish a battle immediately
    """
    if request.method == "POST":
        bh_pk = request.POST.get("history_pk")
        mode = request.POST.get('mode')
        script = request.POST.get('script_pk')
        action = request.POST.get('action')

        try:
            battle = BattleHistory.objects.get(pk=bh_pk)
            battle.is_finished = True
            battle.save()

            if battle.is_victorious:
                award_battle(battle.user.userprofile, battle.opponent.userprofile, mode)
            else:
                award_battle(battle.opponent.userprofile, battle.user.userprofile, mode)

            messages.success(request, "Fin du combat")
        except:
            messages.error(request, "Aucun combat en cours")


        if action == "Modifier le script":
            return redirect("/editor/?script="+script)

    return redirect("backend:battle_histories")

class CreateChampionship(FormView):
    template_name = 'backend/championship.html'
    form_class = ChampionshipForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super(CreateChampionship, self).get_context_data(**kwargs)
        context['pageIn'] = 'championship'
        context['all_championship'] = Championship.objects.all()
        context['championnat'] = UserProfile.objects.get(user=self.request.user).championship_set.all()[0].name
        return context

    def form_valid(self, form):
        name = form.cleaned_data['name']
        current_user = UserProfile.objects.get(user=self.request.user)

        try:
            new_name = Championship.objects.get(name=name)
            # print(new_name)

        except ObjectDoesNotExist:
            Championship(name=name).save()
            old_champ_name = current_user.championship_set.all()[0].name

            Championship.objects.get(name=name).players.add(current_user)
            Championship.objects.get(name=old_champ_name).players.remove(current_user)

            messages.success(self.request, "Le championnat [%s] a bien été créé" % name)
            return super(CreateChampionship,self).form_valid(form)

        messages.error(self.request, "Championnat déjà existant, veuillez en créer un autre. Merci")
        return super(CreateChampionship, self).form_valid(form)

@login_required
def change_championship(request):
    if request.method == "POST":

        try:
            new_champ_name = request.POST.get("champ_name")
            # print(new_champ_name)

            champ_pk = Championship.objects.get(name=new_champ_name).pk
            # print(champ_pk)

            current_user = UserProfile.objects.get(user=request.user)
            # print(current_user)

            old_champ_name = current_user.championship_set.all()[0].name
            # print(old_champ_name)


            Championship.objects.get(name=new_champ_name).players.add(current_user)
            Championship.objects.get(name=old_champ_name).players.remove(current_user)

            current_champ_name = current_user.championship_set.all()[0].name
            print(current_champ_name)

            messages.success(request, "Vous avez rejoint %s" % new_champ_name)
        except:
            messages.error(request, "Erreur changement de championnat")



    return redirect("backend:index")

@login_required
def change_password(request):
    current_user = UserProfile.objects.get(user=request.user)
    champ_pk = UserProfile.objects.get(user=request.user).championship_set.all()[0].pk

    if request.method == 'POST':
        # form = PasswordChangeForm(request.user, request.POST)
        form = SetPasswordForm(request.user, request.POST)
        print(form.errors)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Votre mot de passe a bien été mise à jour !')
            return redirect('backend:index')
        else:
            messages.error(request, 'Veuillez corriger le ou les erreurs ci-dessous')
    else:
        form = SetPasswordForm(request.user)
    return render(request, 'backend/change_password.html', {
        'money': UserProfile.objects.get(user=request.user).money,
        'username': request.user,
        'pageIn': 'change_password',
        # 'point' : UserProfile.objects.get(user=request.user).exp,
        'agression': UserProfile.objects.get(user=request.user).agression,
        'tank': Tank.objects.get(owner=UserProfile.objects.get(user=request.user)),
        'scripts': request.user.userprofile.ia_set.all(),
        'active_script': request.user.userprofile.get_active_ai_script(),
        'players': UserProfile.objects.exclude(pk=current_user.pk),
        # 'classement' : UserProfile.objects.order_by('-exp'),
        'classement': Championship.objects.get(pk=champ_pk).players.all(),
        'all_championship': Championship.objects.all(),
        'championnat': UserProfile.objects.get(user=request.user).championship_set.all()[0].name,
        'form': form
    })