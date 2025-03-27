from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2

# Initialize Spark session with necessary configurations
spark = SparkSession.builder \
    .appName("ElectionStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

# Reduce log verbosity
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

# Read data from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "votes") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Parse JSON data
df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Add age group column for age-based aggregation
df_with_age_group = df.withColumn(
    "age_group",
    when(col("age") <= 25, "18-25")
    .when(col("age") <= 35, "26-35")
    .when(col("age") <= 45, "36-45")
    .when(col("age") <= 60, "46-60")
    .otherwise("60+")
)

# 1. Aggregate votes by candidate
votes_par_candidat = df \
    .groupBy("candidat_nom", "candidat_prenom") \
    .agg(count("*").alias("total_votes"))

# 2. Aggregate votes by candidate and location
votes_par_lieu = df \
    .groupBy("candidat_nom", "candidat_prenom", "lieu_vote") \
    .agg(count("*").alias("votes_par_lieu"))

# 3. Aggregate votes by candidate and age group
votes_par_age = df_with_age_group \
    .groupBy("candidat_nom", "candidat_prenom", "age_group") \
    .agg(count("*").alias("votes_par_age"))

# 4. Aggregate votes by candidate and gender
votes_par_sexe = df \
    .groupBy("candidat_nom", "candidat_prenom", "sexe") \
    .agg(count("*").alias("votes_par_sexe"))

# Function to update the vote_counts table
def update_vote_counts(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    
    try:
                
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="postgres",
            database="ElectionDB",
            user="papamor",
            password="papamor"
        )        
        cursor = conn.cursor()
    
        # Process each row and update database
        for row in batch_df.collect():
            cursor.execute("""
                INSERT INTO vote_counts (candidat_nom, candidat_prenom, total_votes)
                VALUES (%s, %s, %s)
                ON CONFLICT (candidat_nom, candidat_prenom)
                DO UPDATE SET total_votes = %s;
            """, (row.candidat_nom, row.candidat_prenom, row.total_votes, row.total_votes))    
        
        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating vote_counts: {e}")

# Function to update the votes_par_lieu table
def update_votes_par_lieu(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="postgres",
            database="ElectionDB",
            user="papamor",
            password="papamor"
        )        
        cursor = conn.cursor()
        
        for row in batch_df.collect():
            cursor.execute("""
                INSERT INTO votes_par_lieu (candidat_nom, candidat_prenom, lieu_vote, votes_par_lieu)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (candidat_nom, candidat_prenom, lieu_vote)
                DO UPDATE SET votes_par_lieu = %s;
            """, (row.candidat_nom, row.candidat_prenom, row.lieu_vote, row.votes_par_lieu, row.votes_par_lieu))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating votes_par_lieu: {e}")

# Function to update the votes_par_age table
def update_votes_par_age(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="postgres",
            database="ElectionDB",
            user="papamor",
            password="papamor"
        )        
        cursor = conn.cursor()
        
        for row in batch_df.collect():
            cursor.execute("""
                INSERT INTO votes_par_age (candidat_nom, candidat_prenom, age_group, votes_par_age)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (candidat_nom, candidat_prenom, age_group)
                DO UPDATE SET votes_par_age = %s;
            """, (row.candidat_nom, row.candidat_prenom, row.age_group, row.votes_par_age, row.votes_par_age))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating votes_par_age: {e}")

# Function to update the votes_par_sexe table
def update_votes_par_sexe(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="postgres",
            database="ElectionDB",
            user="papamor",
            password="papamor"
        )
        cursor = conn.cursor()
        
        for row in batch_df.collect():
            cursor.execute("""
                INSERT INTO votes_par_sexe (candidat_nom, candidat_prenom, sexe, votes_par_sexe)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (candidat_nom, candidat_prenom, sexe)
                DO UPDATE SET votes_par_sexe = %s;
            """, (row.candidat_nom, row.candidat_prenom, row.sexe, row.votes_par_sexe, row.votes_par_sexe))    
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating votes_par_sexe: {e}")

# Start streaming queries with proper error handling
try:
    # Write aggregated data to PostgreSQL
    query1 = votes_par_candidat.writeStream \
        .outputMode("update") \
        .foreachBatch(update_vote_counts) \
        .start()
    
    query2 = votes_par_lieu.writeStream \
        .outputMode("update") \
        .foreachBatch(update_votes_par_lieu) \
        .start()
    
    query3 = votes_par_age.writeStream \
        .outputMode("update") \
        .foreachBatch(update_votes_par_age) \
        .start()
    
    query4 = votes_par_sexe.writeStream \
        .outputMode("update") \
        .foreachBatch(update_votes_par_sexe) \
        .start()
    
    # Wait for all queries to terminate
    spark.streams.awaitAnyTermination()
    
except Exception as e:
    print(f"Error in streaming application: {e}")