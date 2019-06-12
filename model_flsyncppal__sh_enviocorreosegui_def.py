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

    @periodic_task(run_every=crontab(minute="*/3", hour="*"))
    def sanhigia_sync_enviocorreo():
        q = qsatype.FLSqlQuery()
        q.setSelect("a.idalbaran,a.agenciaenvio,a.sh_numtracking,a.codigo,c.nombre,c.email")
        q.setFrom("albaranescli a INNER JOIN clientes c ON a.codcliente = c.codcliente")
        where = "a.sh_numtracking is not null AND a.sh_estadosegui = 'Pendiente' ORDER BY a.fecha LIMIT 10"
        # if where != "":
        #     where += " AND "

        q.setWhere(where)
        q.exec_()
        if not q.size():
             # syncppal.iface.log("Éxito", "No hay datos para enviar")
            return True
        oDM = qsatype.Object()
        qDM = qsatype.FLSqlQuery()
        qDM.setSelect("hostcorreosaliente, puertosmtp, tipocxsmtp, tipoautsmtp, usuariosmtp, passwordsmtp")
        qDM.setFrom(u"factppal_general")
        qDM.setWhere(u"1 = 1")
        if not qDM.exec_():
             # syncppal.iface.log("Error", "No estan informados los datos del correo saliente.")
            return False
        if qDM.first():
            oDM["hostcorreosaliente"] = qDM.value("hostcorreosaliente")
            oDM["puertosmtp"] = qDM.value("puertosmtp")
            oDM["tipocxsmtp"] = qDM.value("tipocxsmtp")
            oDM["tipoautsmtp"] = qDM.value("tipoautsmtp")
            oDM["usuariosmtp"] = qDM.value("usuariosmtp")
            oDM["passwordsmtp"] = qDM.value("passwordsmtp")
        while q.next():
            idalbaran = q.value("a.idalbaran")
            agencia = q.value("a.agenciaenvio")
            codigo = q.value("a.codigo")
            numtracking = q.value("a.sh_numtracking")
            nombre = q.value("c.nombre")
            email = q.value("c.email")
            estado = "Pendiente"
            asunto = "Prueba envio seguimiento"
            cuerpo = "El número del seguimiento del pedido {} es '{}'<br>".format(codigo, numtracking)
            if not email or email == "":
                # syncppal.iface.log("Error. El cliente {} con pedido {} no tiene email.".format(item["nombre"], item["codigo"]), "enviocorreo")
                estado = "Sin correo"
            else:
                connection = notifications.get_connection(oDM["hostcorreosaliente"], oDM["usuariosmtp"], oDM["passwordsmtp"], oDM["puertosmtp"], oDM["tipocxsmtp"])
                if agencia == "CEX":
                    cuerpo += "https://s.correosexpress.com/SeguimientoSinCP/search?n={}".format(numtracking)
                elif agencia == "MRW":
                    cuerpo += "https://www.mrw.es/seguimiento_envios/MRW_resultados_consultas.asp?modo=nacional&envio={}".format(numtracking)
                if connection is False:
                    # syncppal.iface.log("Error. Los datos de conexión han fallado", "enviocorreo")
                    estado = "Error"
                elif notifications.sendMail(connection, oDM.usuariosmtp, asunto, cuerpo, [email]) is False:
                    # syncppal.iface.log("Error. Ocurrió un error durante el proceso de enviar correos de segumiento de envio", "enviocorreo")
                    estado = "Error"
                else:
                    # syncppal.iface.log("Éxito. Se ha enviado email con número el seguimiento al cliente {}".format(item["nombre"]), "enviocorreo")
                    estado = "Enviado"
            qsatype.FLSqlQuery().execSql("UPDATE albaranescli SET sh_estadosegui = '{}' WHERE idalbaran = '{}'".format(estado, idalbaran))
        return True

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)


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
