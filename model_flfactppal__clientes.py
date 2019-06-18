
# @class_declaration sanhigia_sync_clientes #
class sanhigia_sync_clientes(flfactppal_clientes, helpers.MixinConAcciones):
    pass

    class Meta:
        proxy = True

    @helpers.decoradores.accion()
    def enviocorreo(self):
        return form.iface.enviocorreo()

