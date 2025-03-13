import json
import random
import time
from faker import Faker
from kafka import KafkaProducer

#Utiliser fr ou fr_FR
fake = Faker('fr')  # Configuration pour le Sénégal
candidats = [
    {"nom": "Diomaye", "prenom": "Faye", "bureau_vote": "Dakar"},
    {"nom": "Amadou", "prenom": "Ba", "bureau_vote": "Thies"},
    {"nom": "Idrissa", "prenom": "Seck", "bureau_vote": "Ziguinchor"},
    {"nom": "Khalifa", "prenom": "Sall", "bureau_vote": "Kaolack"},
    {"nom": "Issa", "prenom": "Sall", "bureau_vote": "Saint-Louis"},
    {"nom": "Anta Babacar", "prenom": "Ngom", "bureau_vote": "Louga"}
]

producer = KafkaProducer(bootstrap_servers='kafka:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generer_vote():
    candidat = random.choice(candidats)
    vote = {
        "cni": fake.ssn(),
        "nom": fake.last_name(),
        "prenom": fake.first_name(),
        "lieu_vote": fake.city(),
        "sexe": random.choice(["M", "F"]),
        "age": random.randint(18, 90),
        "candidat_nom": candidat["nom"],
        "candidat_prenom": candidat["prenom"],
        "candidat_bureau_vote": candidat["bureau_vote"]
    }
    return vote

if __name__ == "__main__":
    while True:
        vote = generer_vote()
        producer.send('votes', value=vote)
        #print(f"Vote envoyé : {vote}")
        time.sleep(0.2)  # Simule un flux en temps réel