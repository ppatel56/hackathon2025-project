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

df = spark.read.option("delimiter", ",").option("header", "true").csv("s3://gifs-infrastructure-ai-hackathon/mock-data/kaggle-dataset/NVDA2.csv")
df.printSchema()
