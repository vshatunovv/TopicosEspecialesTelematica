import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'TARGET_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

TARGET_BUCKET = args['TARGET_BUCKET']

# Leer la tabla desde Glue Catalog
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="covid_catalog_db",
    table_name="covid_complement"
)

# Escribir en S3 como parquet
output_path = f"s3://{TARGET_BUCKET}/raw/rds/covid_complement/"
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={"path": output_path},
    format="parquet"
)

job.commit()
