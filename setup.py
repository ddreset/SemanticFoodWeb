import tornado.ioloop
import tornado.web
import handlers.foodweb

routes = [
        (r"/", handlers.foodweb.MainHandler),
        tornado.web.url(r"/graphs", handlers.foodweb.GraphsHandler, name="graphs"),
        tornado.web.url(r"/graph/([0-9A-Za-z]+)", handlers.foodweb.GraphHandler, name="graph"),
        tornado.web.url(r"/graph/([0-9A-Za-z]+)/food/([0-9A-Za-z_]+)/eater/([0-9A-Za-z_]+)", handlers.foodweb.RelationHandler, name="relation"),
        tornado.web.url(r"/graph/([0-9A-Za-z]+)/foodchain", handlers.foodweb.FoodChainHandler, name="foodChain"),
        tornado.web.url(r"/graph/([0-9A-Za-z]+)/check", handlers.foodweb.CheckHandler, name="check")
    ]

def make_app():
    return tornado.web.Application(routes)

if __name__ == "__main__":
    app = make_app()
    app.listen(6688)
    tornado.ioloop.IOLoop.current().start()