from pyspark.sql import SparkSession
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

spark = SparkSession.builder.appName("Analytics COVID").getOrCreate()

df = spark.read.parquet(args.input)

# ejemplo: conteo total
result = df.count()

analytics_df = spark.createDataFrame([(result,)], ["total_rows"])

analytics_df.write.mode("overwrite").parquet(args.output)

spark.stop()
