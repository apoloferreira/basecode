import sys
import os
from pyspark.context import SparkContext
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

sys.path.append(os.getcwd())
os.environ.setdefault("AWS_REGION", "us-east-1")
from negocio import (  # noqa: E402
    get_polygon_record_by_day, define_start_date, search_images, load_dataset,
    process_images, save_images, save_metadata, update_ingestion_record,
    insert_image_control_table, update_image_table, get_ingestion_record,
    count_dataset_pixels
)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "ID_POLIGONO"])

sc = SparkContext()
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


ID_POLIGONO = args["ID_POLIGONO"]
print(f"Id Poligono: {ID_POLIGONO}")

record_polygon = get_polygon_record_by_day(ID_POLIGONO)
record_ingestion = get_ingestion_record(record_polygon)

start_date = define_start_date(record_polygon, record_ingestion)
print(f"Start Date: {start_date}")

if not start_date:
    print("start_date nulo. Encerrando job!")
    job.commit()
    os._exit()
    sys.exit(200)

stac_metadata = search_images(record_polygon, start_date)

ds = load_dataset(record_polygon, stac_metadata)
df_image = process_images(ds, ID_POLIGONO)

save_images(record_polygon['id_poligono'], ds)
save_metadata(record_polygon['id_poligono'], stac_metadata)

update_ingestion_record(record_ingestion, start_date)

number_of_pixles = count_dataset_pixels(ds)
insert_image_control_table(record_polygon, number_of_pixles)
update_image_table(df_image)
