from flask_restful import Api, request





class CoreApi(Api):
    def handle_error(self, e):
        code = getattr(e, 'code', 500)
        return super(CoreApi, self).handle_error(e)

    def make_exception_response(self,e):
        return {}


