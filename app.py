import calendar
import datetime
import json
from zoneinfo import ZoneInfo
import io
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Control Pro", page_icon="📱", layout="wide")
ADMIN_PASS = "admin123"

@st.cache_resource
def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    json_info = json.loads(st.secrets["gcp_service_account"]["text"])
    creds = Credentials.from_service_account_info(json_info, scopes=scope)
    return gspread.authorize(creds).open("Base_Datos_Payjoy")

sh = conectar()

def get_h(p, c):
    try:
        data = sh.worksheet(p).get_all_records()
        if data:
            df = pd.DataFrame(data)
            for x in c:
                if x not in df.columns: df[x] = ""
            return df.dropna(how="all")
    except:
        pass
    return pd.DataFrame(columns=c)

def set_h(p, df):
    try:
        ws = sh.worksheet(p)
        ws.clear()
        if not df.empty:
            ws.update([df.columns.values.tolist()] + df.astype(str).values.tolist())
        else:
            ws.update([[]])
    except:
        pass

def cargar_datos():
    df_inv = get_h("inventario", ["Tipo de Tarjeta", "Cantidad Disponible"])
    inv = {str(r["Tipo de Tarjeta"]): int(r["Cantidad Disponible"]) for _, r in df_inv.iterrows() if str(r["Tipo de Tarjeta"]) != ""}
    ent = get_h("entradas", ["Fecha Registro", "Fecha de Llegada", "Tarjeta", "Cantidad", "Responsable"]).to_dict("records")
    tras = get_h("traslados", ["Fecha/Hora", "Tarjeta", "Cantidad", "Destino", "Responsable"]).to_dict("records")
    cred = get_h("creditos", ["Fecha", "Cliente", "Marca de Celular", "Tipo de Venta", "Aprobaron Tarjeta", "Lleva Tarjeta", "Tarjeta Entregada", "Tag Dispositivo", "Cantidad", "Asesor"]).to_dict("records")
    reg_t = get_h("registro_tarjetas", ["Fecha", "Cliente", "Tag Dispositivo", "Tarjeta", "Cantidad", "Asesor"]).to_dict("records")
    
    df_as = get_h("asesores", ["Asesor", "Contrasena"])
    asesores_base = [
        {"Asesor": "Edgardo", "Contrasena": "1234"},
        {"Asesor": "Alexandra", "Contrasena": "1234"},
        {"Asesor": "Yeriz", "Contrasena": "1234"},
        {"Asesor": "Alejandro", "Contrasena": "1234"},
        {"Asesor": "P Marca", "Contrasena": "1234"},
        {"Asesor": "A Rutero", "Contrasena": "1234"}
    ]
    if df_as.empty:
        df_as = pd.DataFrame(asesores_base)
        set_h("asesores", df_as)
    asesores_list = df_as.to_dict("records")

    df_m = get_h("marcas", ["Marca"])
    marcas_base = ["Samsung", "Motorola", "Oppo", "Infinix", "Vivo", "Xiaomi", "Honor", "Tecno", "Realme"]
    if df_m.empty:
        df_m = pd.DataFrame(marcas_base, columns=["Marca"])
        set_h("marcas", df_m)
    marcas_list = df_m["Marca"].dropna().unique().tolist()

    df_meta = get_h("meta", ["Meta"])
    meta_val = int(df_meta["Meta"].iloc[0]) if not df_meta.empty and "Meta" in df_meta.columns else 200
    return inv, ent, tras, cred, reg_t, asesores_list, marcas_list, meta_val

def guardar_inv(inv):
    set_h("inventario", pd.DataFrame(list(inv.items()), columns=["Tipo de Tarjeta", "Cantidad Disponible"]) if inv else pd.DataFrame(columns=["Tipo de Tarjeta", "Cantidad Disponible"]))

def guardar_lista(clave, lista):
    mapa = {"cred": "creditos", "reg_tarjetas": "registro_tarjetas", "ent": "entradas", "tras": "traslados", "asesores": "asesores", "marcas": "marcas"}
    set_h(mapa.get(clave, clave), pd.DataFrame(lista) if lista else pd.DataFrame())

def guardar_meta(m):
    set_h("meta", pd.DataFrame([{"Meta": m}]))

def a_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Reporte")
    return out.getvalue()

inventario, entradas, traslados, cred, reg_tarjetas, lista_asesores, MARCAS, META = cargar_datos()
TIPOS_VENTA = ["Venta en tienda", "Cliente agendado"]

st.title("Control Payjoy")
st.markdown("---")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Registrar Venta",
        "Registrar Tarjeta",
        "Dashboard",
        "Pendientes",
        "Stock",
        "Ingresar Lote",
        "Traslado",
        "Historiales",
        "Gestion"
    ]
)

nombres_asesores_plana = [a["Asesor"] for a in lista_asesores if "Asesor" in a] if lista_asesores else ["Sin Asesor"]

if menu == "Registrar Venta":
    st.header("Registrar Venta")
    
    cliente = st.text_input("Cliente").strip().title()
    marca = st.selectbox("Marca", MARCAS)
    tipo = st.selectbox("Tipo", TIPOS_VENTA)
    aprobaron = st.selectbox("Aprobaron tarjeta?", ["Si", "No"])
    
    lleva_t = "No"
    tarj_sel = None
    cant_t = 0
    stock_act = 0
    tag_dispositivo = "N/A"

    if aprobaron == "Si":
        lleva_t = st.selectbox("Lleva Tarjeta?", ["Si", "No"])
        if lleva_t == "Si":
            if not inventario:
                st.error("Sin stock de tarjetas disponible.")
            else:
                tarj_sel = st.selectbox("Tarjeta", list(inventario.keys()))
                stock_act = inventario[tarj_sel]
                st.write("Stock actual: " + str(stock_act))
                cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
            tag_dispositivo = st.text_input("Tag del Dispositivo").strip()

    fecha_v = st.date_input("Fecha", value=datetime.datetime.now(ZoneInfo("America/Bogota")).date())
    asesor = st.selectbox("Asesor", nombres_asesores_plana)

    if st.button("Guardar Venta", type="primary"):
        if not cliente:
            st.warning("Falta el nombre del cliente.")
        elif aprobaron == "Si" and lleva_t == "Si" and not inventario:
            st.error("No hay tarjetas en stock.")
        elif aprobaron == "Si" and lleva_t == "Si" and cant_t > stock_act:
            st.error("Stock insuficiente.")
        else:
            if aprobaron == "Si" and lleva_t == "Si" and tarj_sel:
                inventario[tarj_sel] -= cant_t
                guardar_inv(inventario)

            cred.append({
                "Fecha": str(fecha_v),
                "Cliente": cliente,
                "Marca de Celular": marca,
                "Tipo de Venta": tipo,
                "Aprobaron Tarjeta": aprobaron,
                "Lleva Tarjeta": lleva_t,
                "Tarjeta Entregada": tarj_sel if (aprobaron == "Si" and lleva_t == "Si") else "N/A",
                "Tag Dispositivo": tag_dispositivo if (aprobaron == "Si" and lleva_t == "Si" and tag_dispositivo) else "N/A",
                "Cantidad": 1,
                "Asesor": asesor,
            })
            guardar_lista("cred", cred)
            if aprobaron == "Si" and lleva_t == "No":
                st.success("Venta registrada. Quedo en Pendientes de Entrega.")
            else:
                st.success("Venta registrada con exito.")
            st.rerun()

elif menu == "Registrar Tarjeta":
    st.header("Registrar Tarjeta")
    if not inventario:
        st.error("Sin stock.")
    else:
        with st.form("f_reg_t", clear_on_submit=True):
            cliente_t = st.text_input("Cliente").strip().title()
            tag_disp = st.text_input("Tag").strip()
            tarj_elegida = st.selectbox("Tarjeta", list(inventario.keys()))
            cant_asig = st.number_input("Cantidad", min_value=1, step=1, value=1)
            fecha_reg = st.date_input("Fecha", value=datetime.datetime.now(ZoneInfo("America/Bogota")).date())
            asesor_reg = st.selectbox("Asesor", nombres_asesores_plana)

            if st.form_submit_button("Registrar", type="primary"):
                stock_disp_actual = inventario.get(tarj_elegida, 0)
                if not cliente_t:
                    st.warning("Falta cliente.")
                elif not tag_disp:
                    st.warning("Falta tag.")
                elif cant_asig > stock_disp_actual:
                    st.error("Stock insuficiente.")
                else:
                    inventario[tarj_elegida] -= cant_asig
                    guardar_inv(inventario)

                    reg_tarjetas.append({
                        "Fecha": str(fecha_reg),
                        "Cliente": cliente_t,
                        "Tag Dispositivo": tag_disp,
                        "Tarjeta": tarj_elegida,
                        "Cantidad": cant_asig,
                        "Asesor": asesor_reg
                    })
                    guardar_lista("reg_tarjetas", reg_tarjetas)
                    st.success("Registrado.")

        st.markdown("---")
        st.subheader("Historial")
        if reg_tarjetas:
            df_reg_t = pd.DataFrame(reg_tarjetas)
            st.dataframe(df_reg_t, use_container_width=True)
            st.download_button("Excel", a_excel(df_reg_t), "tarjetas.xlsx")
        else:
            st.info("Sin registros.")

elif menu == "Dashboard":
    st.header("Dashboard")
    ahora = datetime.datetime.now(ZoneInfo("America/Bogota"))
    dias_mes = calendar.monthrange(ahora.year, ahora.month)[1]
    df_mes = pd.DataFrame()
    ventas_mes = 0

    if cred:
        df_c = pd.DataFrame(cred)
        if "Fecha" in df_c.columns and "Cantidad" in df_c.columns:
            df_c["_dt"] = pd.to_datetime(df_c["Fecha"], errors="coerce")
            df_mes = df_c[(df_c["_dt"].dt.month == ahora.month) & (df_c["_dt"].dt.year == ahora.year)]
            ventas_mes = int(df_mes["Cantidad"].sum()) if not df_mes.empty else 0

    pct = min(round((ventas_mes / META) * 100, 2), 100.0) if META > 0 else 0.0
    prom_diario = (ventas_mes / ahora.day) if ahora.day > 0 else 0
    proy = int(prom_diario * dias_mes)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meta", str(META))
    c2.metric("Vendidos", str(ventas_mes))
    c3.metric("Cumple", str(pct) + "%")
    c4.metric("Proyeccion", str(proy))

    st.progress(min(ventas_mes / META, 1.0) if META > 0 else 1.0)
    st.markdown("---")

    if not df_mes.empty and "Marca de Celular" in df_mes.columns:
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Por Asesor")
            df_a = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
            st.plotly_chart(px.pie(df_a, names="Asesor", values="Cantidad", hole=0.4), use_container_width=True)
        with g2:
            st.subheader("Por Marca")
            df_m = df_mes.groupby("Marca de Celular")["Cantidad"].sum().reset_index()
            st.plotly_chart(px.bar(df_m, x="Marca de Celular", y="Cantidad"), use_container_width=True)

        st.subheader("Detalle")
        t_asesor = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
        t_asesor["% Meta"] = ((t_asesor["Cantidad"] / META) * 100).round(2).astype(str) + "%" if META > 0 else "0%"
        st.dataframe(t_asesor, use_container_width=True)
    else:
        st.info("Sin registros este mes.")

elif menu == "Pendientes":
    st.header("Pendientes")
    pendientes = [(i, c) for i, c in enumerate(cred) if c.get("Aprobaron Tarjeta") == "Si" and c.get("Lleva Tarjeta") == "No"]

    if not pendientes:
        st.info("Sin pendientes.")
    elif not inventario:
        st.error("Sin stock.")
    else:
        with st.form("f_pend", clear_on_submit=True):
            ops = ["#" + str(i) + " - " + str(c.get('Cliente')) for i, c in pendientes]
            elegido = st.selectbox("Seleccione", ops)
            t_ent = st.selectbox("Tarjeta", list(inventario.keys()))
            stock_b = inventario[t_ent]
            st.write("Stock: " + str(stock_b))
            tag_pend = st.text_input("Tag").strip()

            if st.form_submit_button("Confirmar"):
                if stock_b < 1:
                    st.error("Sin stock.")
                else:
                    idx = int(elegido.split("#")[1].split(" ")[0])
                    inventario[t_ent] -= 1
                    guardar_inv(inventario)
                    cred[idx]["Lleva Tarjeta"] = "Si"
                    cred[idx]["Tarjeta Entregada"] = t_ent
                    if tag_pend:
                        cred[idx]["Tag Dispositivo"] = tag_pend
                    guardar_lista("cred", cred)
                    st.success("Entregado.")
                    st.rerun()

elif menu == "Stock":
    st.header("Stock")
    if not inventario:
        st.info("Vacio.")
    else:
        st.dataframe(pd.DataFrame(list(inventario.items()), columns=["Tarjeta", "Cantidad"]), use_container_width=True)

elif menu == "Ingresar Lote":
    st.header("Lote")
    with st.form("f_lote", clear_on_submit=True):
        t_nombre = st.text_input("Nombre").strip().title()
        cant = st.number_input("Cantidad", min_value=1, step=1, value=10)
        f_lleg = st.date_input("Fecha", value=datetime.datetime.now(ZoneInfo("America/Bogota")).date())
        resp = st.selectbox("Responsable", nombres_asesores_plana)

        if st.form_submit_button("Guardar"):
            if t_nombre:
                inventario[t_nombre] = inventario.get(t_nombre, 0) + cant
                entradas.append({
                    "Fecha Registro": datetime.datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M"),
                    "Fecha de Llegada": str(f_lleg),
                    "Tarjeta": t_nombre,
                    "Cantidad": cant,
                    "Responsable": resp,
                })
                guardar_inv(inventario)
                guardar_lista("ent", entradas)
                st.success("Guardado.")
            else:
                st.warning("Falta nombre.")

elif menu == "Traslado":
    st.header("Traslado")
    with st.form("f_tras", clear_on_submit=True):
        t_sel = st.selectbox("Tarjeta", list(inventario.keys())) if inventario else None
        if not t_sel:
            st.warning("Sin stock.")
        else:
            stock_a = inventario[t_sel]
            st.write("Stock: " + str(stock_a))
            cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
            destino = st.text_input("Destino").strip().title()
            resp_s = st.selectbox("Responsable", nombres_asesores_plana)

            if st.form_submit_button("Trasladar"):
                if not destino:
                    st.warning("Falta destino.")
                elif cant_t > stock_a:
                    st.error("Stock insuficiente.")
                else:
                    inventario[t_sel] -= cant_t
                    traslados.append({
                        "Fecha/Hora": datetime.datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M"),
                        "Tarjeta": t_sel,
                        "Cantidad": cant_t,
                        "Destino": destino,
                        "Responsable": resp_s,
                    })
                    guardar_inv(inventario)
                    guardar_lista("tras", traslados)
                    st.success("Traslado exitoso.")

elif menu == "Historiales":
    st.header("Historiales")
    sub = st.radio("Ver", ["Creditos", "Tarjetas", "Entradas", "Traslados"])
    st.markdown("---")

    if sub == "Creditos":
        df_r = pd.DataFrame(cred) if cred else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "creditos.xlsx")

        if cred:
            st.markdown("---")
            st.subheader("Anular Credito")
            pass_anular = st.text_input("Password Admin", type="password", key="pass_anulacion")
            ops = ["#" + str(i) + " - " + str(c.get('Cliente')) for i, c in enumerate(cred)]
            a_borrar = st.selectbox("Seleccione", ops, key="sel_cred_anular")
            
            if st.button("Anular", type="primary", key="btn_anular_cred"):
                if pass_anular == ADMIN_PASS:
                    idx = int(a_borrar.split("#")[1].split(" ")[0])
                    item = cred.pop(idx)
                    if item.get("Lleva Tarjeta") == "Si" and item.get("Tarjeta Entregada") != "N/A":
                        t = item.get("Tarjeta Entregada")
                        inventario[t] = inventario.get(t, 0) + 1
                        guardar_inv(inventario)
                    guardar_lista("cred", cred)
                    st.success("Anulado.")
                    st.rerun()
                else:
                    st.error("Password incorrecta.")

    elif sub == "Tarjetas":
        df_r = pd.DataFrame(reg_tarjetas) if reg_tarjetas else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "tarjetas.xlsx")

    elif sub == "Entradas":
        df_r = pd.DataFrame(entradas) if entradas else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "entradas.xlsx")

    elif sub == "Traslados":
        df_r = pd.DataFrame(traslados) if traslados else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "traslados.xlsx")

elif menu == "Gestion":
    st.header("Gestion Admin")
    pass_ingresada = st.text_input("Password Admin", type="password", key="pass_admin_gen")
    
    if pass_ingresada == ADMIN_PASS:
        st.success("Acceso concedido.")
        tab1, tab2, tab3 = st.tabs(["Asesores", "Marcas", "Meta"])
        
        with tab1:
            nuevo_nombre = st.text_input("Asesor").strip().title()
            nueva_pass = st.text_input("Password", type="password", key="pass_as_nuevo").strip()
            if st.button("Crear Asesor", key="btn_crear_as"):
                if not nuevo_nombre or not nueva_pass:
                    st.error("Campos vacios.")
                elif any(str(a.get("Asesor")) == nuevo_nombre for a in lista_asesores):
                    st.warning("Ya existe.")
                else:
                    lista_asesores.append({"Asesor": nuevo_nombre, "Contrasena": nueva_pass})
                    guardar_lista("asesores", lista_asesores)
                    st.success("Creado.")
                    st.rerun()

            st.markdown("---")
            if lista_asesores:
                st.dataframe(pd.DataFrame(lista_asesores), use_container_width=True)
                nombres_borrar = [str(a.get("Asesor")) for a in lista_asesores if a.get("Asesor") != "Edgardo" and "Asesor" in a]
                if nombres_borrar:
                    asesor_a_borrar = st.selectbox("Eliminar", nombres_borrar, key="del_a")
                    if st.button("Borrar Asesor", type="primary", key="btn_del_asesor"):
                        lista_asesores = [a for a in lista_asesores if str(a.get("Asesor")) != asesor_a_borrar]
                        guardar_lista("asesores", lista_asesores)
                        st.success("Eliminado.")
                        st.rerun()

        with tab2:
            nueva_marca = st.text_input("Marca").strip().title()
            if st.button("Agregar Marca", key="btn_agregar_marca"):
                if not nueva_marca:
                    st.error("Vacio.")
                elif nueva_marca in MARCAS:
                    st.warning("Ya existe.")
                else:
                    MARCAS.append(nueva_marca)
                    guardar_lista("marcas", [{"Marca": m} for m in MARCAS])
                    st.success("Agregada.")
                    st.rerun()

            st.markdown("---")
            if MARCAS:
                st.dataframe(pd.DataFrame(MARCAS, columns=["Marca"]), use_container_width=True)
                marca_a_borrar = st.selectbox("Eliminar", MARCAS, key="del_m")
                if st.button("Borrar Marca", type="primary", key="btn_del_marca"):
                    MARCAS.remove(marca_a_borrar)
                    guardar_lista("marcas", [{"Marca": m} for m in MARCAS])
                    st.success("Eliminada.")
          
