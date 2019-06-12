# @class_declaration interna #
# import datetime

from celery.task import periodic_task
from celery.schedules import crontab
from YBUTILS import notifications

from YBLEGACY import qsatype
from YBLEGACY.constantes import *

from models.flsyncppal import flsyncppal_def as syncppal


class interna(qsatype.objetoBase):

    ctx = qsatype.Object()

    def __init__(self, context=None):
        self.ctx = context


# @class_declaration sanhigia_sync #
class sanhigia_sync(interna):

    @periodic_task(run_every=crontab(minute="*/1", hour="*"))
    def sanhigia_sync_enviocorreo():
        oDM = _i.datosConfigMail()
        data = self.get_data()
        if data == []:
            # syncppal.iface.log("Éxito", "No hay datos para enviar")
            return True
        for item in data:
            try:
                if "email" not in item or item["email"] == "":
                    # syncppal.iface.log("Error. El cliente {} con pedido {} no tiene email.".format(item["nombre"], item["codigo"]), "enviocorreo")
                    qsatype.FLSqlQuery().execSql("UPDATE albaranescli SET sh_estadosegui = 'Sin correo' WHERE idalbaran = '{}'".format(item["idalbaran"]))
                    continue
                nombreCorreo = item["email"]
                asunto = "Prueba envio seguimineto"
                cuerpo = "El número del seguimiento del pedido {} es '{}'".format(item["codigo"], item["numtracking"])
                connection = notifications.get_connection(oDM.hostcorreosaliente, oDM.usuariosmtp, oDM.passwordsmtp, oDM.puertosmtp, oDM.tipocxsmtp)
                notifications.sendMail(connection, oDM.usuariosmtp, asunto, cuerpo, [nombreCorreo], fichero)
            except Exception as e:
                print(e)
                qsatype.debug(e)
                # syncppal.iface.log("Error. Ocurrió un error durante el proceso de enviar correos de segumiento de envio", "enviocorreo")
                qsatype.FLSqlQuery().execSql("UPDATE albaranescli SET sh_estadosegui = 'Error' WHERE idalbaran = '{}'".format(item["idalbaran"]))
            # syncppal.iface.log("Éxito. Se ha enviado email con número el seguimiento al cliente {}".format(item["nombre"]), "enviocorreo")
            qsatype.FLSqlQuery().execSql("UPDATE albaranescli SET sh_estadosegui = 'Enviado' WHERE idalbaran = '{}'".format(item["idalbaran"]))
        return True

    def sanhigia_sync_datosConfigMail(self):
        oDM = qsatype.Object()
        q = qsatype.FLSqlQuery()
        q.setSelect("hostcorreosaliente, puertosmtp, tipocxsmtp, tipoautsmtp, usuariosmtp, passwordsmtp")
        q.setFrom(u"factppal_general")
        q.setWhere(u"1 = 1")
        if not q.exec_():
            return False
        if q.first():
            oDM.hostcorreosaliente = q.value("hostcorreosaliente")
            print("hostcorreosaliente", oDM.hostcorreosaliente)
            oDM.puertosmtp = q.value("puertosmtp")
            print("puertosmtp", oDM.puertosmtp)
            oDM.tipocxsmtp = q.value("tipocxsmtp")
            print("tipocxsmtp", oDM.tipocxsmtp)
            oDM.tipoautsmtp = q.value("tipoautsmtp")
            print("tipoautsmtp", oDM.tipoautsmtp)
            oDM.usuariosmtp = q.value("usuariosmtp")
            print("usuariosmtp", oDM.usuariosmtp)
            oDM.passwordsmtp = q.value("passwordsmtp")
            print("passwordsmtp", oDM.passwordsmtp)
        return oDM

    def sanhigia_sync_get_data(self):
        q = qsatype.FLSqlQuery()
        q.setSelect("a.idalbaran,a.sh_numtracking,a.codigo,c.nombre,c.email")
        q.setFrom("albaranescli a INNER JOIN clientes c ON a.codcliente = c.codcliente")
        where = "a.numtracking is not null AND a.estadosegui = 'Pendiente'"
        # if where != "":
        #     where += " AND "

        q.setWhere(where)
        q.exec_()
        body = []
        if not q.size():
            return body

        while q.next():
            idalbaran = q.value("a.idalbaran")
            codigo = q.value("a.codigo")
            numtracking = q.value("a.sh_numtracking")
            nombre = q.value("c.nombre")
            email = q.value("c.email")
            body.append({"idalbaran": idalbaran, "codigo": codigo, "numtracking": numtracking, "nombre": nombre, "email": email})
        return body

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def datosConfigMail(self):
        return self.ctx.sanhigia_sync_datosConfigMail()

    def get_data(self):
        return self.ctx.sanhigia_sync_get_data()


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
