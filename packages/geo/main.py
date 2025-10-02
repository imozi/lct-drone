import duckdb

duckdb.execute("INSTALL spatial;")
duckdb.execute("LOAD spatial;")

duckdb.execute("SET s3_region='us-west-2';")

output_file = "division.gpkg"

duckdb.execute(f"""
COPY(
  SELECT
    id,
    division_id,
    names.primary,
    geometry  -- DuckDB v.1.1.0 will autoload this as a `geometry` type
  FROM
    read_parquet('s3://overturemaps-us-west-2/release/2025-09-24.0/theme=divisions/type=division_area/*', hive_partitioning=1)
  WHERE
    subtype = 'region'
    AND country = 'RU'
    AND class = 'maritime'
) TO {output_file} WITH (FORMAT GDAL, DRIVER 'GPKG');
""")

print(f"Overture Maps data downloaded to {output_file}")
duckdb.close()
