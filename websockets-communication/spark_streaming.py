from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import asyncio
import websockets
import json

# Initialize Spark session
spark = SparkSession.builder \
    .appName("ElectionStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Define schema for incoming vote data
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

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "votes") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

WEBSOCKET_URL = "ws://websocket_server:8765"

# Fonction générique pour envoyer toutes les agrégations en un seul message
async def send_all_to_websocket(payload: dict):
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            await websocket.send(json.dumps(payload))
    except Exception as e:
        print(f"****WebSocket Error : **** {e}")


def safe_agg(df, agg_name, func):
    """Exécute une agrégation en attrapant les exceptions."""
    try:
        result = func(df)
        if result and not result.rdd.isEmpty():
            return (agg_name, [json.loads(row) for row in result.toJSON().collect()])
    except Exception as e:
        print(f"[⚠️] Erreur dans l'agrégation '{agg_name}': {e}")
    return (agg_name, [])


def aggregate_all(df):
    df_with_age_group = df.withColumn(
        "age_group",
        when(col("age") <= 25, "18-25")
        .when(col("age") <= 35, "26-35")
        .when(col("age") <= 45, "36-45")
        .when(col("age") <= 60, "46-60")
        .otherwise("60+")
    )

    aggregations = [
        ("votes_par_candidat", lambda d: d.groupBy("candidat_nom", "candidat_prenom").agg(count("*").alias("total_votes"))),
        ("votes_par_lieu", lambda d: d.groupBy("candidat_nom", "candidat_prenom", "lieu_vote").agg(count("*").alias("votes_par_lieu"))),
        ("votes_par_age", lambda d: df_with_age_group.groupBy("candidat_nom", "candidat_prenom", "age_group").agg(count("*").alias("votes_par_age"))),
        ("votes_par_sexe", lambda d: d.groupBy("candidat_nom", "candidat_prenom", "sexe").agg(count("*").alias("votes_par_sexe")))
    ]

    results = {}
    for name, func in aggregations:
        key, value = safe_agg(df, name, func)
        if value: 
            results[key] = value

    return results

def process_batch(df, batch_id):
    print(f"Traitement du batch : {batch_id}")
    payload = aggregate_all(df)
    if payload:
        asyncio.run(send_all_to_websocket(payload))
    else:
        print("Aucune donnée à envoyer pour ce batch.")

def send_combined_batch(aggs_df: dict, batch_id: int):
    aggregated_payload = {}

    for agg_type, df in aggs_df.items():
        try:
            if df.rdd.isEmpty():
                continue

            # Convertir chaque ligne du DataFrame en JSON string
            json_rows = df.toJSON().collect()

            if json_rows:
                # Transformer les JSON strings en dictionnaires Python
                aggregated_payload[agg_type] = [json.loads(row) for row in json_rows]

        except Exception as e:
            print(f"Erreur lors du traitement de l'agrégation '{agg_type}': {e}")

    if aggregated_payload:
        asyncio.run(send_all_to_websocket(aggregated_payload))


# Démarrage d’un seul stream centralisé
try:
    query = df.writeStream \
        .outputMode("update") \
        .foreachBatch(process_batch) \
        .start()

    query.awaitTermination()

except Exception as e:
    print(f"Erreur dans le streaming Spark : {e}")