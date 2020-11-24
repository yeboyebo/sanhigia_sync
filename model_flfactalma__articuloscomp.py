# @class_declaration interna_articuloscomp #
import importlib

from YBUTILS.viewREST import helpers

from models.flfactalma import models as modelos


class interna_articuloscomp(modelos.mtd_articuloscomp, helpers.MixinConAcciones):
    pass

    class Meta:
        proxy = True


# @class_declaration sanhigia_sync_articuloscomp #
class sanhigia_sync_articuloscomp(interna_articuloscomp, helpers.MixinConAcciones):
    pass

    class Meta:
        proxy = True


# @class_declaration articuloscomp #
class articuloscomp(sanhigia_sync_articuloscomp, helpers.MixinConAcciones):
    pass

    class Meta:
        proxy = True

    def getIface(self=None):
        return form.iface


definitions = importlib.import_module("models.flfactalma.articuloscomp_def")
form = definitions.FormInternalObj()
form._class_init()
form.iface.ctx = form.iface
form.iface.iface = form.iface
