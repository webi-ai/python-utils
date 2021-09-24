from quart import Quart
from mapper import MapParser
import pandas as pd
from pyrosm import OSM, get_data
import osmnx as ox
import urllib.parse



app = Quart(__name__)



@app.route("/buildings/<string:city_name>")
async def buildings(city_name):
    data = get_data(city_name)
    mapper = MapParser(data=data)
    buildings = mapper.get_buildings_from_map()
    return buildings[buildings["building"]!= "yes"][["geometry","building"]].to_json()



@app.route("/pois/<string:city_name>")
async def pois(city_name):
    data = get_data(city_name)
    mapper = MapParser(data=data)
    pois = mapper.get_pois_from_map(poi_filter={"shop": True, "tourism": True, "amenity": True, "leisure": True})
    return pois[["geometry","name","poi_type"]].to_json()

@app.route("/geocode/<string:city_name>/<string:state_name>/<string:country_name>")
def geocode(city_name, state_name, country_name):
    return str(ox.geocode(f'{city_name}, {state_name}, {country_name}'))
    


if __name__ == "__main__":
    app.run(debug=True)