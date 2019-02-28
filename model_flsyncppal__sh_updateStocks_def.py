# @class_declaration interna #
import requests
import json
from django.db import transaction
from YBLEGACY import qsatype
from YBLEGACY.constantes import *
from models.flsyncppal import flsyncppal_def as syncppal


class interna(qsatype.objetoBase):

    ctx = qsatype.Object()

    def __init__(self, context=None):
        self.ctx = context


# @class_declaration sanhigia_sync #
class sanhigia_sync(interna):

    @transaction.atomic
    def sanhigia_sync_updateProductStock(self):
        _i = self.iface

        cdSmall = 10
        cdLarge = 180

        headers = None
        if qsatype.FLUtil.isInProd():
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic dGVzdDp0ZXN0"
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic dGVzdDp0ZXN0"
            }

        try:
            body = []
            codTienda = "ALM"
            now = str(qsatype.Date())
            currD = now[:10]
            currT = now[-(8):]

            ultimasincro = qsatype.FLUtil.readDBSettingEntry("SincroStock")
            # ultimasincro = str(currD) + "T" + str(currT)
            if ultimasincro:
                ultimasincro = ultimasincro.split("T")
            else:
                ultimasincro = [str(currD), str(currT)]
                qsatype.FLUtil.writeDBSettingEntry("SincroStock", "T".join(ultimasincro))

            if len(ultimasincro):
                fecha = ultimasincro[0]
                hora = ultimasincro[1]
            else:
                fecha = currD
                hora = currT

            filtroFechas = "(s.fechaalta > '" + fecha + "' OR (s.fechaalta = '" + fecha + "' AND  s.horaalta >= '" + hora + "'))"
            filtroFechas += " OR (s.fechamod > '" + fecha + "' OR (s.fechamod = '" + fecha + "' AND  s.horamod >= '" + hora + "'))"
            where = filtroFechas + " ORDER BY a.referencia"

            q = qsatype.FLSqlQuery()
            q.setSelect("a.referencia, s.disponible")
            q.setFrom("articulos a INNER JOIN stocks s ON (a.referencia = s.referencia AND s.codalmacen = '" + codTienda + "')")
            q.setWhere(where)

            if not q.exec_():
                qsatype.debug("Error. La consulta falló.")
                qsatype.debug(q.sql())
                syncppal.iface.log("Error. La consulta falló.", "shsyncstock")
                return cdLarge

            while q.next():

                sku = q.value("a.referencia")
                qty = parseInt(_i.dameStock(q.value("s.disponible")))

                body.append({"sku": sku, "qty": qty, "sincroStock": True})

            if not len(body):
                nuevaultsincro = str(currD) + "T" + str(currT)
                qsatype.FLUtil.writeDBSettingEntry("SincroStock", nuevaultsincro)
                syncppal.iface.log("Éxito. No hay stocks que sincronizar.", "shsyncstock")
                return cdLarge

            url = None
            if qsatype.FLUtil.isInProd():
                url = 'http://store.sanhigia.com/syncapi/index.php/productupdates'
            else:
                url = 'http://local.sanhigia.com/syncapi/index.php/productupdates'

            qsatype.debug(ustr("Llamando a ", url, " ", json.dumps(body)))
            response = requests.post(url, data=json.dumps(body), headers=headers)
            stCode = response.status_code
            jsonres = None
            if response and stCode == 202:
                jsonres = response.json()

                if jsonres and "request_id" in jsonres:
                    nuevaultsincro = str(currD) + "T" + str(currT)
                    qsatype.FLUtil.writeDBSettingEntry("SincroStock", nuevaultsincro)
                    syncppal.iface.log("Éxito. Stock sincronizado correctamente (id: " + str(jsonres["request_id"]) + ")", "shsyncstock")
                    return cdSmall
                else:
                    syncppal.iface.log("Error. No se pudo actualizar el stock.", "shsyncstock")
                    return cdSmall
            else:
                syncppal.iface.log("Error. No se pudo actualizar el stock. Código: " + str(stCode), "shsyncstock")
                return cdSmall

        except Exception as e:
            qsatype.debug(e)
            syncppal.iface.log("Error. No se pudo establecer la conexión con el servidor.", "shsyncstock")
            return cdSmall

        return cdSmall

    def sanhigia_sync_dameSkuStock(self, referencia, talla):
        print("******referencia")
        print(referencia)
        print(talla)
        if talla == "TU":
            talla = ""
        else:
            talla = "-" + talla

        return referencia + talla

    def sanhigia_sync_dameStock(self, disponible):
        if not disponible or isNaN(disponible) or disponible < 0:
            return 0
        return disponible

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def updateProductStock(self):
        return self.ctx.sanhigia_sync_updateProductStock()

    def dameSkuStock(self, referencia, talla):
        return self.ctx.sanhigia_sync_dameSkuStock(referencia, talla)

    def dameStock(self, disponible):
        return self.ctx.sanhigia_sync_dameStock(disponible)


# @class_declaration head #
class head(sanhigia_sync):

    def __init__(self, context=None):
        super(head, self).__init__(context)


# @class_declaration ifaceCtx #
class ifaceCtx(head):

    def __init__(self, context=None):
        super(ifaceCtx, self).__init__(context)


# @class_declaration FormInternalObj #
class FormInternalObj(qsatype.FormDBWidget):
    def _class_init(self):
        self.iface = ifaceCtx(self)


form = FormInternalObj()
form._class_init()
form.iface.ctx = form.iface
form.iface.iface = form.iface
iface = form.iface
