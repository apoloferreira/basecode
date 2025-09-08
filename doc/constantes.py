
REGION = "us-east-1"
DATABASE = "db_ice"
TABLE_POLIGONO = "tb_poligono"
TABLE_INGESTAO = "tb_controle_ingestao"
TABLE_CONTROLE_IMAGEM = "tb_controle_imagem"
TABLE_IMAGEM = "tb_imagem"
S3_ATHENA_OUTPUT = "s3://aws-athena-query-results-891377318910-us-east-1/output/"

# SATELITE IMAGES
SATELLITE_COLLECTION = "sentinel-2-l2a"
STAC_CATALOG = "https://earth-search.aws.element84.com/v1/"
BANDS = {
    "categorical": ["scl"],
    "constants": ["red", "green", "blue", "nir", "nir08", "rededge1", "rededge2", "rededge3", "swir16", "swir22"]
}
CLASSIFICATION_MAP = {
    0: 'no_data',
    1: 'saturated_or_defective',
    2: 'dark_area_pixels',
    3: 'cloud_shadows',
    4: 'vegetation',
    5: 'bare_soils',
    6: 'water',
    7: 'clouds_low_probability_or_unclassified',
    8: 'clouds_medium_probability',
    9: 'clouds_high_probability',
    10: 'thin_cirrus',
    11: 'snow_or_ice'
}
S3_BUCKET_IMAGENS = "data-us-east-1-891377318910"
S3_PREFIX_IMAGENS = "mvp_sensoriamento/images"
S3_BUCKET_METADATA = "data-us-east-1-891377318910"
S3_PREFIX_METADATA = "mvp_sensoriamento/metadata"
