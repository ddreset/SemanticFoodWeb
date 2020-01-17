from SPARQLWrapper import SPARQLWrapper, JSON
import os,sys
sys.path.append(os.path.realpath('.')) 
import settings

foodWebSparql = SPARQLWrapper(settings.FoodWebEndPoint)
foodWebGraph = SPARQLWrapper(settings.FoodWebGraph)

prefixes = """
PREFIX g: <"""+settings.FoodWebGraph+""">
PREFIX : <"""+settings.FoodWebEndPoint+""">
PREFIX fw: <http://users.jyu.fi/~zhangy/FoodWeb.owl#>
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

def graphExists(graphName):
    foodWebSparql.setQuery(prefixes + """
        ASK WHERE
        { 
            GRAPH g:"""+graphName+"""{?s ?p ?o}
        } 
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()["boolean"]
    return results

def listFoodRelations(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT ?food ?eater
    WHERE {
        GRAPH g:"""+graphName+"""{
            ?food fw:feed ?eater
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
            FILTER NOT EXISTS { [] fw:feed ?entity }
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

def listStartEnd(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT (substr(str(?start),29) as ?startName) (substr(str(?end),29) as ?endName)
    { 
        GRAPH g:"""+graphName+"""{
            ?start fw:feed+ ?end.
            minus{
                ?start1 fw:feed ?start.
            }
            minus{
                ?end fw:feed ?end1
            }
        }
    }
    """)
    foodWebSparql.setReturnFormat(JSON)
    foodWebSparql.setMethod("GET")
    results = foodWebSparql.query().convert()
    results = results["results"]["bindings"]
    startEnd = []
    for result in results:
        startEnd.append([result["startName"]["value"],result["endName"]["value"]])
    return startEnd

# directly coundt food chains
# but does not list each food chain
def countFoodChains(graphName):
    foodWebSparql.setQuery( prefixes + """
    SELECT (substr(str(?start),29)+"-"+substr(str(?end),29) as ?startEnd) (count(?nextEater)as ?count)
    { 
        GRAPH g:"""+graphName+"""{
            ?start fw:feed+ ?end.
            minus{
                ?start1 fw:feed ?start.
            }
            minus {
                ?end fw:feed ?end1.
            }
            ?start fw:feed* ?eater.
            ?eater fw:feed* ?end.
            ?eater fw:feed ?nextEater.
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
        GRAPH g:"""+graphName+"""{
            dbr:"""+start+""" fw:feed* ?entity.
            ?entity fw:feed* dbr:"""+end+""".
            ?entity fw:feed ?nextEntity.
            ?nextEntity fw:feed* dbr:"""+end+""".
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
    SELECT distinct (substr(str(?entity),29) as ?entityName)
    WHERE { 
        SERVICE :{
            GRAPH g:"""+graphName+"""{
                ?entity a* [].
                filter(isuri(?entity) && strstarts(str(?entity),str(dbr:)))
                FILTER NOT EXISTS { [] fw:feed ?entity }
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
        hungryAnimals.append(result["entityName"]["value"])
    return hungryAnimals

def initGraph(graphName):
    foodWebSparql.setQuery(prefixes + """
    INSERT DATA { 
        GRAPH g:"""+graphName+""" { 
            :"""+graphName+""" a :FoodWeb.
            :"""+graphName+""" :hasContributor "user01".
            dbr:Grass a fw:Producer.
            dbr:Seed a fw:Producer.
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

def addRelation(graphName, food, eater):
    foodWebSparql.setQuery(prefixes + """
    INSERT DATA { 
        GRAPH g:"""+graphName+""" { 
            dbr:"""+food+""" fw:feed dbr:"""+eater+"""
            }
    }
    """)
    foodWebSparql.setMethod("POST")
    code = foodWebSparql.query().response.code
    return {"code":code}

def dropRelation(graphName, food, eater):
    foodWebSparql.setQuery(prefixes + """
    DELETE DATA { 
        GRAPH g:"""+graphName+""" { 
            dbr:"""+food+""" fw:feed dbr:"""+eater+"""
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
                ?food fw:feed dbr:"""+animal+""".

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
    
    # results = listFoodChains("user01","Cherry","Tiger")
    
    # results = findHungryAnimals("user01")
    
    # results = listStartResource("user01")

    results = graphExists("user01")
    print(results)