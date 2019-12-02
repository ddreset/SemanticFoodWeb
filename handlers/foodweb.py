from handlers.myRequestHandler import MyRequestHandler
import setting

class MainHandler(MyRequestHandler):
    def get(self):
        self.write('<a href="%s">link to story 1</a>' %
                   self.reverse_url("story", "1"))

class StoryHandler(MyRequestHandler):

    def get(self, story_id):
        self.write("this is story %s" % story_id)

class FoodChainHandler(MyRequestHandler):
    def get(self, userId):
        self.write("user:"+str(userId))