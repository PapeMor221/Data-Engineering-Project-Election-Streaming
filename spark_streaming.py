from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2
from kafka import KafkaProducer
import json

spark = SparkSession.builder \
    .appName("ElectionStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

schema = StructType([
    StructField("cni", StringType()),
    StructField("nom", StringType()),
    StructField("prenom", StringType()),
    StructField("lieu_vote", StringType()),
    StructField("sexe", StringType()),
    StructField("age", IntegerType()),
    StructField("candidat_nom", StringType()),
    StructField("candidat_prenom", StringType()),
    StructField("candidat_bureau_vote", StringType())
])

df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka:9092").option("subscribe", "votes").option("startingOffsets", "latest").load()

df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Exemple de traitement : compter les votes par candidat
# votes_par_candidat = df.groupBy("candidat_nom", "candidat_prenom").count().orderBy("count", ascending=False)
# Agrégations
votes_par_candidat = df.groupBy("candidat_nom", "candidat_prenom").count().orderBy("count", ascending=False)
votes_par_lieu_vote = df.groupBy("lieu_vote").count().orderBy("count", ascending=False)
votes_par_sexe = df.groupBy("sexe").count().orderBy("count", ascending=False)

"""
producer_agreg1 = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
"""

# Fonction pour envoyer les données vers Kafka
def send_to_kafka(batch_df, batch_id, topic_name):
    if batch_df.count() == 0:
        return
    
    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    for row in batch_df.toJSON().collect():
        producer.send(topic_name, value=json.loads(row))
    
    producer.flush()
    producer.close()

# Écriture des résultats vers Kafka
query_candidat = votes_par_candidat.writeStream \
    .outputMode("complete") \
    .foreachBatch(lambda df, id: send_to_kafka(df, id, "agreg1")) \
    .start()

query_lieu_vote = votes_par_lieu_vote.writeStream \
    .outputMode("complete") \
    .foreachBatch(lambda df, id: send_to_kafka(df, id, "agreg2")) \
    .start()

query_sexe = votes_par_sexe.writeStream \
    .outputMode("complete") \
    .foreachBatch(lambda df, id: send_to_kafka(df, id, "agreg3")) \
    .start()


"""
def send_votes_par_candidat(batch_df, batch_id):
    for row in batch_df.collect():
        data = {"candidat_nom": row.candidat_nom, "candidat_prenom": row.candidat_prenom, "count": row["count"]}
        print(data)
        producer_agreg1.send('agreg1', value=data)
    producer_agreg1.flush()

def send_votes_par_lieu_vote(batch_df, batch_id):
    for row in batch_df.collect():
        data = {"lieu_vote": row.lieu_vote, "count": row["count"]}
        producer.send('votes_par_lieu_vote', value=data)
    producer.flush()

def send_votes_par_sexe(batch_df, batch_id):
    for row in batch_df.collect():
        data = {"sexe": row.sexe, "count": row["count"]}
        producer.send('votes_par_sexe', value=data)
    producer.flush()

"""




# Fonction pour mettre à jour PostgreSQL
def update_postgres(batch_df, batch_id):
    conn = psycopg2.connect(
        host="postgres",
        database="ElectionDB",
        user="papamor",
        password="papamor"
    )
    cursor = conn.cursor()

    for row in batch_df.collect():
        candidat_nom = row.candidat_nom
        candidat_prenom = row.candidat_prenom
        count = row["count"]

        cursor.execute("""
            INSERT INTO vote_counts (candidat_nom, candidat_prenom, count)
            VALUES (%s, %s, %s)
            ON CONFLICT (candidat_nom, candidat_prenom)
            DO UPDATE SET count = %s;
        """, (candidat_nom, candidat_prenom, count, count))

    conn.commit()
    cursor.close()
    conn.close()



query = votes_par_candidat.writeStream \
    .outputMode("complete") \
    .foreachBatch(update_postgres) \
    .start()
    
"""
query_candidat = votes_par_candidat.writeStream \
    .outputMode("complete") \
    .foreachBatch(send_votes_par_candidat) \
    .start()



query_lieu_vote = votes_par_lieu_vote.writeStream \
    .outputMode("complete") \
    .foreachBatch(send_votes_par_lieu_vote) \
    .start()

query_sexe = votes_par_sexe.writeStream \
    .outputMode("complete") \
    .foreachBatch(send_votes_par_sexe) \
    .start()

"""

# query.awaitTermination()

spark.streams.awaitAnyTermination()