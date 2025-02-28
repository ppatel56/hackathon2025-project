import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, round, avg

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read data from S3
input_path = "s3://input-bucket/stock_data.csv"
output_path = "s3://output-bucket/transformed_stock_data"

df = spark.read.csv(input_path, header=True, inferSchema=True)

# Perform transformations
transformed_df = df.withColumn("price", col("price").cast("double"))
transformed_df = transformed_df.withColumn("volume", col("volume").cast("integer"))
transformed_df = transformed_df.withColumn("market_cap", round(col("price") * col("volume"), 2))
transformed_df = transformed_df.withColumn("avg_price", avg("price").over(Window.partitionBy("symbol")))

# Write transformed data back to S3
transformed_df.write.mode("overwrite").parquet(output_path)

job.commit()