from handlers.myRequestHandler import MyRequestHandler
import lib.semanticweb as semanticweb
import os,sys
sys.path.append(os.path.realpath('.')) 
import settings

class MainHandler(MyRequestHandler):
    def get(self):
        self.write('<a href="%s">list food chains of user01</a>' %
                   self.reverse_url("foodchain", "user01"))

class GraphsHandler(MyRequestHandler):
    def get(self):
        graphs = semanticweb.listGraphs()
        MyRequestHandler.resp(self,200,{"graphs":graphs})

class GraphHandler(MyRequestHandler):
    # list all points and relatios in this food web
    def get(self, graphName):
        if  not semanticweb.graphExists(graphName):
            MyRequestHandler.resp(self, 500, "graph does not exist")
        resrouces = semanticweb.listDBresource(graphName)
        relations = semanticweb.listFoodRelations(graphName)
        MyRequestHandler.resp(self,200,{"resources":resrouces,
            "relations":relations})
    # craete new grah
    def post(self, graphName):
        graphs = semanticweb.listGraphs()
        if semanticweb.graphExists(graphName):
            MyRequestHandler.resp(self,500,"graph already exists")
        else:
            semanticweb.initGraph(graphName)
            MyRequestHandler.resp(self)
    # delete graph
    def delete(self, graphName):
        if semanticweb.graphExists(graphName):
            semanticweb.dropGraph(graphName)
            MyRequestHandler.resp(self,204)
        else:
            MyRequestHandler.resp(self,500,"graph does not exist")

class RelationHandler(MyRequestHandler):
    # add a relation in food web
    def post(self, graphName, food, eater):
        if semanticweb.graphExists(graphName):
            code = semanticweb.addRelation(graphName,str(food).capitalize(),str(eater).capitalize())
            MyRequestHandler.resp(self,code["code"])
        else:
            MyRequestHandler.resp(self,500,"graph does not exist")
    # delete a relation in food web
    def delete(self, graphName, food, eater):
        if  not semanticweb.graphExists(graphName):
            MyRequestHandler.resp(self, 500, "graph does not exist")
        code = semanticweb.dropRelation(graphName,str(food).capitalize(),str(eater).capitalize())
        MyRequestHandler.resp(self,code["code"])

class FoodChainHandler(MyRequestHandler):
    # list all food chains
    def get(self, graphName):
        if  not semanticweb.graphExists(graphName):
            MyRequestHandler.resp(self, 500, "graph does not exist")
        startEnd = semanticweb.listStartEnd(graphName)
        chains = []
        for pair in startEnd:
            chains = chains + semanticweb.listFoodChains(graphName,pair[0],pair[1])
        MyRequestHandler.resp(self,200,{"foodChains":chains})

class CheckHandler(MyRequestHandler):
    # check if every animal has food in this food web
    def get(self, graphName):
        if  not semanticweb.graphExists(graphName):
            MyRequestHandler.resp(self, 500, "graph does not exist")
        hungry = semanticweb.findHungryAnimals(graphName)
        MyRequestHandler.resp(self, 200, {"hungryAnimals":hungry})
