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
    def sanhigia_sync_getUnsynchronizedOrders(self):
        _i = self.iface

        cdSmall = 10
        cdLarge = 180

        params_b2c = syncppal.iface.get_param_sincro('b2c')
        params_orders = syncppal.iface.get_param_sincro('b2cOrdersDownload')
        params_orders_sync = syncppal.iface.get_param_sincro('b2cOrdersDownloadSync')

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
            url = params_orders['url'] if qsatype.FLUtil.isInProd() else params_orders['test_url']

            response = requests.get(url, headers=headers)
            stCode = response.status_code
            json = None
            if response and stCode == 200:
                json = response.json()
            else:
                raise Exception("Mala respuesta")

        except Exception as e:
            print(e)
            syncppal.iface.log("Error. No se pudo establecer la conexión con el servidor.", "shsyncorders")
            return cdLarge

        if json and len(json):
            try:
                aOrders = _i.processOrders(json)

                if not aOrders and not isinstance(aOrders, (list, tuple, dict)):
                    syncppal.iface.log("Error. Ocurrió un error al sincronizar los pedidos.", "shsyncorders")
                    raise Exception
            except Exception as e:
                print(e)
                return cdSmall

            if aOrders and len(aOrders.keys()):
                strCods = ""
                for k in aOrders.keys():
                    strCods += k if strCods == "" else ", " + k
                syncppal.iface.log(ustr("Éxito. Los siguientes pedidos se han sincronizado correctamente: ", str(strCods)), "shsyncorders")
                for order in aOrders.keys():
                    try:
                        url = params_orders_sync['url'] if qsatype.FLUtil.isInProd() else params_orders_sync['test_url']
                        url = url.format(aOrders[order])

                        print("Llamando a", url)
                        response = requests.put(url, headers=headers)
                        print("Correcto")
                    except Exception:
                        syncppal.iface.log(ustr("Error. El pedido ", str(order), " no ha podido marcarse como sincronizado."), "shsyncorders")
            elif aOrders == {}:
                syncppal.iface.log("Éxito. No hay pedidos que sincronizar.", "shsyncorders")
                return cdLarge
        else:
            syncppal.iface.log("Éxito. No hay pedidos que sincronizar.", "shsyncorders")
            return cdLarge

        return cdSmall

    def sanhigia_sync_processOrders(self, orders):
        _i = self.iface

        aOrders = {}
        saltar = {}
        iva = 0

        for order in orders:
            if order["entity_id"] in saltar:
                continue

            codigo = qsatype.FactoriaModulos.get("flfacturac").iface.cerosIzquierda(str(order["increment_id"]), 9)

            if qsatype.FLUtil.sqlSelect("pedidoscli", "idpedido", "mg_increment_id = '" + str(codigo) + "'"):
                saltar[order["entity_id"]] = order["entity_id"]
                aOrders[str(codigo)] = order["entity_id"]
                continue

            iva = 0

            curPedido = _i.creaCabeceraPedido(order, codigo)
            if not curPedido:
                return False
            # Asigno los identificadores que se han creado en el commit de pedido
            idpedido = str(curPedido.valueBuffer("idpedido"))
            codigo = str(curPedido.valueBuffer("codigo"))
            # Añado lineas de pedido
            for linea in order["items"]:

                if not _i.creaLineaPedido(linea, curPedido, order["increment_id"]):
                    return False

                iva = linea["iva"]

            # if not _i.creaLineaGastosComanda(curPedido, order["shipping_price"]):
            #     return False

            if not _i.creaLineaDescuento(curPedido, order["discount_amount"], order["coupon"]):
                return False
            neto = round(parseFloat(order["grand_total"] / ((100 + iva) / 100)), 2)
            iva = order["grand_total"] - neto
            if not qsatype.FLSqlQuery().execSql(u"UPDATE pedidoscli SET total = " + str(order["grand_total"]) + ", neto = " + str(neto) + ", totaliva = " + str(iva) + " WHERE idpedido = '" + str(idpedido) + "'"):
                syncppal.iface.log(ustr("Error. No se pudieron actualizar los totales para ", str(idpedido)), "shsyncorders")
                return False

            # iva = 0

            # if not _i.cerrarVentaWeb(curPedido):
            #     syncppal.iface.log(ustr("Error. No se pudo cerrar la venta ", str(codigo)), "shsyncorders")
            #     return False

            aOrders[idpedido] = order["entity_id"]

        return aOrders

    def sanhigia_sync_creaCabeceraPedido(self, order, codigo):
        _i = self.iface

        try:
            curPedido = qsatype.FLSqlCursor("pedidoscli")
            # curPedido.setActivatedCommitActions(False)
            curPedido.setModeAccess(curPedido.Insert)
            curPedido.refreshBuffer()
            curPedido.setValueBuffer("codigo", codigo[:15])

            cif = order["cif"][:20] if order["cif"] and order["cif"] != "" else ""
            if not cif or cif == "":
                cif = "-"
            nombrecliente = str(order["shipping_address"]["firstname"]) + " " + str(order["shipping_address"]["lastname"])

            #street = order["shipping_address"]["street"].split(" ")
            dirtipovia = ""
            direccion = order["shipping_address"]["street"]
            dirnum = ""
            dirotros = ""

            codpostal = str(order["shipping_address"]["postcode"])
            city = order["shipping_address"]["city"]
            region = order["shipping_address"]["region"]
            codpais = _i.damePaisMg(order["shipping_address"]["country_id"])
            telefonofac = order["shipping_address"]["telephone"]
            codpago = _i.obtenerCodPago(order["payment_method"])
            email = order["email"]
            
            idprovincia = None
            if order["shipping_address"]["region_id"] is not None:
                provincias = qsatype.FLSqlQuery().execSql(u"select idprovincia from provincias where mg_idprovincia='"+str(order["shipping_address"]["region_id"])+"'")
                if len(provincias) > 0:
                    idprovincia = str(provincias[0][0])

            curPedido.setValueBuffer("codserie", "W")
            curPedido.setValueBuffer("codejercicio", _i.obtenerEjercicio(order["created_at"]))
            curPedido.setValueBuffer("codalmacen", "ALM")
            curPedido.setValueBuffer("fecha", order["created_at"][:10])
            curPedido.setValueBuffer("fechasalida", order["created_at"][:10])
            curPedido.setValueBuffer("hora", _i.obtenerHora(order["created_at"]))
            curPedido.setValueBuffer("nombrecliente", nombrecliente[:100] if nombrecliente else nombrecliente)
            curPedido.setValueBuffer("codcliente", _i.obtenerCodCliente(cif))
            curPedido.setValueBuffer("cifnif", cif)
            curPedido.setValueBuffer("dirtipovia", dirtipovia[:100] if dirtipovia else dirtipovia)
            curPedido.setValueBuffer("direccion", direccion[:100] if direccion else direccion)
            curPedido.setValueBuffer("dirnum", dirnum[:100] if dirnum else dirnum)
            curPedido.setValueBuffer("dirotros", dirotros[:100] if dirotros else dirotros)
            curPedido.setValueBuffer("codpostal", codpostal[:10] if codpostal else codpostal)
            curPedido.setValueBuffer("ciudad", city[:100] if city else city)
            curPedido.setValueBuffer("provincia", region[:100] if region else region)
            curPedido.setValueBuffer("idprovincia", idprovincia)
            curPedido.setValueBuffer("telefono1", telefonofac[:30] if telefonofac else telefonofac)
            curPedido.setValueBuffer("codpais", codpais[:20] if codpais else codpais)
            curPedido.setValueBuffer("codpago", codpago[:10] if codpago else codpago)
            curPedido.setValueBuffer("coddivisa", "EUR")
            curPedido.setValueBuffer("tasaconv", 1)
            curPedido.setValueBuffer("email", email[:100] if email else email)
            curPedido.setValueBuffer("total", order["grand_total"])
            curPedido.setValueBuffer("totaleuros", order["grand_total"])
            curPedido.setValueBuffer("neto", order["subtotal"])
            curPedido.setValueBuffer("totaliva", order["tax_amount"])
            curPedido.setValueBuffer("mg_increment_id", str(order["increment_id"]))
            curPedido.setValueBuffer("regimeniva", _i.obtenerRegimenIva(order))
            curPedido.setValueBuffer("codagente", "NO")
            #Gastos de envio
            if int(order["shipping_price"]) > 0:
                curPedido.setValueBuffer("totalportes", order["shipping_price"])
                curPedido.setValueBuffer("netoportes", order["shipping_price"]/1.21)
                curPedido.setValueBuffer("ivaportes", 21)
                curPedido.setValueBuffer("codimpuestoportes", 'IVA21')
                curPedido.setValueBuffer("totalivaportes", order["shipping_price"]-(order["shipping_price"]/1.21))
            #Si es una domiciliacion, pongo el numero de cuenta en las observaciones
            if(order["bank_account"] != None and order["payment_method"] == 'direct_debit'):
                curPedido.setValueBuffer("observaciones", order["bank_account"])
            if(order["payment_method"] == 'banktransfer' or order["payment_method"] == 'direct_debit'):
                curPedido.setValueBuffer("sh_estadopago", "Pte. Validacion pago")
                curPedido.setValueBuffer("pda", "Suspendido")

            if not _i.creaLineaEnvio(order, curPedido):
                return False

            if not curPedido.commitBuffer():
                syncppal.iface.log(ustr("Error. No se pudo guardar la cabecera de la venta ", str(codigo)), "shsyncorders")
                return False
            codigo = curPedido.valueBuffer("codigo")
            curPedido.select("codigo = '" + str(codigo) + "'")
            if not curPedido.first():
                syncppal.iface.log(ustr("Error. No se pudo recuperar la cabecera guardada para ", str(codigo)), "shsyncorders")
                return False

            curPedido.setModeAccess(curPedido.Edit)
            curPedido.refreshBuffer()

            return curPedido

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_creaLineaEnvio(self, order, curPedi):
        _i = self.iface

        try:

            tracking = order["tracking_number"] if order["tracking_number"] and order["tracking_number"] != "" else ""
            street = order["shipping_address"]["street"].split(" ")
            dirtipoviaenv = street[0] if len(street) >= 1 else ""
            direccionenv = str(street[1]) + " " + str(street[2]) if len(street) >= 3 else ""
            dirnumenv = street[3] if len(street) >= 4 else ""
            dirotrosenv = street[4] if len(street) >= 5 else ""

            numcliente = order["customer_id"]
            email = order["email"]
            metodopago = order["payment_method"]
            metodoenvio = order["shipping_description"]
            nombreenv = order["shipping_address"]["firstname"]
            apellidosenv = order["shipping_address"]["lastname"]
            codpostalenv = str(order["shipping_address"]["postcode"])
            ciudad = order["shipping_address"]["city"]
            region = order["shipping_address"]["region"]
            pais = _i.damePaisMg(order["shipping_address"]["country_id"])
            telefonoenv = order["shipping_address"]["telephone"]

            curPedi.setValueBuffer("mg_numcliente", numcliente[:15] if numcliente else numcliente)
            curPedi.setValueBuffer("mg_email", email[:200] if email else email)
            curPedi.setValueBuffer("mg_metodopago", metodopago[:30] if metodopago else metodopago)
            curPedi.setValueBuffer("mg_confac", _i.conFac(False))
            curPedi.setValueBuffer("mg_metodoenvio", metodoenvio[:50] if metodoenvio else metodoenvio)
            curPedi.setValueBuffer("mg_unidadesenv", order["units"])
            curPedi.setValueBuffer("mg_numseguimiento", tracking[:50] if tracking else tracking)
            curPedi.setValueBuffer("mg_nombreenv", nombreenv[:100] if nombreenv else nombreenv)
            curPedi.setValueBuffer("mg_apellidosenv", apellidosenv[:200] if apellidosenv else apellidosenv)
            curPedi.setValueBuffer("mg_dirtipoviaenv", dirtipoviaenv[:100] if dirtipoviaenv else dirtipoviaenv)
            curPedi.setValueBuffer("mg_direccionenv", direccionenv[:200] if direccionenv else direccionenv)
            curPedi.setValueBuffer("mg_dirnumenv", dirnumenv[:100] if dirnumenv else dirnumenv)
            curPedi.setValueBuffer("mg_dirotrosenv", dirotrosenv[:100] if dirotrosenv else dirotrosenv)
            curPedi.setValueBuffer("mg_codpostalenv", codpostalenv[:10] if codpostalenv else codpostalenv)
            curPedi.setValueBuffer("mg_ciudadenv", ciudad[:100] if ciudad else ciudad)
            curPedi.setValueBuffer("mg_provinciaenv", region[:100] if region else region)
            curPedi.setValueBuffer("mg_paisenv", pais[:100] if pais else pais)
            curPedi.setValueBuffer("mg_telefonoenv", telefonoenv[:30] if telefonoenv else telefonoenv)
            curPedi.setValueBuffer("mg_gastosenv", order["shipping_price"])
            # Facturacion
            street = order["billing_address"]["street"].split(" ")
            dirtipoviafac = str(street[0]) if len(street) >= 1 else ""
            direccionfac = str(street[1]) + " " + str(street[2]) if len(street) >= 3 else ""
            dirnumfac = street[3] if len(street) >= 4 else ""
            dirotrosfac = street[4] if len(street) >= 5 else ""
            nombrefac = order["billing_address"]["firstname"]
            apellidosfac = order["billing_address"]["lastname"]
            codpostalfac = str(order["billing_address"]["postcode"])
            ciudad = order["billing_address"]["city"]
            region = order["billing_address"]["region"]
            pais = _i.damePaisMg(order["billing_address"]["country_id"])
            telefonofac = order["billing_address"]["telephone"]
            curPedi.setValueBuffer("mg_nombrefac", nombrefac[:100] if nombrefac else nombrefac)
            curPedi.setValueBuffer("mg_apellidosfac", apellidosfac[:200] if apellidosfac else apellidosfac)
            curPedi.setValueBuffer("mg_dirtipoviafac", dirtipoviafac[:100] if dirtipoviafac else dirtipoviafac)
            curPedi.setValueBuffer("mg_direccionfac", direccionfac[:200] if direccionfac else direccionfac)
            curPedi.setValueBuffer("mg_dirnumfac", dirnumfac[:100] if dirnumfac else dirnumfac)
            curPedi.setValueBuffer("mg_dirotrosfac", dirotrosfac[:100] if dirotrosfac else dirotrosfac)
            curPedi.setValueBuffer("mg_codpostalfac", codpostalfac[:10] if codpostalfac else codpostalfac)
            curPedi.setValueBuffer("mg_ciudadfac", ciudad[:100] if ciudad else ciudad)
            curPedi.setValueBuffer("mg_provinciafac", region[:100] if region else region)
            curPedi.setValueBuffer("mg_paisfac", pais[:100] if pais else pais)
            curPedi.setValueBuffer("mg_telefonofac", telefonofac[:30] if telefonofac else telefonofac)
            curPedi.setValueBuffer("mg_gastosfac", order["shipping_price"])

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_creaLineaPedido(self, linea, curPedido, increment):
        _i = self.iface

        try:
            curLinea = qsatype.FLSqlCursor("lineaspedidoscli")
            curLinea.setModeAccess(curLinea.Insert)
            curLinea.refreshBuffer()

            idpedido = curPedido.valueBuffer("idpedido")
            nl = _i.obtenerNumLineaComanda(idpedido)
            iva = linea["iva"]
            if not iva or iva == "":
                iva = 0

            # ref = _i.obtenerReferencia(linea["sku"], linea["size"])
            ref = linea["sku"]
            
            desc = _i.obtenerDescripcion(ref)
            qsatype.debug("Descripcion: " + str(desc))
            codiva = _i.obtenerCodImpuesto(linea["iva"])

            curLinea.setValueBuffer("idpedido", idpedido)
            curLinea.setValueBuffer("cantidad", linea["cantidad"])
            # curLinea.setValueBuffer("pvpunitarioiva", linea["pvpunitarioiva"])
            # curLinea.setValueBuffer("pvpsindtoiva", linea["pvpsindtoiva"])
            # curLinea.setValueBuffer("pvptotaliva", linea["pvptotaliva"])
            curLinea.setValueBuffer("pvpunitario", parseFloat(linea["pvpunitarioiva"] / ((100 + iva) / 100)))
            curLinea.setValueBuffer("pvpsindto", parseFloat(linea["pvpsindtoiva"] / ((100 + iva) / 100)))
            curLinea.setValueBuffer("pvptotal", parseFloat(linea["pvptotaliva"] / ((100 + iva) / 100)))
            curLinea.setValueBuffer("iva", iva)
            curLinea.setValueBuffer("descripcion", desc[:100] if desc else desc)
            curLinea.setValueBuffer("referencia", ref[:18] if ref else ref)
            curLinea.setValueBuffer("numlinea", nl)
            curLinea.setValueBuffer("dtolineal", 0)
            curLinea.setValueBuffer("dtopor", 0)
            curLinea.setValueBuffer("codimpuesto", codiva[:10] if codiva else codiva)
            curLinea.setValueBuffer("canpedidorect", 0)
            curLinea.setValueBuffer("totalenalbaran", 0)

            if not curLinea.commitBuffer():
                syncppal.iface.log(ustr("Error. No se pudo guardar la línea ", str(nl), " de la venta ", str(idpedido)), "shsyncorders")
                return False

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_obtenerCodSerie(self, nomPais, codPostal):
        codPais = None
        codSerie = "W"
        codPostal2 = None

        if not nomPais or nomPais == "":
            return codSerie

        codPais = qsatype.FLUtil.quickSqlSelect("paises", "codpais", "UPPER(codpais) = '" + nomPais.upper() + "'")
        if not codPais or codPais == "":
            return codSerie

        if codPais != "ES":
            codSerie = "X"
        elif codPostal and codPostal != "":
            codPostal2 = codPostal[:2]
            if codPostal2 == "35" or codPostal2 == "38" or codPostal2 == "51" or codPostal2 == "52":
                codSerie = "X"

        return codSerie

    def sanhigia_sync_obtenerEjercicio(self, fecha):
        fecha = fecha[:10]
        datosFecha = fecha.split("-")

        return str(datosFecha[0])

    def sanhigia_sync_obtenerHora(self, fecha):
        h = fecha[-(8):]
        h = "23:59:59" if h == "00:00:00" else h

        return h

    def sanhigia_sync_obtenerCodPais(self, paisfc):
        if not paisfc or paisfc == "":
            return ""

        codPais = qsatype.FLUtil.quickSqlSelect("paises", "codpais", "UPPER(codpais) = '" + paisfc.upper() + "'")
        if not codPais or codPais == "":
            return ""

        return codPais

    def sanhigia_sync_obtenerCodPago(self, metPago):
        codPago = qsatype.FLUtil.quickSqlSelect("mg_formaspago", "codpago", "mg_metodopago = '" + str(metPago) + "'")
        if not codPago:
            codPago = qsatype.FactoriaModulos.get('flfactppal').iface.pub_valorDefectoEmpresa("codpago")

        return codPago

    def sanhigia_sync_conFac(self, fac):
        if not fac or fac == "":
            return False
        return True

    def sanhigia_sync_obtenerColor(self, ref, talla):
        if talla is not False and talla is not None and talla != "No":
            return qsatype.FLUtil.quickSqlSelect("atributosarticulos", "color", "UPPER(referencia) = '" + str(ref) + "' AND talla = '" + str(talla) + "'")
        else:
            return qsatype.FLUtil.quickSqlSelect("atributosarticulos", "color", "UPPER(referencia) = '" + str(ref) + "'")

    def sanhigia_sync_obtenerTalla(self, talla):
        if talla:
            return talla
        else:
            return "TU"

    def sanhigia_sync_obtenerReferencia(self, sku, talla):
        if talla is not False and talla is not None and talla != "No":
            sku = sku[:len(sku) - len(talla) - 1]
        return sku

    def sanhigia_sync_obtenerNumLineaComanda(self, idpedido):
        # codigo = "WEB" + qsatype.FactoriaModulos.get("flfactppal").iface.cerosIzquierda(str(codigo), 9)
        # idPedido = qsatype.FLUtil.quickSqlSelect("pedidoscli", "idpedido", "codigo = '" + str(codigo) + "'")
        numL = parseInt(qsatype.FLUtil.quickSqlSelect("lineaspedidoscli", "count(*)", "idpedido = " + str(idpedido)))
        if isNaN(numL):
            numL = 0
        return numL + 1

    def sanhigia_sync_obtenerDescripcion(self, ref):
        return qsatype.FLUtil.quickSqlSelect("articulos", "descripcion", "referencia = '" + str(ref) + "'")

    def sanhigia_sync_obtenerBarcode(self, ref, talla):
        if talla is not False and talla is not None and talla != "No":
            return qsatype.FLUtil.quickSqlSelect("atributosarticulos", "barcode", "UPPER(referencia) = '" + str(ref) + "' AND talla = '" + str(talla) + "'")
        else:
            return qsatype.FLUtil.quickSqlSelect("atributosarticulos", "barcode", "UPPER(referencia) = '" + str(ref) + "'")

    def sanhigia_sync_obtenerCodImpuesto(self, iva):
        codImpuesto = qsatype.FLUtil.quickSqlSelect("impuestos", "codimpuesto", "iva = " + str(iva))
        return codImpuesto

    def sanhigia_sync_creaLineaGastosComanda(self, curPedido, gastos):
        try:
            tieneIva = curPedido.valueBuffer("totaliva")
            idComanda = curPedido.valueBuffer("idtpv_comanda")
            codigo = curPedido.valueBuffer("codigo")

            if not idComanda or idComanda == 0:
                return False
            if not gastos or gastos == 0:
                return True

            curLGastos = qsatype.FLSqlCursor("tpv_lineascomanda")
            curLGastos.setModeAccess(curLGastos.Insert)
            curLGastos.refreshBuffer()

            curLGastos.setValueBuffer("idtpv_comanda", idComanda)
            curLGastos.setValueBuffer("codcomanda", codigo[:12] if codigo else codigo)
            curLGastos.setValueBuffer("referencia", "0000ATEMP00001")
            curLGastos.setValueBuffer("barcode", "8433613403654")
            curLGastos.setValueBuffer("descripcion", "MANIPULACIÓN Y ENVIO")

            gastosSinIva = None

            if tieneIva and tieneIva != 0:
                curLGastos.setValueBuffer("codimpuesto", "GEN")
                curLGastos.setValueBuffer("iva", 21)
                gastosSinIva = gastos / (1 + (parseFloat(21) / 100))
            else:
                curLGastos.setValueBuffer("codimpuesto", "EXT")
                curLGastos.setValueBuffer("iva", 0)
                gastosSinIva = gastos

            # curLGastos.setValueBuffer("ivaincluido", True)
            curLGastos.setValueBuffer("pvpunitarioiva", gastos)
            curLGastos.setValueBuffer("pvpunitario", gastosSinIva)
            curLGastos.setValueBuffer("pvpsindto", gastosSinIva)
            curLGastos.setValueBuffer("pvptotal", gastosSinIva)
            curLGastos.setValueBuffer("pvptotaliva", gastos)
            curLGastos.setValueBuffer("pvpsindtoiva", gastos)
            curLGastos.setValueBuffer("codtienda", "AWEB")

            idsincro = qsatype.FactoriaModulos.get('formRecordtpv_lineascomanda').iface.pub_commonCalculateField("idsincro", curLGastos)
            curLGastos.setValueBuffer("idsincro", idsincro[:30] if idsincro else idsincro)

            if not curLGastos.commitBuffer():
                syncppal.iface.log(ustr("Error. No se pudo crear la línea de gastos de la venta ", str(codigo)), "shsyncorders")
                return False

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_creaLineaDescuento(self, curPedido, dto, descripcion):
        try:
            codigo = curPedido.valueBuffer("codigo")
            idpedido = curPedido.valueBuffer("idpedido")

            if not codigo or codigo == 0 or not dto or dto == 0 or dto == "0.0000" or dto == "0.00":
                return True

            ref = "DTOWEB"
            desc = "DESCUENTO: " + descripcion
 
            curLDesc = qsatype.FLSqlCursor("lineaspedidoscli")
            curLDesc.setModeAccess(curLDesc.Insert)
            curLDesc.refreshBuffer()
            curLDesc.setValueBuffer("idpedido", idpedido)
            curLDesc.setValueBuffer("referencia", ref[:18] if ref else ref)
            #curLDesc.setValueBuffer("barcode", bC[:20] if bC else bC)
            curLDesc.setValueBuffer("descripcion", desc[:100] if desc else desc)
            curLDesc.setValueBuffer("codimpuesto", "IVA21")
            curLDesc.setValueBuffer("iva", 21)
            dtoSinIva = dto / (1 + (parseFloat(21) / 100))
            # curLDesc.setValueBuffer("ivaincluido", True)
            curLDesc.setValueBuffer("pvpunitarioiva", dto)
            curLDesc.setValueBuffer("pvpunitario", dtoSinIva)
            curLDesc.setValueBuffer("pvpsindto", dtoSinIva)
            curLDesc.setValueBuffer("pvptotal", dtoSinIva)
            curLDesc.setValueBuffer("pvptotaliva", dto)
            curLDesc.setValueBuffer("pvpsindtoiva", dto)
            curLDesc.setValueBuffer("totalenalbaran", 0)

            if not curLDesc.commitBuffer():
                syncppal.iface.log(ustr("Error. No se pudo crear la línea de descuento de la venta ", str(codigo)), "shsyncorders")
                return False

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_cerrarVentaWeb(self, curPedido):
        _i = self.iface

        try:
            idComanda = curPedido.valueBuffer("idtpv_comanda")

            codArqueo = _i.crearArqueoVentaWeb(curPedido)
            if not codArqueo:
                syncppal.iface.log(ustr("Error. No se pudo crear el arqueo"), "shsyncorders")
                return False

            if not _i.crearPagoVentaWeb(curPedido, codArqueo):
                syncppal.iface.log(ustr("Error. No se pudo crear el pago para el arqueo ", str(codArqueo)), "shsyncorders")
                return False

            if not qsatype.FLSqlQuery().execSql(u"UPDATE tpv_comandas SET estado = 'Cerrada', editable = true, pagado = total WHERE idtpv_comanda = " + str(idComanda)):
                syncppal.iface.log(ustr("Error. No se pudo cerrar la venta ", str(idComanda)), "shsyncorders")
                return False

            d = qsatype.Date()
            if not qsatype.FactoriaModulos.get('formtpv_tiendas').iface.marcaFechaSincroTienda("AWEB", "VENTAS_TPV", d):
                return False

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_crearArqueoVentaWeb(self, curPedido):
        _i = self.iface

        try:
            codTienda = "AWEB"
            fecha = curPedido.valueBuffer("fecha")

            idArqueo = qsatype.FLUtil.sqlSelect("tpv_arqueos", "idtpv_arqueo", "codtienda = '" + codTienda + "' AND diadesde = '" + str(fecha) + "'")
            if idArqueo:
                return idArqueo

            codTpvPuntoVenta = qsatype.FLUtil.sqlSelect("tpv_puntosventa", "codtpv_puntoventa", "codtienda = '" + codTienda + "'")

            curArqueo = qsatype.FLSqlCursor("tpv_arqueos")
            curArqueo.setActivatedCommitActions(False)
            curArqueo.setActivatedCheckIntegrity(False)
            curArqueo.setModeAccess(curArqueo.Insert)
            curArqueo.refreshBuffer()

            curArqueo.setValueBuffer("abierta", True)
            curArqueo.setValueBuffer("sincronizado", False)
            curArqueo.setValueBuffer("idfactura", 0)
            curArqueo.setValueBuffer("diadesde", fecha)
            curArqueo.setValueBuffer("horadesde", "00:00:01")
            curArqueo.setValueBuffer("ptoventa", codTpvPuntoVenta[:6] if codTpvPuntoVenta else codTpvPuntoVenta)
            curArqueo.setValueBuffer("codtpv_agenteapertura", "0350")
            curArqueo.setValueBuffer("codtienda", codTienda)

            if not _i.masDatosArqueo(curArqueo, curPedido):
                return False

            idArqueo = qsatype.FactoriaModulos.get("formRecordtpv_arqueos").iface.codigoArqueo(curArqueo)
            curArqueo.setValueBuffer("idtpv_arqueo", idArqueo[:8] if idArqueo else idArqueo)

            if not curArqueo.commitBuffer():
                return False

            return idArqueo

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_crearPagoVentaWeb(self, curPedido, idArqueo):
        try:
            if not idArqueo or not curPedido:
                return False

            fecha = curPedido.valueBuffer("fecha")
            codTienda = "AWEB"
            idComanda = curPedido.valueBuffer("idtpv_comanda")
            codComanda = curPedido.valueBuffer("codigo")
            codTpvPuntoVenta = curPedido.valueBuffer("codtpv_puntoventa")
            codPago = curPedido.valueBuffer("codpago")
            importe = curPedido.valueBuffer("total")

            if not importe:
                importe = 0

            curPago = qsatype.FLSqlCursor("tpv_pagoscomanda")
            curPago.setModeAccess(curPago.Insert)
            curPago.refreshBuffer()

            curPago.setValueBuffer("idtpv_comanda", idComanda)
            curPago.setValueBuffer("codcomanda", codComanda[:12] if codComanda else codComanda)
            curPago.setValueBuffer("idtpv_arqueo", idArqueo[:8] if idArqueo else idArqueo)
            curPago.setValueBuffer("fecha", fecha)
            curPago.setValueBuffer("editable", True)
            curPago.setValueBuffer("nogenerarasiento", True)
            curPago.setValueBuffer("anulado", False)
            curPago.setValueBuffer("importe", importe)
            curPago.setValueBuffer("estado", "Pagado")
            curPago.setValueBuffer("codpago", codPago[:10] if codPago else codPago)
            curPago.setValueBuffer("codtpv_puntoventa", codTpvPuntoVenta[:6] if codTpvPuntoVenta else codTpvPuntoVenta)
            curPago.setValueBuffer("codtpv_agente", "0350")
            curPago.setValueBuffer("codtienda", codTienda)

            idsincro = qsatype.FactoriaModulos.get("formRecordtpv_pagoscomanda").iface.commonCalculateField("idsincro", curPago)
            curPago.setValueBuffer("idsincro", idsincro[:30] if idsincro else idsincro)

            if not curPago.commitBuffer():
                return False

            return True

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_masDatosArqueo(self, curArqueo, curPedido):
        fecha = curPedido.valueBuffer("fecha")

        curArqueo.setValueBuffer("sincronizado", True)
        curArqueo.setValueBuffer("diahasta", fecha)
        curArqueo.setValueBuffer("horahasta", "23:59:59")

        return True

    def sanhigia_sync_obtenerCodFactura(self):
        try:
            prefijo = "AWEBX"
            ultimaFact = None

            idUltima = qsatype.FLUtil.sqlSelect("tpv_comandas", "egcodfactura", "egcodfactura LIKE '" + prefijo + "%' ORDER BY egcodfactura DESC")
            if idUltima:
                ultimaFact = parseInt(str(idUltima)[-(12 - len(prefijo)):])
            else:
                ultimaFact = 0
            ultimaFact = ultimaFact + 1

            return prefijo + qsatype.FactoriaModulos.get("flfactppal").iface.cerosIzquierda(str(ultimaFact), 12 - len(prefijo))

        except Exception as e:
            qsatype.debug(e)
            return False

    def sanhigia_sync_obtenerRegimenIva(self, order):
        if order['tax_amount'] > 0:
            cod = "General"
        elif int(order['store_id']) < 3:
            cod = "U.E."
        else:
            cod = "Exportaciones"

        return cod

    def sanhigia_sync_obtenerCodCliente(self, cif):
        cod = None
        if str(cif) != "-":
            cod = qsatype.FLUtil.sqlSelect("clientes", "codcliente", "UPPER(cifnif) = '" + str(cif).upper() + "' order by codcliente DESC limit 1")
        return cod

    def sanhigia_sync_damePaisMg(self, codPaisISO):        
        return qsatype.FLUtil.sqlSelect("paises", "codpais", "codiso = '" + str(codPaisISO) + "'")

    def __init__(self, context=None):
        super(sanhigia_sync, self).__init__(context)

    def getUnsynchronizedOrders(self):
        return self.ctx.sanhigia_sync_getUnsynchronizedOrders()

    def processOrders(self, orders):
        return self.ctx.sanhigia_sync_processOrders(orders)

    def creaCabeceraPedido(self, order, codigo):
        return self.ctx.sanhigia_sync_creaCabeceraPedido(order, codigo)

    def creaLineaEnvio(self, order, curPedido):
        return self.ctx.sanhigia_sync_creaLineaEnvio(order, curPedido)

    def creaLineaPedido(self, linea, curPedido, increment):
        return self.ctx.sanhigia_sync_creaLineaPedido(linea, curPedido, increment)

    def obtenerCodSerie(self, nomPais=None, codPostal=None):
        return self.ctx.sanhigia_sync_obtenerCodSerie(nomPais, codPostal)

    def obtenerEjercicio(self, fecha):
        return self.ctx.sanhigia_sync_obtenerEjercicio(fecha)

    def obtenerHora(self, fecha):
        return self.ctx.sanhigia_sync_obtenerHora(fecha)

    def obtenerCodPais(self, paisfc=None):
        return self.ctx.sanhigia_sync_obtenerCodPais(paisfc)

    def obtenerCodPago(self, metPago):
        return self.ctx.sanhigia_sync_obtenerCodPago(metPago)

    def conFac(self, fac):
        return self.ctx.sanhigia_sync_conFac(fac)

    def obtenerColor(self, ref, talla):
        return self.ctx.sanhigia_sync_obtenerColor(ref, talla)

    def obtenerTalla(self, talla):
        return self.ctx.sanhigia_sync_obtenerTalla(talla)

    def obtenerReferencia(self, sku, talla):
        return self.ctx.sanhigia_sync_obtenerReferencia(sku, talla)

    def obtenerNumLineaComanda(self, idpedido):
        return self.ctx.sanhigia_sync_obtenerNumLineaComanda(idpedido)

    def obtenerDescripcion(self, ref):
        return self.ctx.sanhigia_sync_obtenerDescripcion(ref)

    def obtenerBarcode(self, ref, talla):
        return self.ctx.sanhigia_sync_obtenerBarcode(ref, talla)

    def obtenerCodImpuesto(self, iva):
        return self.ctx.sanhigia_sync_obtenerCodImpuesto(iva)

    def creaLineaGastosComanda(self, curPedido, gastos):
        return self.ctx.sanhigia_sync_creaLineaGastosComanda(curPedido, gastos)

    def creaLineaDescuento(self, curPedido, dto, desc):
        return self.ctx.sanhigia_sync_creaLineaDescuento(curPedido, dto, desc)

    def cerrarVentaWeb(self, curPedido):
        return self.ctx.sanhigia_sync_cerrarVentaWeb(curPedido)

    def crearArqueoVentaWeb(self, curPedido):
        return self.ctx.sanhigia_sync_crearArqueoVentaWeb(curPedido)

    def crearPagoVentaWeb(self, curPedido, idArqueo):
        return self.ctx.sanhigia_sync_crearPagoVentaWeb(curPedido, idArqueo)

    def masDatosArqueo(self, curArqueo, curPedido):
        return self.ctx.sanhigia_sync_masDatosArqueo(curArqueo, curPedido)

    def obtenerCodFactura(self):
        return self.ctx.sanhigia_sync_obtenerCodFactura()

    def obtenerRegimenIva(self, order):
        return self.ctx.sanhigia_sync_obtenerRegimenIva(order)

    def obtenerCodCliente(self, cif):
        return self.ctx.sanhigia_sync_obtenerCodCliente(cif)

    def damePaisMg(self, codPaisISO):
        return self.ctx.sanhigia_sync_damePaisMg(codPaisISO)

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
