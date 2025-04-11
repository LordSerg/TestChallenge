import geopandas as gpd
import matplotlib.pyplot as plt
import random
import math
import os

#for plotting image
def create_subplot():
    _, axes = plt.subplots(figsize=(10.00, 10.00))
    return axes

#for saving plotted image to file
def render_axes(axes, title, output_path):
    axes.set_title(title, fontsize = 14)
    plt.grid(True)
    plt.savefig(output_path, dpi=300)#, bbox_inches='tight')
    print(f"Result image saved as {output_path}")

#find angle of the line relative to horizon (0-180 degrees)
def find_angle(p1,p2):
    if p1[1]>p2[1]:
        p1, p2 = p2, p1
    dx = p1[0]-p2[0]
    dy = p1[1]-p2[1]
    if p2[0]<p1[0]:
        return 180-math.degrees(math.asin(abs(dy)/math.sqrt((dx*dx)+(dy*dy))))
    else:
        return math.degrees(math.asin(abs(dy)/math.sqrt((dx*dx)+(dy*dy))))

#graph structure for the algorithm

#represents a segment of the road and branchings from the segment to other segments
class Vertex: 
    def __init__(self, index, angle, is_used = False, is_starter = False):
        self.edges = []
        self.index = index
        self.angle = angle #relative to horizon
        self.is_starter = is_starter #those segments where we start from
        self.is_used = is_used

    def add_edge(self, vertex):
        self.edges.append(Edge(vertex))

    def get_edges(self): #show all available neighbours of the street
        return [x for x in self.edges if x.vertex.is_used == False]
    
    #def get_num_available_nghbrs(self):
    #    return len([x for x in self.edges if x.vertex.is_used == False])

#connection between two verteces
class Edge:
    def __init__(self, vertex):
        self.vertex = vertex

#the graph itself
class Graph:
    def __init__(self):
        self.verteces = {}

    def add_vertex(self, index, angle, is_used = False, is_starter = False):
        self.verteces[index] = Vertex(index, angle, is_used, is_starter)

    def get_vertex(self, index):
        return self.verteces[index]
    
    def add_edge(self, index1, index2):
        v1 = self.get_vertex(index1)
        v2 = self.get_vertex(index2)
        v1.add_edge(v2)
        v2.add_edge(v1) #since we have undirected graph - we do connection "v1 to v2" and "v2 to v1"

    def set_if_starter(self, index, is_starter):
        self.verteces[index].is_starter = is_starter

#solution 1
def make_decision(curr_vertex, neighbour_list):
    if len(neighbour_list) == 0:
        return None
    if len(neighbour_list) == 1:
        return neighbour_list[0].vertex
    if len(neighbour_list) == 2:
        a = curr_vertex.angle
        a1 = neighbour_list[0].vertex.angle
        a2 = neighbour_list[1].vertex.angle

        dif1 = 90-abs(abs(a-a1)-90)
        dif2 = 90-abs(abs(a-a2)-90)
        #if it's dead end between to other segments
        if dif1>60 and dif2>60:
            return None
        #otherwise we chose the one with the smallest difference
        if dif1<dif2:
            return neighbour_list[0].vertex
        else:
            return neighbour_list[1].vertex
    
    if len(neighbour_list) > 2: # here is same logic as with 2 neighbours, but cycled
        a = curr_vertex.angle
        diffs = []
        for vert in neighbour_list:
            diffs.append(90-abs(abs(a-vert.vertex.angle)-90))
        minimum = min(diffs)
        if minimum>45:
            return None
        return neighbour_list[diffs.index(minimum)].vertex

#solution 2
def make_decision(curr_vertex, neighbour_list, xy):
    if len(neighbour_list) == 0:
        return None
    if len(neighbour_list) == 1:
        return neighbour_list[0].vertex
    cross = list(set(xy[curr_vertex.index]).intersection(set(xy[neighbour_list[0].vertex.index])))[0]
    if len(neighbour_list) == 2:
        #find angle of the subsegment, that attached to the crossroad
        t = xy[curr_vertex.index].index(cross)
        k = 1 if t == 0 else t-1
        a_pt = xy[curr_vertex.index][k]
        a = find_angle(cross, a_pt)

        t = xy[neighbour_list[0].vertex.index].index(cross)
        k = 1 if t == 0 else t-1
        a_pt1 = xy[neighbour_list[0].vertex.index][k]
        a1 = find_angle(cross, a_pt1)

        t = xy[neighbour_list[1].vertex.index].index(cross)
        k = 1 if t == 0 else t-1
        a_pt2 = xy[neighbour_list[1].vertex.index][k]
        a2 = find_angle(cross, a_pt2)

        dif1 = 90-abs(abs(a-a1)-90)
        dif2 = 90-abs(abs(a-a2)-90)
        #if it's dead end between to other segments
        if dif1>60 and dif2>60:
            return None
        #otherwise we chose the one with the smallest difference
        if dif1<dif2:
            return neighbour_list[0].vertex
        else:
            return neighbour_list[1].vertex
    
    if len(neighbour_list) > 2: # here is same logic as with 2 neighbours, but cycled
        t = xy[curr_vertex.index].index(cross)
        k = 1 if t == 0 else t-1
        a_pt = xy[curr_vertex.index][k]
        a = find_angle(cross, a_pt)

        diffs = []
        for vert in neighbour_list:
            t = xy[vert.vertex.index].index(cross)
            k = 1 if t == 0 else t-1
            pt_tmp = xy[vert.vertex.index][k]
            a_tmp = find_angle(cross, pt_tmp)
            diffs.append(90-abs(abs(a-a_tmp)-90))
        minimum = min(diffs)
        if minimum>45:
            return None
        return neighbour_list[diffs.index(minimum)].vertex



#guess what this function does :)
def solve_the_problem(gdf: gpd.GeoDataFrame, output_path: str = None):
    axes = create_subplot()
    #copy the initial data to list of lists, where one element = one segment
    xy = gdf.geometry.apply(lambda geom: list(geom.coords))
    
    '''
    #printing picture by segments
    for _, row in gdf.iterrows():
        if row.geometry.geom_type == "LineString":
            axes.plot(
                row.geometry.xy[0],
                row.geometry.xy[1],
                color=(0,1,0),
                linewidth=1
            )
    '''

    #creating graph

    graph = Graph()
    i = 0
    while(i<len(xy)):#initializing graph
        graph.add_vertex(i,find_angle(xy[i][0],xy[i][-1]))
        i = i+1
    '''
    counter for (begin, end) for each segment overlaping with other begin/end
    every element is a tuple (begin, end)
    'begin' - counts how many branchings are there from the segment if we go to the begin of the segment
    'end' - counts how many branchings are there from the segment if we go to the end of the segment
    '''
    starts_ends_overlaps_count = [(0,0) for x in xy]
    i=0
    j=0
    size = len(xy)
    #calculate whether a segment is starter or no + construct edges of the graph
    while(i<size):
        j=i+1
        while(j<size):
            flag = 0
            if xy[i][0] == xy[j][0]:
                starts_ends_overlaps_count[i] = (starts_ends_overlaps_count[i][0]+1,starts_ends_overlaps_count[i][1])
                starts_ends_overlaps_count[j] = (starts_ends_overlaps_count[j][0]+1,starts_ends_overlaps_count[j][1])
                flag = 1
            if xy[i][0] == xy[j][-1]:
                starts_ends_overlaps_count[i] = (starts_ends_overlaps_count[i][0]+1,starts_ends_overlaps_count[i][1])
                starts_ends_overlaps_count[j] = (starts_ends_overlaps_count[j][0],starts_ends_overlaps_count[j][1]+1)
                flag = 1
            if xy[i][-1] == xy[j][0]:
                starts_ends_overlaps_count[i] = (starts_ends_overlaps_count[i][0],starts_ends_overlaps_count[i][1]+1)
                starts_ends_overlaps_count[j] = (starts_ends_overlaps_count[j][0]+1,starts_ends_overlaps_count[j][1])
                flag = 1
            if xy[i][-1] == xy[j][-1]:
                starts_ends_overlaps_count[i] = (starts_ends_overlaps_count[i][0],starts_ends_overlaps_count[i][1]+1)
                starts_ends_overlaps_count[j] = (starts_ends_overlaps_count[j][0],starts_ends_overlaps_count[j][1]+1)
                flag = 1
            
            if flag == 1:
                graph.add_edge(i,j)
            j=j+1
        
        #graph.add_vertex(i,calculate_angle(xy[i][0],xy[i][-1]),True if starts_ends_overlaps_count[i][0] == 0 or starts_ends_overlaps_count[i][1] == 0 else False)
        graph.set_if_starter(i,True if starts_ends_overlaps_count[i][0] == 0 or starts_ends_overlaps_count[i][1] == 0 else False)
        i=i+1
    
    streets = []# list of the streets
    street_index = -1#index for streets

    #list of starter verteces
    starter_list = [ix for ix in range(size) if graph.get_vertex(ix).is_starter == True]
    '''
    for i in range(size):
        if graph.get_vertex(i).is_starter == True:
            starter_list.append(i)
    '''
    
    #here starts the algorithm itself:
    while(len(starter_list)>0):
        for i in starter_list:
            v = graph.get_vertex(i)
            if v.is_used == False:
                if len(v.get_edges())>0:
                    streets.append([])
                    street_index = street_index + 1
                    #find first crossroad point
                    i1 = v.get_edges()[0].vertex.index
                    i2 = v.index
                    tmp = xy[i2].index(list(set(xy[i1]).intersection(set(xy[i2])))[0]) #[x for x in xy[i1] if (x in xy[i2])][0]
                    #for pt in xy[i1]:
                    #    if pt in xy[i2]:
                    #        crossroad = pt
                    #        break
                    if tmp == 0:
                        tmp = -1
                    else:
                        tmp = 0
                    crossroad = xy[i2][tmp]
                    #cycle of walking around
                    while(True):

                        #since available neighbours can be on both sides of the segment - we filter only those, that in the right direction
                        available_nghbrs = [x for x in v.get_edges() if (crossroad not in xy[x.vertex.index])]
                        
                        #make decision, which segment will be next added to the street
                        #solution 1
                        #choosen_one = make_decision(v, available_nghbrs)

                        #solution 2
                        choosen_one = make_decision(v, available_nghbrs, xy)
                        
                        #if the coosen_one is non-empty vertex
                        if choosen_one != None:
                            crossroad = list(set(xy[v.index]).intersection(set(xy[choosen_one.index])))[0] #[x for x in xy[v.index] if (x in xy[choosen_one.index])][0]
                            streets[street_index].append(v.index)
                            graph.verteces[v.index].is_used = True
                            v = graph.verteces[choosen_one.index]
                        else: # if choosen is empty vertex - that means that this is the end of the street
                            streets[street_index].append(v.index)
                            graph.verteces[v.index].is_used = True
                            break
                else:#if there are no other segments
                    streets.append([])
                    street_index = street_index + 1
                    streets[street_index].append(v.index)
                    graph.verteces[v.index].is_used = True
        
        #after the round is over - there could be some segments that were left untoched
        #so look for starter segments out of those ones, wich left untoched

        starter_list.clear()
        for i in range(size):
            if graph.get_vertex(i).is_used == False:
                #find how many intersection points are there between vertex and its neighbours
                vrtx = graph.get_vertex(i)
                points = [list(set(xy[x.vertex.index]).intersection(set(xy[i])))[0] for x in vrtx.get_edges()]
                #if there is only one or less unique intersection point - the vertex is a starter
                if len(set(points)) <= 1:
                    starter_list.append(i)
    
    #draw all streets
    for street in streets:
        street_col = (random.random(),random.random(),random.random())
        for segment in street:
            X, Y = map(list, zip(*(xy[segment])))
            axes.plot(
                X,
                Y,
                color = street_col,
                linewidth = 2
            )
    
    #output of result to file
    render_axes(axes, f"Visualization of streets [{output_path}]", output_path)

if __name__ == "__main__":
    gdf = gpd.read_file("sample/roads.shp")
    solve_the_problem(gdf, "output/solution.png")