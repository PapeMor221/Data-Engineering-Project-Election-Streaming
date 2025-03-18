import json
import random
import time
from faker import Faker
from kafka import KafkaProducer

# Structure administrative du Sénégal
REGIONS = {
    "Dakar": ["Dakar", "Guédiawaye", "Pikine", "Rufisque"],
    "Thiès": ["Mbour", "Thiès", "Tivaouane"],
    "Diourbel": ["Bambey", "Diourbel", "Mbacké"],
    "Saint-Louis": ["Dagana", "Podor", "Saint-Louis"],
    "Louga": ["Kébémer", "Linguère", "Louga"],
    "Ziguinchor": ["Bignona", "Oussouye", "Ziguinchor"],
    "Matam": ["Kanel", "Matam", "Ranérou-Ferlo"],
    "Kaolack": ["Kaolack", "Guinguinéo", "Nioro du Rip"],
    "Fatick": ["Fatick", "Foundiougne", "Gossas"],
    "Kolda": ["Kolda", "Médina Yoro Foulah", "Vélingara"],
    "Tambacounda": ["Bakel", "Goudiry", "Koumpentoum", "Tambacounda"],
    "Kaffrine": ["Birkelane", "Kaffrine", "Koungheul", "Malem Hodar"],
    "Kédougou": ["Kédougou", "Salémata", "Saraya"],
    "Sédhiou": ["Bounkiling", "Goudomp", "Sédhiou"]
}

# Préférences électorales par région (biais régionaux)
CANDIDATE_REGIONAL_BIAS = {
    "Dakar": {"Bassirou Diomaye": 1.8, "Amadou": 1.2, "Khalifa": 1.1},
    "Thiès": {"Amadou": 1.5, "Bassirou Diomaye": 1.4, "Idrissa": 1.3},
    "Diourbel": {"Bassirou Diomaye": 1.6, "Khalifa": 1.2, "Idrissa": 1.1},
    "Saint-Louis": {"Amadou": 1.5, "Bassirou Diomaye": 1.2, "Khalifa": 1.1},
    "Louga": {"Amadou": 1.4, "Khalifa": 1.1, "Anta Babacar": 1.3},
    "Ziguinchor": {"Bassirou Diomaye": 1.7, "Khalifa": 1.0, "Idrissa": 1.1},
    "Matam": {"Amadou": 1.8, "Idrissa": 1.1, "Khalifa": 1.0},
    "Kaolack": {"Bassirou Diomaye": 1.5, "Amadou": 1.2, "Khalifa": 1.3},
    "Fatick": {"Bassirou Diomaye": 1.6, "Amadou": 1.1, "Anta Babacar": 1.0},
    "Kolda": {"Bassirou Diomaye": 1.5, "Amadou": 1.2, "Khalifa": 1.1},
    "Tambacounda": {"Amadou": 1.4, "Bassirou Diomaye": 1.3, "Idrissa": 1.1},
    "Kaffrine": {"Bassirou Diomaye": 1.5, "Amadou": 1.2, "Khalifa": 1.1},
    "Kédougou": {"Amadou": 1.4, "Bassirou Diomaye": 1.3, "Issa": 1.1},
    "Sédhiou": {"Bassirou Diomaye": 1.6, "Amadou": 1.1, "Khalifa": 1.0}
}

# Ajout du biais par âge
CANDIDATE_AGE_BIAS = {
    "Bassirou Diomaye": {
        "18-25": 1.8,  # L'espoir de la jeunesse
        "26-35": 1.6,
        "36-45": 1.3,
        "46-60": 1.0,
        "60+": 0.7     # Moins populaire chez les vieux
    },
    "Amadou": {
        "18-25": 0.9,
        "26-35": 1.1,
        "36-45": 1.3,
        "46-60": 1.5,
        "60+": 1.4     # Plus populaire chez les vieux
    },
    "Khalifa": {
        "18-25": 0.8,
        "26-35": 1.0,
        "36-45": 1.2,
        "46-60": 1.4,
        "60+": 1.2
    },
    "Idrissa": {
        "18-25": 0.7,
        "26-35": 0.9,
        "36-45": 1.2,
        "46-60": 1.3,
        "60+": 1.2
    },
    "Issa": {
        "18-25": 0.5,
        "26-35": 0.7,
        "36-45": 1.0,
        "46-60": 0.9,
        "60+": 0.8
    },
    "Anta Babacar": {
        "18-25": 1.2,
        "26-35": 1.1,
        "36-45": 0.9,
        "46-60": 0.8,
        "60+": 0.7
    }
}

# Liste des candidats avec leurs informations
candidats = [
    {"nom": "Faye", "prenom": "Bassirou Diomaye", "bureau_vote": "Dakar"},
    {"nom": "Ba", "prenom": "Amadou", "bureau_vote": "Dakar"},
    {"nom": "Seck", "prenom": "Idrissa", "bureau_vote": "Thies"},
    {"nom": "Sall", "prenom": "Khalifa", "bureau_vote": "Kaolack"},
    {"nom": "Sall", "prenom": "Issa", "bureau_vote": "Louga"},
    {"nom": "Ngom", "prenom": "Anta Babacar", "bureau_vote": "Dakar"}
]

# Initialisation de Faker
fake = Faker('fr')  # Configuration pour le Sénégal

# Création du producteur Kafka
producer = KafkaProducer(bootstrap_servers='kafka:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generer_vote():
    # Sélection d'une région aléatoire
    region = random.choice(list(REGIONS.keys()))
    
    # Sélection d'une ville aléatoire dans la région
    ville = random.choice(REGIONS[region])
    
    # Générer un âge aléatoire
    age = random.randint(18, 90)
    
    # Déterminer la tranche d'âge
    if age <= 25:
        age_group = "18-25"
    elif age <= 35:
        age_group = "26-35"
    elif age <= 45:
        age_group = "36-45"
    elif age <= 60:
        age_group = "46-60"
    else:
        age_group = "60+"
    
    # Calculer les probabilités de vote pour chaque candidat en tenant compte des biais
    weighted_candidates = []
    for candidat in candidats:
        base_weight = 1.0
        
        # Appliquer le biais régional si disponible
        regional_bias = CANDIDATE_REGIONAL_BIAS.get(region, {}).get(candidat["prenom"], 1.0)
        
        # Appliquer le biais d'âge si disponible
        age_bias = CANDIDATE_AGE_BIAS.get(candidat["prenom"], {}).get(age_group, 1.0)
        
        # Calculer le poids total
        total_weight = base_weight * regional_bias * age_bias
        
        weighted_candidates.append((candidat, total_weight))
    
    # Normaliser les poids pour obtenir des probabilités
    total_weights = sum(weight for _, weight in weighted_candidates)
    probabilities = [weight/total_weights for _, weight in weighted_candidates]
    
    # Sélectionner un candidat en fonction des probabilités
    selected_candidate = random.choices(
        [candidat for candidat, _ in weighted_candidates],
        weights=probabilities,
        k=1
    )[0]
    
    # Générer le vote
    vote = {
        "cni": fake.ssn(),
        "nom": fake.last_name(),
        "prenom": fake.first_name(),
        "lieu_vote": ville,
        "sexe": random.choice(["M", "F"]),
        "age": age,
        "candidat_nom": selected_candidate["nom"],
        "candidat_prenom": selected_candidate["prenom"],
        "candidat_bureau_vote": selected_candidate["bureau_vote"]
    }
    
    return vote

if __name__ == "__main__":
    while True:
        vote = generer_vote()
        producer.send('votes', value=vote)
        #print(f"Vote envoyé : {vote}")
        time.sleep(0.2)  # Simule un flux en temps réel