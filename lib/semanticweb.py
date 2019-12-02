from SPARQLWrapper import SPARQLWrapper, JSON
import os,sys
sys.path.append(os.path.realpath('.')) 
import settings

foodWebSparql = SPARQLWrapper(settings.FoodWebEndPoint)
foodWebGraph = SPARQLWrapper(settings.FoodWebGraph)

prefixes = """
PREFIX g: <"""+settings.FoodWebGraph+""">
PREFIX : <"""+settings.FoodWebEndPoint+""">
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbo: <http://dbpedia.org/ontology/>
"""
 
def listDefaultGraph():
    foodWebSparql.setQuery("""
        SELECT ?subject ?predicate ?object
        WHERE {
        ?subject ?predicate ?object
        }
        LIMIT 25
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    print(results)

def listGraphs():
    foodWebSparql.setQuery("""
        SELECT ?g 
        WHERE {
        GRAPH ?g { }
        }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    graphs = []
    for r in results:
        graphs.append(r["g"]["value"])
    return graphs

def listFoodRelations(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT ?food ?eater
    WHERE {
        GRAPH g:"""+graphName+"""{
            ?food :feed ?eater
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    relations = []
    for result in results:
        relations.append([result["food"]["value"],result["eater"]["value"]])
    return relations

# list entity which is from dbpedia.org/resource
# excep those from default graph
def listDBresource(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT distinct ?entity
    { 
        GRAPH g:"""+graphName+"""{
            ?entity a* [].
            filter(isuri(?entity) && strstarts(str(?entity),str(dbr:)))
        }
        minus{
            ?entity a* [].
            filter(isuri(?entity) && strstarts(str(?entity),str(dbr:)))
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    entities = []
    for result in results:
        entities.append(result["entity"]["value"])
    return entities

# list all resources that starts a food chain
# also those resources not in any food chain
def listStartResource(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT distinct ?entity
    { 
        GRAPH g:"""+graphName+"""{
            ?entity a* [].
            filter(isuri(?entity) && strstarts(str(?entity),str(dbr:)))
            FILTER NOT EXISTS { [] :feed ?entity }
        }
        minus{
            ?entity a* [].
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    entities = []
    for result in results:
        entities.append(result["entity"]["value"])
    return entities

# directly coundt food chains
# but does not list each food chain
def countFoodChains(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT (substr(str(?start),29)+"-"+substr(str(?end),29) as ?startEnd) (count(?nextEater)as ?count)
    { 
        GRAPH g:"""+graphName+"""{
            ?start :feed+ ?end.
            minus{
                ?start1 :feed ?start.
            }
            minus {
                ?end :feed ?end1.
            }
            ?start :feed* ?eater.
            ?eater :feed* ?end.
            ?eater :feed ?nextEater.
        }
    } 
    group by ?start ?end ?eater
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    chains = {}
    for result in results:
        key = result["startEnd"]["value"]
        count = int(result["count"]["value"])
        if key in chains:
            chains[key] = chains[key] * count
        else:
            chains[key] = count
    chainsNum = sum(chains.values())
    return chainsNum

def listFoodChains(graphName,start,end):
    foodWebSparql.setQuery( prefixes + """
    SELECT (substr(str(?entity),29) as ?entityName) (substr(str(?nextEntity),29) as ?nextEntityName)
    { 
        GRAPH g:user01{
            dbr:"""+start+""" :feed* ?entity.
            ?entity :feed* dbr:"""+end+""".
            ?entity :feed ?nextEntity.
        }
    } 
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    foodChains = [[start]]
    chainIndex = 0
    while chainIndex < len(foodChains):
        currentEnd = foodChains[chainIndex][-1]
        newEnd = None
        for result in results:
            entity = result["entityName"]["value"]
            nextEntity = result["nextEntityName"]["value"]
            if entity == currentEnd and newEnd == None:
                newEnd = nextEntity
            elif entity == currentEnd and newEnd != None:
                foodChains.append(foodChains[chainIndex]+[nextEntity])
        if newEnd == None:
            chainIndex = chainIndex + 1
        else:
            foodChains[chainIndex].append(newEnd)
    return foodChains

def findHungryAnimals(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT distinct *
    WHERE { 
        SERVICE :{
            GRAPH g:"""+graphName+"""{
                ?entity a* [].
                filter(isuri(?entity) && strstarts(str(?entity),str(dbr:)))
                FILTER NOT EXISTS { [] :feed ?entity }
            }
        }
        SERVICE <http://dbpedia.org/sparql/> {
            ?entity a ?type.
            filter(regex(?type,"Animal")).
        }
        minus{
            ?entity a* [].
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    hungryAnimals = []
    for result in results:
        hungryAnimals.append(result["entity"]["value"])
    return hungryAnimals

def initGraph(graphName):
    foodWebSparql.setQuery(prefixes + """
    INSERT DATA { 
        GRAPH g:"""+graphName+""" { 
            :MapOwner :userName \""""+graphName+"""\".
            dbr:Grass a :Producer.
            dbr:Seed a :Producer.
            }
    }
    """)
    foodWebSparql.setMethod("POST")
    code = foodWebSparql.query().response.code
    return {"code":code}

def dropGraph(graphName):
    foodWebSparql.setQuery("""
        Drop graph <"""+settings.FoodWebGraph+graphName+""">
    """)
    # foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("POST")
    code = foodWebSparql.query().response.code
    return {"code":code}

def insertAnimal(graphName, animalName):
    foodWebSparql.setQuery(prefixes + """
    INSERT DATA { 
        GRAPH g:"""+graphName+""" { 
            dbr:"""+animalName+""" a dbo:Animal
            }
    }
    """)
    foodWebSparql.setMethod("POST")
    code = foodWebSparql.query().response.code
    return {"code":code}

def addFoodChain(graphName, food, eater):
    foodWebSparql.setQuery(prefixes + """
    INSERT DATA { 
        GRAPH g:"""+graphName+""" { 
            dbr:"""+food+""" :feed dbr:"""+eater+"""
            }
    }
    """)
    foodWebSparql.setMethod("POST")
    code = foodWebSparql.query().response.code
    return {"code":code}

# foodType can be "Animal" or "Plant"
def countFood(graphName, animal, foodType):
    foodWebSparql.setQuery(prefixes + """
    SELECT (count(distinct ?food) as ?foodNum)
    WHERE {
        SERVICE :{
            GRAPH g:"""+graphName+"""{
                ?food :feed dbr:"""+animal+""".

            }
        }
        SERVICE <"""+settings.DBpediaEndPoint+"""> {
            ?food a ?foodType.
            filter(regex(?foodType,\""""+foodType+"""\")).
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    return int(results["results"]["bindings"][0]["foodNum"]["value"])

# an animal can be Herbivore, Omnivore or Carnivore
def getAnimalIdentity(graphName,animal):
    plantNum = countFood(graphName,animal,"Plant")
    animalNum = countFood(graphName,animal,"Animal")
    if plantNum > 0 and animalNum > 0:
        return "Omnivore"
    elif plantNum > 0:
        return "Herbivore"
    elif animalNum > 0:
        return "Carnivore"
    else:
        return None

if __name__ == '__main__':
    # results = initGraph("user01")
    # results = dropGraph("user01")
    # results = insertAnimal("user01","Dog")
    
    # results = listGraphs()
    
    # results = addFoodChain("user01","Wolf","Tiger")
    
    # results = listFoodChains("user01")
    
    # results = countFood("user01","Tiger","Animal")
    # results = getAnimalIdentity("user01","Cat")
    
    # results = countFoodChains("user01")
    
    results = listFoodChains("user01","Cherry","Tiger")
    
    # results = findHungryAnimals("user01")
    
    # results = listStartResource("user01")
    print(results)