from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2

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
votes_par_candidat = df.groupBy("candidat_nom", "candidat_prenom").count().orderBy("count", ascending=False)

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

query.awaitTermination()