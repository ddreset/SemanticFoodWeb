import tornado.ioloop
import tornado.web
import handlers.foodweb

routes = [
        (r"/", handlers.foodweb.MainHandler),
        tornado.web.url(r"/story/([0-9]+)", handlers.foodweb.StoryHandler, name="story"),
        (r"/foodchain/([0-9]+)", handlers.foodweb.FoodChainHandler)
    ]

def make_app():
    return tornado.web.Application(routes)

if __name__ == "__main__":
    app = make_app()
    app.listen(6688)
    tornado.ioloop.IOLoop.current().start()