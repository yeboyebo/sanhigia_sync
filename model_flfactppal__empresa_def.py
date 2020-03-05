
# @class_declaration sanhigia_sync #
from sync import tasks
from models.flsyncppal import flsyncppal_def as syncppal


class sanhigia_sync(flfactppal):

    params_sincro = syncppal.iface.get_param_sincro('apipass')

    def sanhigia_sync_getActivity(self, params):
        return tasks.getActivity()

    def sanhigia_sync_revoke(self, params):
        return tasks.revoke(params["id"])

    def sanhigia_sync_shsyncOrders(self, params):
        if "passwd" in params and params['passwd'] == self.params_sincro['auth']:
            tasks.getUnsynchronizedOrders.delay(params['fakeRequest'])
            return {"msg": "Tarea encolada correctamente"}
        else:
            print("no tengo contraseña")

        return False

    def sanhigia_sync_shsyncStock(self, params):
        if "passwd" in params and params['passwd'] == self.params_sincro['auth']:
            tasks.updateProductStock.delay(params['fakeRequest'])
            return {"msg": "Tarea encolada correctamente"}
        else:
            print("no tengo contraseña")

        return False

    def sanhigia_sync_shsyncPrices(self, params):
        if "passwd" in params and params['passwd'] == self.params_sincro['auth']:
            tasks.updateProductPrice.delay(params['fakeRequest'])
            return {"msg": "Tarea encolada correctamente"}
        else:
            print("no tengo contraseña")

        return False

    def sanhigia_sync_shsyncCust(self, params):
        if "passwd" in params and params['passwd'] == self.params_sincro['auth']:
            tasks.getUnsynchronizedCustomers.delay(params['fakeRequest'])
            return {"msg": "Tarea encolada correctamente"}
        else:
            print("no tengo contraseña")

        return False

    def sanhigia_sync_syncPvpCondCli(self, params):
        if "passwd" in params and params['passwd'] == self.params_sincro['auth']:
            tasks.updatePvpCondCli.delay(params['fakeRequest'])
            return {"msg": "Tarea encolada correctamente"}
        else:
            print("no tengo contraseña")

        return False

    def __init__(self, context=None):
        super().__init__(context)

    def getActivity(self, params):
        return self.ctx.sanhigia_sync_getActivity(params)

    def revoke(self, params):
        return self.ctx.sanhigia_sync_revoke(params)

    def shsyncOrders(self, params):
        return self.ctx.sanhigia_sync_shsyncOrders(params)

    def shsyncStock(self, params):
        return self.ctx.sanhigia_sync_shsyncStock(params)

    def shsyncPrices(self, params):
        return self.ctx.sanhigia_sync_shsyncPrices(params)

    def shsyncCust(self, params):
        return self.ctx.sanhigia_sync_shsyncCust(params)

    def syncPvpCondCli(self, params):
        return self.ctx.sanhigia_sync_syncPvpCondCli(params)

