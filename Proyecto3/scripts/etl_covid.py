from pyspark.sql import SparkSession
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

spark = SparkSession.builder.appName("ETL COVID").getOrCreate()

df = spark.read.parquet(args.input)

df_clean = df.dropDuplicates()

df_clean.write.mode("overwrite").parquet(args.output)

spark.stop()
