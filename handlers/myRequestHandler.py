import json
import tornado.web

class MyRequestHandler(tornado.web.RequestHandler):
    def resp(self, code=None, msg=None):
        """response formatting"""
        resp_dict = {}
        resp_dict['RetSucceed'] = True
        resp_dict['Succeed'] = code == 200 or not code
        if code is None:
            resp_dict['Code'] = code = 200
        else:
            resp_dict['Code'] = code
        if msg is None:
            resp_dict['Message'] = {}
        else:
            resp_dict['Message'] = msg
        json_str = json.dumps(resp_dict, ensure_ascii=False, cls=JSONEncoder)
        return self.write(json_str)