
# @class_declaration sanhigia_sync_empresa #
class sanhigia_sync_empresa(flfactppal_empresa, helpers.MixinConAcciones):
    pass

    class Meta:
        proxy = True

    @helpers.decoradores.csr()
    def getactivity(params):
        return form.iface.getActivity(params)

    @helpers.decoradores.csr()
    def revoke(params):
        return form.iface.revoke(params)

    @helpers.decoradores.csr()
    def shsyncorders(params):
        return form.iface.shsyncOrders(params)

    @helpers.decoradores.csr()
    def shsyncstock(params):
        return form.iface.shsyncStock(params)

    @helpers.decoradores.csr()
    def shsyncprices(params):
        return form.iface.shsyncPrices(params)

    @helpers.decoradores.csr()
    def shsynccust(params):
        return form.iface.shsyncCust(params)

    @helpers.decoradores.csr()
    def syncpvpcondcli(params):
        return form.iface.syncPvpCondCli(params)

