import calendar
import datetime
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
    # Leemos directamente desde st.secrets
    sec = st.secrets["gcp_service_account"]
    creds_dict = {
        "type": sec["type"],
        "project_id": sec["project_id"],
        "private_key_id": sec["private_key_id"],
        "private_key": sec["private_key"].replace("\\n", "\n"),
        "client_email": sec["client_email"],
        "client_id": sec["client_id"],
        "auth_uri": sec["auth_uri"],
        "token_uri": sec["token_uri"],
        "auth_provider_x509_cert_url": sec["auth_provider_x509_cert_url"],
        "client_x509_cert_url": sec["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
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
    if df_as.empty:
        df_as = pd.DataFrame([{"Asesor": "Edgardo", "Contrasena": "1234"}, {"Asesor": "Alexandra", "Contrasena": "1234"}])
        set_h("asesores", df_as)
    asesores_list = df_as.to_dict("records")

    df_m = get_h("marcas", ["Marca"])
    if df_m.empty:
        df_m = pd.DataFrame(["Samsung", "Motorola", "Oppo", "Infinix", "Vivo", "Xiaomi", "Honor", "Tecno", "Realme"], columns=["Marca"])
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

menu = st.sidebar.selectbox("Menu", ["Registrar Venta", "Registrar Tarjeta", "Dashboard", "Pendientes", "Stock", "Ingresar Lote", "Traslado", "Historiales", "Gestion"])
nombres_asesores_plana = [a["Asesor"] for a in lista_asesores if "Asesor" in a] if lista_asesores else ["Sin Asesor"]

if menu == "Registrar Venta":
    st.header("Registrar Venta")
    cliente = st.text_input("Cliente").strip().title()
    marca = st.selectbox("Marca", MARCAS)
    tipo = st.selectbox("Tipo", TIPOS_VENTA)
    aprobaron = st.selectbox("Aprobaron tarjeta?", ["Si", "No"])
    lleva_t, tarj_sel, cant_t, stock_act, tag_disp = "No", None, 0, 0, "N/A"
    
    if aprobaron == "Si":
        lleva_t = st.selectbox("Lleva Tarjeta?", ["Si", "No"])
        if lleva_t == "Si" and inventario:
            tarj_sel = st.selectbox("Tarjeta", list(inventario.keys()))
            stock_act = inventario[tarj_sel]
            st.write("Stock actual: " + str(stock_act))
            cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
            tag_disp = st.text_input("Tag del Dispositivo").strip()

    fecha_v = st.date_input("Fecha", value=datetime.datetime.now(ZoneInfo("America/Bogota")).date())
    asesor = st.selectbox("Asesor", nombres_asesores_plana)

    if st.button("Guardar Venta", type="primary"):
        if not cliente: st.warning("Falta cliente.")
        elif aprobaron == "Si" and lleva_t == "Si" and cant_t > stock_act: st.error("Stock insuficiente.")
        else:
            if aprobaron == "Si" and lleva_t == "Si" and tarj_sel:
                inventario[tarj_sel] -= cant_t
                guardar_inv(inventario)
            cred.append({"Fecha": str(fecha_v), "Cliente": cliente, "Marca de Celular": marca, "Tipo de Venta": tipo, "Aprobaron Tarjeta": aprobaron, "Lleva Tarjeta": lleva_t, "Tarjeta Entregada": tarj_sel or "N/A", "Tag Dispositivo": tag_disp, "Cantidad": 1, "Asesor": asesor})
            guardar_lista("cred", cred)
            st.success("Guardado con exito.")
            st.rerun()

elif menu == "Stock":
    st.header("Stock")
    if inventario: st.dataframe(pd.DataFrame(list(inventario.items()), columns=["Tarjeta", "Cantidad"]), use_container_width=True)
    else: st.info("Vacio.")

elif menu == "Gestion":
    st.header("Gestion Admin")
    pass_ing = st.text_input("Password", type="password")
    if pass_ing == ADMIN_PASS:
        st.success("Acceso concedido.")
        meta_n = st.number_input("Meta", value=int(META))
        if st.button("Actualizar Meta"):
            guardar_meta(meta_n)
            st.success("Actualizado.")
            st.rerun()
    elif pass_ing: st.error("Incorrecto.")
            
