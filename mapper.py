from pyrosm import OSM, get_data
import osmnx as ox
#import osmium as osm
import pandas as pd
import urllib.request
import os

'''class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.osm_data = []
        
    def download_data(self,filename,url):
        if not os.path.exists(filename):
            filename, headers = urllib.request.urlretrieve(url,filename)   

    def tag_inventory(self, elem, elem_type):
        for tag in elem.tags:
            self.osm_data.append([elem_type, 
                                   elem.id, 
                                   elem.version,
                                   elem.visible,
                                   pd.Timestamp(elem.timestamp),
                                   elem.uid,
                                   elem.user,
                                   elem.changeset,
                                   len(elem.tags),
                                   tag.k, 
                                   tag.v])

    def node(self, n):
        self.tag_inventory(n, "node")

    def way(self, w):
        self.tag_inventory(w, "way")

    def relation(self, r):
        self.tag_inventory(r, "relation")

    def dataframe(self):
        data_colnames = ['type', 'id', 'version', 'visible', 'ts', 'uid',
                 'user', 'chgset', 'ntags', 'tagkey', 'tagvalue']
        return pd.DataFrame(self.osm_data, columns=data_colnames).sort_values(by=['type', 'id', 'ts'])   
'''
class MapParser:
    def __init__(self, data):
        """
        reads pbf structured data from file path into OSM object
        """
        self.data=data
        if data is not None:
            self.osm_data = OSM(data)
        else:
            pass
        self.bounded_data=None
        self.route=None
        self.Graph=None
 
    def download_data(self,filename,url):
        if not os.path.exists(filename):
            filename, headers = urllib.request.urlretrieve(url,filename)  

    def to_geojson(self):
        if self.bounded_data:
            return self.bounded_data.to_file(path, driver="GeoJSON")   
        else
            return self.osm_data.to_file(path, driver="GeoJSON")


    def get_pois_from_map(self,poi_filter=None):
        """
        poi_filter 
        poi_filter={"shop": ["alcohol"], "tourism": True, "amenity": ["restaurant", "bar"], "leisure": ["dance"]}
        """
        if self.bounded_data:
            pois= self.bounded_data.get_pois(custom_filter=poi_filter)
        else:
            pois = self.osm_data.get_pois(custom_filter=poi_filter)
    # Merge poi type information into a single column
        pois["shop"] = pois["shop"].fillna(' ')
        pois["amenity"] = pois["amenity"].fillna(' ')
        pois["leisure"] = pois["leisure"].fillna(' ')
        pois["tourism"] = pois["tourism"].fillna(' ')
        pois["poi_type"] = pois["amenity"] + pois["shop"] + pois["leisure"] + pois["tourism"] 
        return pois
    
    def get_network_from_map(self,nodes,network_type,retain_all):
        """
        -inherits .plot() from .get_network()-
        -retain_all=True will remove all unconnected edges
        network_type:
        
            ’walking’

            ’cycling’

            ’driving’

            ’driving+service’

            ’all’
        """
        if self.bounded_data:
            return self.bounded_data.get_network(nodes,network_type,retain_all)
        else:    
            return self.osm_data.get_network(nodes,network_type,retain_all)

    def get_graph_from_map(self,nodes,edges,graph_type):
        """
        get graph from nodes and edges
        Export OSM network to routable graph. Supported output graph types are:
        igraph (default),
        networkx,
        pandana
        """
        if self.bounded_data:
            return self.bounded_data.to_graph(nodes,edges,graph_type, osmnx_compatible=True)
        else:
            return self.osm_data.to_graph(nodes,edges,graph_type, osmnx_compatible=True)



    def get_buildings_from_map(self,custom_filter=None):
        """
        custom_filter={‘building’: [‘residential’, ‘retail’]}
        
        """
        if self.bounded_data:
            return self.bounded_data.get_buildings(custom_filter)
        else:
            return self.osm_data.get_buildings(custom_filter)
    
    def get_bounding_box_from_map(self,boundary_type,name):
        """
        The type of boundaries to parse. Possible values:
        ”administrative” (default)

        ”national_park”

        ”political”

        ”postal_code”

        ”protected_area”

        ”aboriginal_lands”

        ”maritime”

        ”lot”

        ”parcel”

        ”tract”

        ”marker”

        ”all”
        """
        self.bounded_data= OSM(self.data, bounding_box=self.osm_data.get_boundaries(boundary_type,name)['geometry'].values[0])
        return self.bounded_data

    def get_shortest_path_from_map(self,source,target, weight):
        """
        gets shortest path between two nodes

        weight:
        -"length" 
        -"travel_time" (default)


        """

        if self.bounded_data:
            nodes, edges = self.bounded_data.get_network(nodes=True,retain_all=False)
            self.Graph = self.bounded_data.get_graph(nodes,edges,graph_type="networkx")
            source = ox.geocode(source)
            target = ox.geocode(target)
            # Find the closest nodes from the graph
            source_node = ox.get_nearest_node(G, source)
            target_node = ox.get_nearest_node(G, target)
            self.route = ox.shortest_path(G, source_node, target_node, weight="travel_time")
            return self.route
        else:
            nodes, edges = self.osm_data.get_network(nodes=True,retain_all=False)
            self.Graph = self.osm_data.get_graph(nodes,edges,graph_type="networkx")
            source = ox.geocode(source)
            target = ox.geocode(target)
            # Find the closest nodes from the graph
            source_node = ox.get_nearest_node(G, source)
            target_node = ox.get_nearest_node(G, target)
            self.route = ox.shortest_path(G, source_node, target_node, weight="travel_time")
            return self.route

    def get_graph_from_query(self,city,state,country,network_type):
        """
        gets graph from query
        
        """
        self.Graph = ox.graph_from_place({"city": city, "state": state, "country": country}, network_type="drive", truncate_by_edge=True)
        self.Graph = ox.speed.add_edge_speeds(self.Graph)
        self.Graph = ox.speed.add_edge_travel_times(self.Graph)
        return self.Graph

    def get_shortest_path_from_query(self,city,state,country,orig,dest,weight,network_type):
        """
        gets shortest path from a query 
        """
        self.Graph = self.get_graph_from_query(city,state,country,network_type)
        source = ox.geocode(orig)
        target = ox.geocode(dest)
            # Find the closest nodes from the graph
        source_node = ox.get_nearest_node(self.Graph, source)
        target_node = ox.get_nearest_node(self.Graph, target)
        self.route = ox.shortest_path(self.Graph, source_node, target_node, weight)
        return self.route

    def get_shortest_path_from_query_Graph(self,Graph,orig,dest,weight):
        """
        gets shortest path from a graph derived by a query
        """
        source = ox.geocode(orig)
        target = ox.geocode(dest)
            # Find the closest nodes from the graph
        source_node = ox.get_nearest_node(Graph, source)
        target_node = ox.get_nearest_node(Graph, target)
        self.route = ox.shortest_path(Graph, source_node, target_node, weight)
        return self.route

    
