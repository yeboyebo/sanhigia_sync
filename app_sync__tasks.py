from AQNEXT.celery import app
from YBLEGACY import qsatype
from YBUTILS import globalValues
from YBUTILS import DbRouter

from models.flsyncppal import flsyncppal_def as syncppal
from models.flsyncppal import sh_importOrders_def as iGbOrders
from models.flsyncppal import sh_updateStocks_def as iGbStocks
from models.flsyncppal import sh_updatePrices_def as iGbPrices
from models.flsyncppal import sh_importCustomers_def as iGbCust
from models.flsyncppal import sh_updatePvpCondCli_def as iGbPvpCond

from models.flsyncppal import sh_enviocorreosegui_def


globalValues.registrarmodulos()
cdDef = 10


def getActivity():
    i = app.control.inspect()
    active = i.active()
    scheduled = i.scheduled()
    reserved = i.reserved()

    aActive = {}
    for w in active:
        for t in active[w]:
            aActive[t['id']] = {}
            aActive[t['id']]['worker'] = w
            aActive[t['id']]['id'] = t['id']
            aActive[t['id']]['name'] = t['name']
            aActive[t['id']]['args'] = t['args']
    aScheduled = {}
    for w in scheduled:
        for t in scheduled[w]:
            aScheduled[t['request']['id']] = {}
            aScheduled[t['request']['id']]['worker'] = w
            aScheduled[t['request']['id']]['eta'] = t['eta'][:19]
            aScheduled[t['request']['id']]['id'] = t['request']['id']
            aScheduled[t['request']['id']]['name'] = t['request']['name']
            aScheduled[t['request']['id']]['args'] = t['request']['args']
    aReserved = {}
    for w in reserved:
        for t in reserved[w]:
            aReserved[t['id']] = {}
            aReserved[t['id']]['worker'] = w
            aReserved[t['id']]['id'] = t['id']
            aReserved[t['id']]['name'] = t['name']
            aReserved[t['id']]['args'] = t['args']

    return {'active': aActive, 'scheduled': aScheduled, 'reserved': aReserved}


def revoke(id):
    app.control.revoke(id, terminate=True)
    return True


@app.task
def getUnsynchronizedOrders(r):
    DbRouter.ThreadLocalMiddleware.process_request_celery(None, r)

    try:
        cdTime = iGbOrders.iface.getUnsynchronizedOrders() or cdDef
    except Exception as e:
        print(e)
        syncppal.iface.log("Error. Fallo en tasks", "shsyncorders")
        cdTime = cdDef

    activo = False
    try:
        resul = qsatype.FLSqlQuery().execSql("SELECT activo FROM yb_procesos WHERE proceso = 'shsyncorders'", "yeboyebo")
        activo = resul[0][0]
    except Exception:
        activo = False

    if activo:
        getUnsynchronizedOrders.apply_async((r,), countdown=cdTime)
    else:
        syncppal.iface.log("Info. Proceso detenido", "shsyncorders")


@app.task
def updateProductStock(r):
    DbRouter.ThreadLocalMiddleware.process_request_celery(None, r)

    try:
        cdTime = iGbStocks.iface.updateProductStock() or cdDef
    except Exception:
        syncppal.iface.log("Error. Fallo en tasks", "shsyncstock")
        cdTime = cdDef

    activo = False
    try:
        resul = qsatype.FLSqlQuery().execSql("SELECT activo FROM yb_procesos WHERE proceso = 'shsyncstock'", "yeboyebo")
        activo = resul[0][0]
    except Exception:
        activo = False

    if activo:
        updateProductStock.apply_async((r,), countdown=cdTime)
    else:
        syncppal.iface.log("Info. Proceso detenido", "shsyncstock")


@app.task
def updateProductPrice(r):
    DbRouter.ThreadLocalMiddleware.process_request_celery(None, r)

    try:
        cdTime = iGbPrices.iface.updateProductPrice() or cdDef
    except Exception as e:
        syncppal.iface.log("Error. Fallo en tasks " + e, "shsyncprices")
        cdTime = cdDef

    activo = False
    try:
        resul = qsatype.FLSqlQuery().execSql("SELECT activo FROM yb_procesos WHERE proceso = 'shsyncprices'", "yeboyebo")
        activo = resul[0][0]
    except Exception:
        activo = False

    if activo:
        updateProductPrice.apply_async((r,), countdown=cdTime)
    else:
        syncppal.iface.log("Info. Proceso detenido", "shsyncprices")


@app.task
def getUnsynchronizedCustomers(r):
    DbRouter.ThreadLocalMiddleware.process_request_celery(None, r)

    try:
        cdTime = iGbCust.iface.getUnsynchronizedCustomers() or cdDef
    except Exception:
        syncppal.iface.log("Error. Fallo en tasks", "shsynccust")
        cdTime = cdDef

    activo = False
    try:
        resul = qsatype.FLSqlQuery().execSql("SELECT activo FROM yb_procesos WHERE proceso = 'shsynccust'", "yeboyebo")
        activo = resul[0][0]
    except Exception:
        activo = False

    if activo:
        getUnsynchronizedCustomers.apply_async((r,), countdown=cdTime)
    else:
        syncppal.iface.log("Info. Proceso detenido", "shsynccust")


@app.task
def updatePvpCondCli(r):
    DbRouter.ThreadLocalMiddleware.process_request_celery(None, r)

    try:
        cdTime = iGbPvpCond.iface.updatePvpCondCli() or cdDef
    except Exception:
        syncppal.iface.log("Error. Fallo en tasks", "syncpvpcondcli")
        cdTime = cdDef

    activo = False
    try:
        resul = qsatype.FLSqlQuery().execSql("SELECT activo FROM yb_procesos WHERE proceso = 'syncpvpcondcli'", "yeboyebo")
        activo = resul[0][0]
    except Exception:
        activo = False

    if activo:
        updatePvpCondCli.apply_async((r,), countdown=cdTime)
    else:
        syncppal.iface.log("Info. Proceso detenido", "syncpvpcondcli")
