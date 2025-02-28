import sys
import boto3
import io
import pandas as pd
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import lit

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job.commit()

print('hello')

bucket_name = 'gifs-infrastructure-ai-hackathon'
key = 'mock-data/test_file.txt'
converter_dict = {
    'field1': str,
    'field2': str,
    'field3': str
}

s3_client = boto3.client('s3')
data = s3_client.get_object(Bucket=bucket_name, Key=key)
pandas_df = pd.read_csv(io.BytesIO(data['Body'].read()), sep='~', converters=converter_dict)
print(pandas_df.head(10))

spark_df = spark.createDataFrame(pandas_df)
spark_df = spark_df.withColumn("field4", lit('i am a new column'))
print(spark_df.count())

spark_df.write.format('csv').option('header', 'true').mode("overwrite").save("s3://gifs-infrastructure-ai-hackathon/mock-data/out")

print('wrote file')
