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

    @periodic_task(run_every=crontab(minute="*/30", hour="*"))
    def sanhigia_sync_enviocorreo():
        q = qsatype.FLSqlQuery()
        q.setSelect("a.idalbaran,a.agenciaenvio,a.sh_numtracking,a.codigo,c.nombre,c.email")
        q.setFrom("albaranescli a INNER JOIN clientes c ON a.codcliente = c.codcliente")
        where = "a.sh_numtracking is not null AND a.sh_estadosegui = 'Pendiente' ORDER BY a.fecha LIMIT 20"
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
            email = qsatype.FLUtil.quickSqlSelect("albaranescli a INNER JOIN lineasalbaranescli la ON a.idalbaran = la.idalbaran INNER JOIN pedidoscli p ON la.idpedido = p.idpedido", "p.mg_email", "a.idalbaran = {} AND p.mg_increment_id is not null".format(idalbaran))
            if not email or email == "":
                email = q.value("c.email")
            estado = "Pendiente"
            asunto = "Seguimiento del pedido {}".format(codigo)
            cuerpo = ""
            # cuerpo = "El número del seguimiento del pedido {} es '{}'<br>".format(codigo, numtracking)
            if not email or email == "":
                # syncppal.iface.log("Error. El cliente {} con pedido {} no tiene email.".format(item["nombre"], item["codigo"]), "enviocorreo")
                estado = "Sin correo"
            else:
                connection = notifications.get_connection(oDM["hostcorreosaliente"], oDM["usuariosmtp"], oDM["passwordsmtp"], oDM["puertosmtp"], oDM["tipocxsmtp"])
                urlsegui = qsatype.FLUtil.quickSqlSelect("agenciastrans", "urlsegui", "codagencia = '{}'".format(agencia))
                if urlsegui is False or urlsegui == "":
                    # syncppal.iface.log("Error. No tiene informado el campo 'URL de seguimiento en la tabla {}".format(agencia), "enviocorreo")
                    continue
                cuerpo += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Raleway:400,500,700);@media screen {.email-heading h1,.store-info h4,  th.cell-name,a.product-name,p.product-name,.address-details h6,.method-info h6,h5.closing-text,.action-button,.action-button a,.action-button span,  .action-content h1 {font-family: "Raleway", Verdana, Arial !important;font-weight: normal;}}@media screen and (max-width: 600px) {body {width: 94% !important;padding: 0 3% !important;display: block !important;}.container-table {width: 100% !important;max-width: 600px;min-width: 300px;}  td.store-info h4 {margin-top: 8px !important;margin-bottom: 0px !important;}td.store-info p {margin: 5px 0 !important;}.wrapper {width: 100% !important;  display: block;padding: 5px 0 !important;}.cell-name,.cell-content {padding: 8px !important;}}@media screen and (max-width: 450px) {.email-heading,  .store-info {float: left;width: 98% !important;display: block;text-align: center;padding: 10px 1% !important;border-right: 0px !important;}  .address-details, .method-info {width: 85%;display: block;}.store-info {border-top: 1px dashed #c3ced4;}.method-info {margin-bottom: 15px !important;}}/* Remove link color on iOS */.no-link a {color: #333333 !important;cursor: default !important;text-decoration: none !important;}.method-info h6,.address-details h6,.closing-text {color: #3696c2 !important;}td.order-details h3,td.store-info h4 {color: #333333 !important;}.method-info p,.method-info dl {margin: 5px 0 !important;font-size: 12px !important;}td.align-center {text-align: center !important;}td.align-right {text-align: right !important;}/* Newsletter styles */td.expander {padding: 0 !important;}table.button td,table.social-button td {width: 92% !important;}table.facebook:hover td {background: #2d4473 !important;}table.twitter:hover td {background: #0087bb !important;}table.google-plus:hover td {  background: #CC0000 !important;}@media screen and (max-width: 600px) {.products-grid tr td {width: 50% !important;display: block !important;float: left !important;}}.product-name a:hover {color: #3399cc !important;text-decoration: none !important;}</style><!-- Begin wrapper table --><table width="100%" cellpadding="0" cellspacing="0" border="0" id="background-table" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; padding: 0; margin: 0 auto; background-color: #ebebeb; font-size: 12px;"><tr><td valign="top" class="container-td" align="center" style="font-family: Verdana, Arial; font-weight: normal; border-collapse: collapse; vertical-align: top; padding: 0; margin: 0; width: 100%;"><table cellpadding="0" cellspacing="0" border="0" align="center" class="container-table" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; padding: 0; margin: 0 auto; width: 600px;"><tr><td style="font-family: Verdana, Arial; font-weight: normal; border-collapse: collapse; vertical-align: top; padding: 0; margin: 0;"><table cellpadding="0" cellspacing="0" border="0" class="logo-container" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; padding: 0; margin: 0; width: 100%;"><tr><td class="logo" style="font-family: Verdana, Arial; font-weight: normal; border-collapse: collapse; vertical-align: top; padding: 15px 0px 10px 5px; margin: 0;"><a href="http://store.sanhigia.com/es/%22%22/index/index/" style="color: #c52213; float: left; display: block;"><img width="165" style="-ms-interpolation-mode: bicubic; outline: none; text-decoration: none;"></a></td></tr></table></td></tr><tr><td valign="top" class="top-content" style="font-family: Verdana, Arial; font-weight: normal; border-collapse: collapse; vertical-align: top; padding: 5px; margin: 0; border: 1px solid #ebebeb; background: #FFF;"><!-- Begin Content --><div class="header"><img src="http://store.sanhigia.com/skin/frontend/accessshop/default/images/sanhigia_logo.jpg" style="max-width: 300px; margin: 0 auto; display: block; -ms-interpolation-mode: bicubic;"/></div><table cellpadding="0" cellspacing="0" border="0" style="margin-top: 30px; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; padding: 0; margin: 0; width: 100%;"><tr><td class="action-content" style="font-family: Verdana, Arial; font-weight: normal; border-collapse: collapse; vertical-align: top; padding: 10px 20px 15px; margin: 0; line-height: 18px;"><h4 style="font-family: Verdana, Arial; font-weight: normal;">'

                cuerpo2 = '<h4>ACTUALIZACIÓN DE TU PEDIDO</h4><p>Tu pedido con albarán {0} ha sido enviado.<br>El número del seguimiento del pedido es {1}.</p>Puedes comprobar el estado del envio a <br><a class="boton" href="{2}={1}">Consultar envio</a><br><br>Gracias, Sanhigia'.format(codigo, numtracking, urlsegui)
                cuerpo += cuerpo2
                cuerpo += '</h4></td></tr></table></td></tr></table></td></tr></table>'
                # cuerpo += "{}={}".format(urlsegui, numtracking)
                # if agencia == "CEX":
                #     cuerpo += "https://s.correosexpress.com/SeguimientoSinCP/search?n={}".format(numtracking)
                # elif agencia == "MRW":
                #     cuerpo += "https://www.mrw.es/seguimiento_envios/MRW_resultados_consultas.asp?modo=nacional&envio={}".format(numtracking)
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
