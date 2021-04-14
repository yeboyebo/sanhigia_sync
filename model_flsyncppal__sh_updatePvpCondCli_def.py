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
    def sanhigia_sync_updatePvpCondCli(self):

        cdSmall = 10
        cdLarge = 120

        params_b2c = syncppal.iface.get_param_sincro('b2c')
        params_pvpcondcli = syncppal.iface.get_param_sincro('b2cPvpCondCliUpload')

        headers = None
        if qsatype.FLUtil.isInProd():
            headers = {
                "Content-Type": "application/json",
                "Authorization": params_b2c['auth']
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": params_b2c['test_auth']
            }

        try:
            body = []

            q = qsatype.FLSqlQuery()
            q.setSelect("idssw, datossincro")
            q.setFrom("mg_colasincroweb")
            q.setWhere("tipo = 'syncpvpcondcli'  AND sincronizado = false ORDER BY idssw ASC LIMIT 20")

            if not q.exec_():
                qsatype.debug("Error. La consulta falló.")
                qsatype.debug(q.sql())
                syncppal.iface.log("Error. La consulta falló.", "syncpvpcondcli")
                return cdLarge

            ids_enviados = []
            emails_enviados = []
            datossincro = {}
            emailant = None
            while q.next():
                if q.isNull('datossincro'):
                    continue
                datossincro = json.loads(q.value('datossincro'))
                if emailant != datossincro["email"]:
                    emails_enviados.append(datossincro["email"])
                    emailant = datossincro["email"]
                ids_enviados.append(str(q.value('idssw')))
                body.append(datossincro)

            if not len(body):
                syncppal.iface.log("Exito. No hay precios artículo cliente que sincronizar.", "syncpvpcondcli")
                return cdLarge

            url = params_pvpcondcli['url'] if qsatype.FLUtil.isInProd() else params_pvpcondcli['test_url']

            qsatype.debug(ustr("Llamando a ", url, " ", json.dumps(body)))
            response = requests.post(url, data=json.dumps(body), headers=headers)
            stCode = response.status_code
            if response and stCode == int(params_pvpcondcli['success_code']):
                if str(stCode) == '200' and response.text == 'ok':
                    ids_enviados = ','.join(ids_enviados)
                    emails_enviados = ','.join(emails_enviados)
                    qsatype.FLSqlQuery().execSql("UPDATE mg_colasincroweb SET sincronizado = true WHERE idssw in (" + ids_enviados + ")")
                    syncppal.iface.log("Exito. Los precios del los clientes ({}) sincronizados correctamente".format(emails_enviados), "syncpvpcondcli")
                    return cdSmall
                else:
                    syncppal.iface.log("Error. No se pudo actualizar los precios del los clientes ({}).".format(emails_enviados), "syncpvpcondcli")
                    return cdSmall
            else:
                syncppal.iface.log("Error. No se pudo actualizar el Precio artículo cliente. Código: {}".format(stCode), "syncpvpcondcli")
                return cdSmall

        except Exception as e:
            qsatype.debug(e)
            syncppal.iface.log("Error. No se pudo establecer la conexión con el servidor.", "syncpvpcondcli")
            return cdSmall

        return cdSmall

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def updatePvpCondCli(self):
        return self.ctx.sanhigia_sync_updatePvpCondCli()

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
