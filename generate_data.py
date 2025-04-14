import json
import random
import time
from faker import Faker
from kafka import KafkaProducer

# Structure administrative du Sénégal
REGIONS = {
    "Dakar": (["Dakar", "Guédiawaye", "Pikine", "Rufisque"], 26.03),
    "Thiès": (["Mbour", "Thiès", "Tivaouane"], 14.26),
    "Diourbel": (["Bambey", "Diourbel", "Mbacké"], 9.04),
    "Saint-Louis": (["Dagana", "Podor", "Saint-Louis"], 8.02),
    "Louga": (["Kébémer", "Linguère", "Louga"], 6.55),
    "Ziguinchor": (["Bignona", "Oussouye", "Ziguinchor"], 4.38),
    "Matam": (["Kanel", "Matam", "Ranérou-Ferlo"], 4.49),
    "Kaolack": (["Kaolack", "Guinguinéo", "Nioro du Rip"], 6.60),
    "Fatick": (["Fatick", "Foundiougne", "Gossas"], 4.96),
    "Kolda": (["Kolda", "Médina Yoro Foulah", "Vélingara"], 3.78),
    "Tambacounda": (["Bakel", "Goudiry", "Koumpentoum", "Tambacounda"], 4.08),
    "Kaffrine": (["Birkelane", "Kaffrine", "Koungheul", "Malem Hodar"], 3.81),
    "Kédougou": (["Kédougou", "Salémata", "Saraya"], 1.03),
    "Sédhiou": (["Bounkiling", "Goudomp", "Sédhiou"], 2.99)
}

# Préférences électorales par région (biais régionaux)
CANDIDATE_REGIONAL_BIAS = {
    "Dakar": {"Bassirou Diomaye": 4.5, "Amadou": 3.4, "Khalifa": 2.2},
    "Thiès": {"Amadou": 1.9, "Bassirou Diomaye": 3.5, "Idrissa": 2.2},
    "Diourbel": {"Bassirou Diomaye": 2.4, "Khalifa": 0.7, "Idrissa": 0.5},
    "Saint-Louis": {"Amadou": 1.9, "Bassirou Diomaye": 2.2, "Khalifa": 0.6},
    "Louga": {"Amadou": 2.8, "Khalifa": 0.5, "Anta Babacar": 0.8},
    "Ziguinchor": {"Bassirou Diomaye": 2.2, "Khalifa": 0.3, "Idrissa": 0.4},
    "Matam": {"Amadou": 3.3, "Idrissa": 0.4, "Khalifa": 0.2},
    "Kaolack": {"Bassirou Diomaye": 1.8, "Amadou": 0.9, "Khalifa": 0.7},
    "Fatick": {"Bassirou Diomaye": 2.1, "Amadou": 0.6, "Anta Babacar": 0.3},
    "Kolda": {"Bassirou Diomaye": 1.9, "Amadou": 0.8, "Khalifa": 0.5},
    "Tambacounda": {"Amadou": 1.7, "Bassirou Diomaye": 1.4, "Idrissa": 0.6},
    "Kaffrine": {"Bassirou Diomaye": 1.8, "Amadou": 0.9, "Khalifa": 0.5},
    "Kédougou": {"Amadou": 1.6, "Bassirou Diomaye": 1.3, "Issa": 0.4},
    "Sédhiou": {"Bassirou Diomaye": 2.0, "Amadou": 0.7, "Khalifa": 0.3}
}

# Ajout du biais par âge
CANDIDATE_AGE_BIAS = {
    "Bassirou Diomaye": {
        "18-25": 4.8,  # L'espoir de la jeunesse
        "26-35": 4.8,
        "36-45": 3.7,
        "46-60": 3.0,
        "60+": 2.7     # Moins populaire chez les vieux
    },
    "Amadou": {
        "18-25": 1.9,
        "26-35": 2.1,
        "36-45": 1.3,
        "46-60": 2.5,
        "60+": 3.9     # Plus populaire chez les vieux
    },
    "Khalifa": {
        "18-25": 0.3,
        "26-35": 1.0,
        "36-45": 0.2,
        "46-60": 0.4,
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
        "36-45": 0.0,
        "46-60": 0.9,
        "60+": 0.8
    },
    "Anta Babacar": {
        "18-25": 0.2,
        "26-35": 0.3,
        "36-45": 0.5,
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
fake = Faker('fr')

# Création du producteur Kafka
producer = KafkaProducer(bootstrap_servers='kafka:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generer_vote():
    
    regions = list(REGIONS.keys())
    regions_weights = [REGIONS[region][1] for region in regions]  # On récupère les pourcentages
    
    # Sélection d'une région pondérée par son pourcentage
    region = random.choices(regions, weights=regions_weights, k=1)[0]

    
    # Sélection d'une ville aléatoire dans la région
    ville = random.choice(REGIONS[region][0])
    
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
        "region": region,
        "departement": ville,
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