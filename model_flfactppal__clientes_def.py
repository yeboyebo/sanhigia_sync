
# @class_declaration sanhigia_sync #
from YBUTILS import notifications
class sanhigia_sync(flfactppal):

    def sanhigia_sync_enviocorreo(self):
        _i = self.iface
        oDM = _i.datosConfigMail()
        print("sanhigia_sync_enviocorreo")
        try:
            nombreCorreo = ["nikolay@yeboyebo.es","pozuelo@yeboyebo.es","juanma@yeboyebo.es"]
            asunto = "Asunto prueba envio seguimiento"
            cuerpo = "Cuerpo prueba envio seguimiento"
            connection = notifications.get_connection(oDM.hostcorreosaliente, oDM.usuariosmtp, oDM.passwordsmtp, oDM.puertosmtp, oDM.tipocxsmtp)
            print("connection_____: ", connection)
            notifications.sendMail(connection, oDM.usuariosmtp, asunto, cuerpo, nombreCorreo)
            print("FIN_____: ")
        except Exception as e:
            print(e)
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


    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def datosConfigMail(self):
        return self.ctx.sanhigia_sync_datosConfigMail()

    def enviocorreo(self):
        return self.ctx.sanhigia_sync_enviocorreo()

