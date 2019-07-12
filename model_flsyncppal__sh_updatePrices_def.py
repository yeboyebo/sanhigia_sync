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
    def sanhigia_sync_updateProductPrice(self):
        _i = self.iface

        cdSmall = 10
        cdLarge = 180

        headers = None
        if qsatype.FLUtil.isInProd():
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic c2luY3JvOklMdHYyUE9BT0NVcg=="
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic dGVzdDp0ZXN0"
            }

        try:
            body = []
            now = str(qsatype.Date())
            currD = now[:10]
            currT = now[-(8):]

            ultimasincro = qsatype.FLUtil.readDBSettingEntry("SincroPrices")
            if ultimasincro:
                ultimasincro = ultimasincro.split("T")
            else:
                ultimasincro = [str(currD), str(currT)]
                qsatype.FLUtil.writeDBSettingEntry("SincroPrices", "T".join(ultimasincro))

            if len(ultimasincro):
                fecha = ultimasincro[0]
                hora = ultimasincro[1]
            else:
                fecha = currD
                hora = currT

            filtroFechas = "(a.fechaalta > '" + fecha + "' OR (a.fechaalta = '" + fecha + "' AND  a.horaalta >= '" + hora + "'))"
            filtroFechas += " OR (a.fechamod > '" + fecha + "' OR (a.fechamod = '" + fecha + "' AND  a.horamod >= '" + hora + "'))"
            where = filtroFechas + " ORDER BY a.referencia"

            q = qsatype.FLSqlQuery()
            q.setSelect("a.referencia,a.pvp, a.codtarifa, st.codwebsite, st.codstoreview")
            q.setFrom("mg_websites w inner join mg_storeviews st on w.codwebsite = st.codwebsite inner join articulostarifas a on a.codtarifa = w.codtarifa")
            q.setWhere(where)

            if not q.exec_():
                qsatype.debug("Error. La consulta falló.")
                qsatype.debug(q.sql())
                syncppal.iface.log("Error. La consulta falló.", "shsyncprices")
                return cdLarge

            while q.next():
                sku = q.value("a.referencia")
                price = parseFloat(q.value("a.pvp"))
                store_id = q.value("st.codstoreview")
                website = q.value("st.codwebsite")

                body.append({"sku": sku, "price": price, "sincroPrecios": True, "auto": True, "store_id": store_id, "website": website})

            if not len(body):
                syncppal.iface.log("Éxito. No hay precios que sincronizar.", "shsyncprices")
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
                    # Actualizo fecha y hora ultima sincro
                    nuevaultsincro = str(currD) + "T" + str(currT)
                    qsatype.FLUtil.writeDBSettingEntry("SincroPrices", nuevaultsincro)

                    syncppal.iface.log("Éxito. Precios sincronizados correctamente (id: " + str(jsonres["request_id"]) + ")", "shsyncprices")
                    return cdSmall
                else:
                    syncppal.iface.log("Error. No se pudo actualizar los precios.", "shsyncprices")
                    return cdSmall
            else:
                syncppal.iface.log("Error. No se pudo actualizar los precios. Código: " + str(stCode), "shsyncprices")
                return cdSmall

        except Exception as e:
            qsatype.debug(e)
            syncppal.iface.log("Error. No se pudo establecer la conexión con el servidor.", "shsyncprices")
            return cdSmall

        return cdSmall

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def updateProductPrice(self):
        return self.ctx.sanhigia_sync_updateProductPrice()


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
