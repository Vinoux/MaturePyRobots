# Informations générales
Nom du projet: MaturePyRobot (basé sur https://github.com/huacayacauh/WebPyRobot )

Présentation :
- WebPyRobot est un jeu de type “bac à sable” (sandbox) dont le but est de faire affronter son IA (Intelligence Artificielle) contrôlant un tank contre l’IA d’un autre joueur. 
Le gagnant de la partie est celui dont le tank est encore en vie à la fin de l’affrontement.

- WebPyRobot se présente sous la forme d’un site web. Chaque utilisateur possède un compte pour pouvoir sauvegarder ses IA. 

- Cette application web permet aux personnes voulant s’initier à la programmation de développer, avec des outils simples, une intelligence artificielle. Cette plateforme web complète permet l’initiation, l’explication et la pratique de la programmation pour tout le monde possédant uniquement un périphérique permettant de naviguer sur le web.

- L'objectif de MaturePyRobot est d'en faire une application ergonomique et installable sans soucis. En ajoutant des fonctionnalités de qualité de vie (QOL) afin de peaufinner l'application et en faire un produit mature prêt à exploitation.

Auteurs 2018 :
2017 : MaturePyRobot :
- [Brice MAUSSANG](mailto:brice.maussang@etu.univ-amu.fr) : BBprog
- [Dan LE](mailto:dan.le@etu.univ-amu.fr) : Hibouh
- [Cédric SANCHEZ](mailto:cedric.sanchez@etu.univ-amu.fr) : Biebz
- [Vinciane LE MAGUET](mailto:vinciane.le-maguet@etu.univ-amu.fr) : Vinoux et vinouteug

Anciens auteurs 2017 :
2017 : MaturePyRobot :
- [Alex ANDRIAMAHALEO](mailto:alex.andriamahaleo@etu.univ-amu.fr)
- [Thai Son NGUYEN](mailto:thai-son.nguyen@etu.univ-amu.fr)
- [Ayoub EL-YOUSFI](mailto:ayoub.elyousfi@etu.univ-amu.fr)
- [Samy SELAIMIA](mailto:samy.selaimia@etu.univ-amu.fr)

Ancien projet WebPyRobot :
- [Michaël GILETA](mailto:michael.gileta@etu.univ-amu.fr)
- [Mickaël BERNARDINI](mailto:mickael.bernardini@etu.univ-amu.fr)
- [Yohan ROUX](mailto:yohan.roux@etu.univ-amu.fr)
- [Sylvain DE BARROS](mailto:sylvain.debarros@etu.univ-amu.fr)

Encadrants:
2018 MaturePyRobot :
- Pablo ARRIGHI
- Kevin PERROT
- Laurent TICHIT

2017 MaturePyRobot :
- Pablo ARRIGHI
- Kevin PERROT

WebPyrobot :
- Pablo ARRIGHI
- Stefano FACCHINI

# Manuel d'utilisation
## Utilisation de Base
1. S'inscrire
2. Se connecter
3. Aller dans Éditeur et coder son IA en Python
4. Pour les fonctions propres au jeu, aller dans Documentation 
5. Tester son IA si besoin
6. Sur la page d'accueil cliquer sur Battle pour lancer un combat
7. Si votre IA est prète à vous rapporter de l'argent, désactiver le mode Passif pour combattre pendant votre absence.

## Améliorer son Tank
1. Dans la Boutique avec l'argent gagner en combattant acheter des équipements pour les tanks
2. Dans Inventaire modifier l'équipement de votre tank

# Structure
- /WebPyRobot - Dossier du serveur web Django
- /WebPyRobot/WebPyRobot - Dossier des configs de Django
- /WebPyRobot/backend - Dossier possédant les pages et les intéraction
- /WebPyRobot/init.sh - Permet d'initialiser django pour le projet
- /WebPyRobot/manage.py - Permet de lancer des commandes Django
- /WebPyRobot/run.sh - Permet de lancer le serveur web

# TODO
- Gestion Arbre de compétences ( demande d'y réfléchir un peu plus, est-ce que cela à sa place dans ce projet ?)
- Galerie d'images items

#Thechnologie/logiciels utilisés:
- Python, HTML, CSS, JavaScript, JQuery, SQLite
- Pip, Django, Pillow, CodeMirror, Materialize, ExCanvas
- Trello, Balsamiq Mockup, StarUML
