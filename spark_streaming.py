from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("ElectionStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
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

def write_to_postgres(df, epoch_id):
    try:
        
        # Configuration de la connexion PostgreSQL
        postgres_url = "jdbc:postgresql://postgres:5432/election_db"
        postgres_properties = {
            "user": "election_user",
            "password": "election_password",
            "driver": "org.postgresql.Driver"
        }

        # Mettre en cache le DataFrame dans la mémoire de Spark pour éviter de recalculer les transformations chaque fois        
        df_persisted = df.persist()

        # Écrire les votes bruts
        if not df_persisted.isEmpty():
            print("Écriture des votes bruts...")
            df_persisted.write \
                .jdbc(url=postgres_url, 
                      table="votes_raw", 
                      mode="append", 
                      properties=postgres_properties)

            # Écrire les statistiques par candidat
            print("Calcul et écriture des votes par candidat...")
            votes_par_candidat = df_persisted.groupBy("candidat_nom", "candidat_prenom").count()
            votes_par_candidat.write \
                .jdbc(url=postgres_url, 
                      table="votes_par_candidat", 
                      mode="overwrite", 
                      properties=postgres_properties)

            # Statistiques par lieu de vote
            print("Calcul et écriture des votes par lieu...")
            votes_par_lieu = df_persisted.groupBy("lieu_vote", "candidat_nom").count()
            votes_par_lieu.write \
                .jdbc(url=postgres_url, 
                      table="votes_par_lieu", 
                      mode="overwrite", 
                      properties=postgres_properties)

            # Statistiques démographiques
            print("Calcul et écriture des votes par démographie...")
            votes_par_demo = df_persisted.withColumn("tranche_age", 
                                          when(col("age") < 30, "18-29")
                                         .when((col("age") >= 30) & (col("age") < 45), "30-44")
                                         .when((col("age") >= 45) & (col("age") < 60), "45-59")
                                         .otherwise("60+")) \
                              .groupBy("sexe", "tranche_age", "candidat_nom").count()
            votes_par_demo.write \
                .jdbc(url=postgres_url, 
                      table="votes_par_demo", 
                      mode="overwrite", 
                      properties=postgres_properties)
            
            # Libérer la mémoire utilisée pour stocker le Dataframe
            df_persisted.unpersist()
        else:
            print("DataFrame vide, aucune écriture effectuée")
    except Exception as e:
        # Capture et affichage des erreurs
        import traceback
        traceback.print_exc()


# Lecture des données de Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "votes") \
    .option("startingOffsets", "latest") \
    .load()

# Traiter les données 
df_parsed = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Utiliser foreachBatch pour écrire dans PostgreSQL
query = df_parsed.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("update") \
    .start()

query.awaitTermination()