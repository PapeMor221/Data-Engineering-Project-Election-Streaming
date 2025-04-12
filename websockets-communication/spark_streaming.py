from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, count
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
import json
import websockets
import asyncio

# Création de la session Spark
spark = SparkSession.builder \
    .appName("ElectionStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Définition du schéma basé sur le générateur Kafka
schema = StructType([
    StructField("voterId", StringType(), True),
    StructField("candidateName", StringType(), True),
    StructField("sexe", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("pollingStationId", IntegerType(), True),
    StructField("votingCenterId", IntegerType(), True),
    StructField("region", StringType(), True),
    StructField("timestamp", TimestampType(), True)
])

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "votes") \
    .option("startingOffsets", "latest") \
    .load()

df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Agrégations
votes_par_candidat = df.groupBy("candidateName").count().orderBy("count", ascending=False)

async def send_data(df, epoch_id):
    results = df.toJSON().collect()
    async with websockets.connect("ws://websocket_server:8765") as websocket:
        await websocket.send(json.dumps(results))

def process_batch(df, epoch_id):
    """Synchronous function to run the asynchronous send_data."""
    asyncio.run(send_data(df, epoch_id))

# Écriture du stream dans la console
query = votes_par_candidat.writeStream \
    .outputMode("complete") \
    .foreachBatch(process_batch) \
    .start()

query.awaitTermination()