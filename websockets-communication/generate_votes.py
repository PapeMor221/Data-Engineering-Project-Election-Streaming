import json
import random
import time
from kafka import KafkaProducer
from faker import Faker
from datetime import datetime
import pytz

# Initialize Faker
fake = Faker()

# Kafka configuration
KAFKA_BROKER = "kafka:9092"  
KAFKA_TOPIC = "votes"

# Create Kafka producer
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))

candidates = ["Pape Mor", "Kany", "Assane", "Thiane", "Ndaraw"]

def generate_vote():
    return {
        "voterId": fake.uuid4(), 
        "candidateName": random.choice(candidates),
        "sexe": random.choice(["M", "F"]),
        "age": random.randint(18, 90),
        "pollingStationId": random.randint(1, 20),
        "votingCenterId": random.randint(1, 10),
        "region": fake.city(),
        "timestamp": datetime.now(pytz.utc).timestamp()
    }

def send_votes(total_votes=1000):
    """ Send votes at random intervals (multiple votes at the same time) """
    for _ in range(total_votes):
        batch_size = random.randint(1, 10)
        votes = [generate_vote() for _ in range(batch_size)]

        for vote in votes:
            producer.send(KAFKA_TOPIC, value=vote)
            #print(f"Vote sent: {vote}")

        sleep_time = random.uniform(0.1, 1)  
        time.sleep(sleep_time)

if __name__ == "__main__":
    send_votes()