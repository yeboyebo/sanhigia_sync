
# @class_declaration sanhigia_sync #
class sanhigia_sync(flsyncppal):

    def sanhigia_sync_get_customer(self):
        return "sanhigia"

    def __init__(self, context=None):
        super().__init__(context)

    def get_customer(self):
        return self.ctx.sanhigia_sync_get_customer()

