import geopandas as gpd


shapefile_path = "ke_shp/ke.shp"         
geojson_path = "static/data/subcounties.geojson" 


gdf = gpd.read_file(shapefile_path)


print("Columns in shapefile:", gdf.columns)



gdf = gdf[['source', 'name', 'geometry']]


gdf = gdf.rename(columns={'source': 'COUNTY', 'name': 'SUBCOUNTY'})


gdf.to_file(geojson_path, driver="GeoJSON")

print(f" GeoJSON saved to {geojson_path}")