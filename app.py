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
        ws = sh.worksheet(p)
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            for x in c:
                if x not in df.columns:
                    df[x] = ""
            return df[c].dropna(how="all")
    except:
        pass
    return pd.DataFrame(columns=c)

def set_h(p, df):
    try:
        ws = sh.worksheet(p)
        ws.clear()
        if not df.empty:
            df_str = df.astype(str)
            ws.update([df_str.columns.values.tolist()] + df_str.values.tolist())
        else:
            ws.update([[]])
    except:
        pass

def cargar_datos():
    df_inv = get_h("inventario", ["Tipo de Tarjeta", "Cantidad Disponible"])
    inv = {}
    for _, r in df_inv.iterrows():
        t = str(r["Tipo de Tarjeta"]).strip()
        if t:
            try:
                inv[t] = int(r["Cantidad Disponible"])
            except:
                inv[t] = 0

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
    meta_val = int(df_meta["Meta"].iloc[0]) if not df_meta.empty and str(df_meta["Meta"].iloc[0]).isdigit() else 200
    return inv, ent, tras, cred, reg_t, asesores_list, marcas_list, meta_val

def guardar_inv(inv):
    cols = ["Tipo de Tarjeta", "Cantidad Disponible"]
    df = pd.DataFrame(list(inv.items()), columns=cols) if inv else pd.DataFrame(columns=cols)
    set_h("inventario", df)

def guardar_lista(clave, lista):
    mapa = {
        "cred": ("creditos", ["Fecha", "Cliente", "Marca de Celular", "Tipo de Venta", "Aprobaron Tarjeta", "Lleva Tarjeta", "Tarjeta Entregada", "Tag Dispositivo", "Cantidad", "Asesor"]),
        "reg_tarjetas": ("registro_tarjetas", ["Fecha", "Cliente", "Tag Dispositivo", "Tarjeta", "Cantidad", "Asesor"]),
        "ent": ("entradas", ["Fecha Registro", "Fecha de Llegada", "Tarjeta", "Cantidad", "Responsable"]),
        "tras": ("traslados", ["Fecha/Hora", "Tarjeta", "Cantidad", "Destino", "Responsable"]),
        "asesores": ("asesores", ["Asesor", "Contrasena"]),
        "marcas": ("marcas", ["Marca"])
    }
    pestana, cols = mapa.get(clave, (clave, []))
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    set_h(pestana, df[cols])

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
    
    lleva_t = "No"
    tarj_sel = None
    cant_t = 0
    stock_act = 0
    tag_dispositivo = "N/A"

    if aprobaron == "Si":
        lleva_t = st.selectbox("Lleva Tarjeta?", ["Si", "No"])
        if lleva_t == "Si":
            if not inventario:
                st.error("Sin stock disponible.")
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
            st.warning("Falta cliente.")
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
            st.success("Venta guardada con exito.")
            st.rerun()

elif menu == "Stock":
    st.header("Stock")
    if inventario:
        st.dataframe(pd.DataFrame(list(inventario.items()), columns=["Tarjeta", "Cantidad"]), use_container_width=True)
    else:
        st.info("Vacio.")

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
    elif pass_ing:
        st.error("Incorrecto.")
        
