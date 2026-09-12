import datetime
import uuid

def write_chunks_if_not_exists(spark, chunk, source_url, document_id, chunk_table, min_chunk_size):
    c = chunk.replace("'", "\\'").replace('"', '\\"')
    if len(c) >= min_chunk_size:
        data = [[str(uuid.uuid4()), c, source_url, datetime.datetime.now(), document_id]]

        df = spark.createDataFrame(data=data, schema=['chunk_id', 'chunk', 'url', 'timestamp', 'document_id'])

        r = spark.sql(f"""select * from {chunk_table} where chunk = "{c}" """)
        if r.isEmpty():
            df.write.mode("append").format("delta").saveAsTable(chunk_table)