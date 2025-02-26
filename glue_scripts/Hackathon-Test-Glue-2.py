import sys
import boto3
import io
import pandas as pd
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
import pyspark.sql.functions as F
import pyspark.sql.types
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job.commit()

df1 = spark.read.option("delimiter", ",").option("header", "true").csv("s3://gifs-infrastructure-ai-hackathon/mock-data/kaggle-dataset/NVDA2.csv")
df1.printSchema()
df1.show()

df2 = spark.read.option("delimiter", ",").option("header", "true").csv("s3://gifs-infrastructure-ai-hackathon/mock-data/kaggle-dataset/walmart_stock_prices.csv")
df2.printSchema()
df2.show()

# Get the common columns between the two
common_columns = list(set(df1.columns) & set(df2.columns))
print(common_columns)

df1_common = df1.select(*common_columns)
df2_common = df2.select(*common_columns)

df1_common = df1_common.selectExpr(
    "cast(Date as date) as Date",
    "cast(Close as double) as Close",
    "cast(High as double) as High",
    "cast(Low as double) as Low",
    "cast(Open as double) as Open",
    "cast(Volume as double) as Volume"
)

df2_common = df2_common.selectExpr(
    "cast(Date as date) as Date",
    "cast(Close as double) as Close",
    "cast(High as double) as High",
    "cast(Low as double) as Low",
    "cast(Open as double) as Open",
    "cast(Volume as double) as Volume"
)

df_final = df1_common.join(df2_common, [common_columns], how="left")
new_csv_file = "final_stocks.csv"
# Write to S3
output_path = "s3://gifs-infrastructure-ai-hackathon/write-data/final_stocks"
df_final.write \
  .mode("overwrite") \
  .option("header", "true") \
  .csv(output_path)
