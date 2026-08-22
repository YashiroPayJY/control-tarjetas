import calendar
import datetime
from zoneinfo import ZoneInfo
import io
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Control Pro - Payjoy", page_icon="📱", layout="wide"
)

ARCHIVOS = {
    "inv": "inventario.csv",
    "ent": "entradas.csv",
    "cred": "creditos.csv",
    "tras": "traslados.csv",
    "asesores": "asesores_control.csv",
    "marcas": "marcas_control.csv",
    "reg_tarjetas": "registro_tarjetas.csv",
}

ADMIN_PASS = "admin123"  # Contraseña maestra para gestionar asesores y marcas

def obtener_hora():
    return datetime.datetime.now(ZoneInfo("America/Bogota"))

def cargar_csv(archivo):
    if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
        try:
            return pd.read_csv(archivo).dropna(how="all")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def cargar_datos():
    df_inv = cargar_csv(ARCHIVOS["inv"])
    inv = {}
    if not df_inv.empty and "Tipo de Tarjeta" in df_inv.columns:
        inv = dict(zip(df_inv["Tipo de Tarjeta"], df_inv["Cantidad Disponible"]))

    ent = cargar_csv(ARCHIVOS["ent"]).to_dict("records") if not cargar_csv(ARCHIVOS["ent"]).empty else []
    tras = cargar_csv(ARCHIVOS["tras"]).to_dict("records") if not cargar_csv(ARCHIVOS["tras"]).empty else []
    cred = cargar_csv(ARCHIVOS["cred"]).to_dict("records") if not cargar_csv(ARCHIVOS["cred"]).empty else []
    reg_t = cargar_csv(ARCHIVOS["reg_tarjetas"]).to_dict("records") if not cargar_csv(ARCHIVOS["reg_tarjetas"]).empty else []
    
    # Asesores
    df_as = cargar_csv(ARCHIVOS["asesores"])
    asesores_base = [
        {"Asesor": "Edgardo", "Contrasena": "1234"},
        {"Asesor": "Alexandra", "Contrasena": "1234"},
        {"Asesor": "Yeriz", "Contrasena": "1234"},
        {"Asesor": "Alejandro", "Contrasena": "1234"},
        {"Asesor": "P Marca", "Contrasena": "1234"},
        {"Asesor": "A Rutero", "Contrasena": "1234"}
    ]
    if df_as.empty or "Asesor" not in df_as.columns:
        df_as = pd.DataFrame(asesores_base)
        df_as.to_csv(ARCHIVOS["asesores"], index=False)
    else:
        if "Contrasena" not in df_as.columns:
            df_as["Contrasena"] = "1234"
        if "Nombre" in df_as.columns and "Asesor" not in df_as.columns:
            df_as["Asesor"] = df_as["Nombre"]
    asesores_list = df_as.to_dict("records")

    # Marcas (respetando las existentes)
    df_m = cargar_csv(ARCHIVOS["marcas"])
    marcas_base = ["Samsung", "Motorola", "Oppo", "Infinix", "Vivo", "Xiaomi", "Honor", "Tecno", "Realme"]
    if df_m.empty or "Marca" not in df_m.columns:
        df_m = pd.DataFrame(marcas_base, columns=["Marca"])
        df_m.to_csv(ARCHIVOS["marcas"], index=False)
    marcas_list = df_m["Marca"].dropna().unique().tolist()

    return inv, ent, tras, cred, reg_t, asesores_list, marcas_list

def guardar_inv(inv):
    cols = ["Tipo de Tarjeta", "Cantidad Disponible"]
    df = pd.DataFrame(list(inv.items()), columns=cols) if inv else pd.DataFrame(columns=cols)
    df.to_csv(ARCHIVOS["inv"], index=False)

def guardar_lista(clave, lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame()
    df.to_csv(ARCHIVOS[clave], index=False)

def a_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Reporte")
    return out.getvalue()

inventario, entradas, traslados, cred, reg_tarjetas, lista_asesores, MARCAS = cargar_datos()

TIPOS_VENTA = ["Venta en tienda", "Cliente agendado"]
META = 200

st.title("Control Operativo Payjoy")
st.markdown("---")

st.sidebar.markdown("### Menu Principal")
menu = st.sidebar.selectbox(
    "Selecciona opcion",
    [
        "Registrar Venta",
        "Registrar Tarjeta",
        "Dashboard y Cumplimiento",
        "Entregar Tarjeta Pendiente",
        "Stock (Inventario)",
        "Ingresar Lote",
        "Traslado",
        "Historiales",
        "Gestion Asesores"
    ]
)

nombres_asesores_plana = [a["Asesor"] for a in lista_asesores if "Asesor" in a] if lista_asesores else ["Sin Asesor"]

# ---------------------------------------------------------
# 1. REGISTRAR VENTA
# ---------------------------------------------------------
if menu == "Registrar Venta":
    st.header("Registrar Venta Payjoy")
    
    with st.form("form_registro_venta", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente").strip().title()
        marca = st.selectbox("Marca", MARCAS)
        tipo = st.selectbox("Tipo de Venta", TIPOS_VENTA)
        aprobaron_tarjeta = st.selectbox("Le aprobaron tarjeta?", ["Si", "No"])
        
        lleva_t = "No"
        tarj_sel = None
        cant_t = 0
        stock_act = 0
        tag_dispositivo = "N/A"

        if aprobaron_tarjeta == "Si":
            lleva_t = st.selectbox("Lleva Tarjeta Fisica?", ["Si", "No"])
            if lleva_t == "Si":
                if not inventario:
                    st.error("No hay stock disponible de tarjetas.")
                else:
                    tarj_sel = st.selectbox("Tarjeta", list(inventario.keys()))
                    stock_act = inventario[tarj_sel]
                    st.write("Stock actual: " + str(stock_act))
                    cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
                tag_dispositivo = st.text_input("Tag del Dispositivo").strip()

        fecha_v = st.date_input("Fecha", value=obtener_hora().date())
        asesor = st.selectbox("Asesor", nombres_asesores_plana)

        submitted = st.form_submit_button("Registrar Venta", type="primary")
        
        if submitted:
            if not cliente:
                st.warning("Falta el nombre del cliente.")
            elif aprobaron_tarjeta == "Si" and lleva_t == "Si" and not inventario:
                st.error("No hay tarjetas en stock.")
            elif aprobaron_tarjeta == "Si" and lleva_t == "Si" and cant_t > stock_act:
                st.error("Stock insuficiente para la cantidad seleccionada.")
            else:
                if aprobaron_tarjeta == "Si" and lleva_t == "Si" and tarj_sel:
                    inventario[tarj_sel] -= cant_t
                    guardar_inv(inventario)

                cred.append({
                    "Fecha": str(fecha_v),
                    "Cliente": cliente,
                    "Marca de Celular": marca,
                    "Tipo de Venta": tipo,
                    "Aprobaron Tarjeta": aprobaron_tarjeta,
                    "Lleva Tarjeta": lleva_t,
                    "Tarjeta Entregada": tarj_sel if (aprobaron_tarjeta == "Si" and lleva_t == "Si") else "N/A",
                    "Tag Dispositivo": tag_dispositivo if (aprobaron_tarjeta == "Si" and lleva_t == "Si" and tag_dispositivo) else "N/A",
                    "Cantidad": 1,
                    "Asesor": asesor,
                })
                guardar_lista("cred", cred)
                if aprobaron_tarjeta == "Si" and lleva_t == "No":
                    st.success("✅ Venta registrada. Quedo guardada en Pendientes de Entrega.")
                else:
                    st.success("✅ ¡Venta registrada con exito!")

# ---------------------------------------------------------
# 2. REGISTRAR TARJETA (CON FORMULARIO PARA LIMPIARSE)
# ---------------------------------------------------------
elif menu == "Registrar Tarjeta":
    st.header("💳 Registrar Tarjeta a Cliente (Sin Venta Nueva)")
    st.markdown("Use esta sección para registrar una tarjeta física a un cliente que regresa por ella, descontándola del inventario de forma automática.")

    if not inventario:
        st.error("⚠️ No hay inventario de tarjetas disponible en este momento.")
    else:
        # Usamos st.form con clear_on_submit=True para que se limpie al registrar
        with st.form("form_reg_tarjeta_limpiar", clear_on_submit=True):
            cliente_t = st.text_input("Nombre del Cliente").strip().title()
            tag_disp = st.text_input("Tag del Dispositivo").strip()
            
            tarj_elegida = st.selectbox("Tarjeta a Asignar", list(inventario.keys()))
            cant_asig = st.number_input("Cantidad", min_value=1, step=1, value=1)
            fecha_reg = st.date_input("Fecha", value=obtener_hora().date())
            asesor_reg = st.selectbox("Asesor Responsable", nombres_asesores_plana)

            btn_reg_tarj = st.form_submit_button("Registrar y Descontar Tarjeta", type="primary")

            if btn_reg_tarj:
                stock_disp_actual = inventario.get(tarj_elegida, 0)
                if not cliente_t:
                    st.warning("⚠️ Debe ingresar el nombre del cliente.")
                elif not tag_disp:
                    st.warning("⚠️ Debe ingresar el tag del dispositivo.")
                elif cant_asig > stock_disp_actual:
                    st.error(f"⚠️ Stock insuficiente. Solo hay {stock_disp_actual} disponibles.")
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
                    st.success(f"✅ ¡Tarjeta '{tarj_elegida}' registrada y descontada con éxito! Campos limpios.")

        st.markdown("---")
        st.subheader("📋 Historial de Tarjetas Registradas Independientemente")
        if reg_tarjetas:
            df_reg_t = pd.DataFrame(reg_tarjetas)
            st.dataframe(df_reg_t, use_container_width=True)
            st.download_button("📥 Descargar Reporte en Excel", a_excel(df_reg_t), "tarjetas_registradas.xlsx")
        else:
            st.info("No hay registros de tarjetas independientes aún.")

# ---------------------------------------------------------
# 3. DASHBOARD & CUMPLIMIENTO
# ---------------------------------------------------------
elif menu == "Dashboard y Cumplimiento":
    st.header("Dashboard Gerencial")
    ahora = obtener_hora()
    dias_mes = calendar.monthrange(ahora.year, ahora.month)[1]
    df_mes = pd.DataFrame()
    ventas_mes = 0

    if cred:
        df_c = pd.DataFrame(cred)
        if "Fecha" in df_c.columns and "Cantidad" in df_c.columns:
            df_c["_dt"] = pd.to_datetime(df_c["Fecha"], errors="coerce")
            df_mes = df_c[(df_c["_dt"].dt.month == ahora.month) & (df_c["_dt"].dt.year == ahora.year)]
            ventas_mes = int(df_mes["Cantidad"].sum()) if not df_mes.empty else 0

    pct = min(round((ventas_mes / META) * 100, 2), 100.0)
    prom_diario = (ventas_mes / ahora.day) if ahora.day > 0 else 0
    proy = int(prom_diario * dias_mes)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meta", str(META))
    c2.metric("Vendidos", str(ventas_mes))
    c3.metric("Cumplimiento", str(pct) + "%")
    c4.metric("Proyeccion", str(proy))

    st.progress(min(ventas_mes / META, 1.0))
    st.markdown("---")

    if not df_mes.empty and "Marca de Celular" in df_mes.columns:
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Por Asesor")
            df_a = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
            fig1 = px.pie(df_a, names="Asesor", values="Cantidad", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            st.subheader("Por Marca")
            df_m = df_mes.groupby("Marca de Celular")["Cantidad"].sum().reset_index()
            fig2 = px.bar(df_m, x="Marca de Celular", y="Cantidad")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Detalle Asesores")
        t_asesor = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
        t_asesor["% Meta"] = ((t_asesor["Cantidad"] / META) * 100).round(2).astype(str) + "%"
        st.dataframe(t_asesor, use_container_width=True)
    else:
        st.info("Sin registros.")

# ---------------------------------------------------------
# 4. ENTREGAR TARJETA PENDIENTE
# ---------------------------------------------------------
elif menu == "Entregar Tarjeta Pendiente":
    st.header("Entregar Tarjeta Pendiente")
    pendientes = [(i, c) for i, c in enumerate(cred) if c.get("Aprobaron Tarjeta") == "Si" and c.get("Lleva Tarjeta") == "No"]

    if not pendientes:
        st.info("No hay pendientes.")
    elif not inventario:
        st.error("Inventario vacio.")
    else:
        with st.form("f_pend", clear_on_submit=True):
            ops = []
            for i, c in pendientes:
                ops.append("#" + str(i) + " - " + str(c.get('Cliente')))

            elegido = st.selectbox("Pendiente", ops)
            t_ent = st.selectbox("Tarjeta", list(inventario.keys()))
            stock_b = inventario[t_ent]
            st.write("Stock: " + str(stock_b))
            tag_pend = st.text_input("Tag Dispositivo").strip()

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

# ---------------------------------------------------------
# 5. STOCK (INVENTARIO)
# ---------------------------------------------------------
elif menu == "Stock (Inventario)":
    st.header("Stock de Tarjetas")
    if not inventario:
        st.info("Vacio.")
    else:
        df_i = pd.DataFrame(list(inventario.items()), columns=["Tarjeta", "Cantidad"])
        st.dataframe(df_i, use_container_width=True)

# ---------------------------------------------------------
# 6. INGRESAR LOTE
# ---------------------------------------------------------
elif menu == "Ingresar Lote":
    st.header("Ingresar Tarjetas")
    with st.form("f_lote", clear_on_submit=True):
        t_nombre = st.text_input("Nombre").strip().title()
        cant = st.number_input("Cantidad", min_value=1, step=1, value=10)
        f_lleg = st.date_input("Fecha", value=obtener_hora().date())
        resp = st.selectbox("Responsable", nombres_asesores_plana)

        if st.form_submit_button("Guardar"):
            if t_nombre:
                inventario[t_nombre] = inventario.get(t_nombre, 0) + cant
                entradas.append({
                    "Fecha Registro": obtener_hora().strftime("%Y-%m-%d %H:%M"),
                    "Fecha de Llegada": str(f_lleg),
                    "Tarjeta": t_nombre,
                    "Cantidad": cant,
                    "Responsable": resp,
                })
                guardar_inv(inventario)
                guardar_lista("ent", entradas)
                st.success("Ingresado.")
            else:
                st.warning("Falta nombre.")

# ---------------------------------------------------------
# 7. TRASLADO
# ---------------------------------------------------------
elif menu == "Traslado":
    st.header("Traslado")
    with st.form("f_tras", clear_on_submit=True):
        t_sel = st.selectbox("Tarjeta", list(inventario.keys())) if inventario else None
        if not t_sel:
            st.warning("No hay stock para trasladar.")
        else:
            stock_a = inventario[t_sel]
            st.write("Stock: " + str(stock_a))
            cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
            destino = st.text_input("Destino").strip().title()
            resp_s = st.selectbox("Responsable", nombres_asesores_plana)

            if st.form_submit_button("Trasladar"):
                if not destino:
                    st.warning("Indica destino.")
                elif cant_t > stock_a:
                    st.error("Stock insuficiente.")
                else:
                    inventario[t_sel] -= cant_t
                    traslados.append({
                        "Fecha/Hora": obtener_hora().strftime("%Y-%m-%d %H:%M"),
                        "Tarjeta": t_sel,
                        "Cantidad": cant_t,
                        "Destino": destino,
                        "Responsable": resp_s,
                    })
                    guardar_inv(inventario)
                    guardar_lista("tras", traslados)
                    st.success("Traslado exitoso.")

# ---------------------------------------------------------
# 8. HISTORIALES
# ---------------------------------------------------------
elif menu == "Historiales":
    st.header("Historiales")
    sub = st.radio("Ver:", ["Creditos", "Tarjetas Registradas", "Entradas", "Traslados"])
    st.markdown("---")

    if sub == "Creditos":
        df_r = pd.DataFrame(cred) if cred else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "creditos.xlsx")

        if cred:
            st.markdown("---")
            ops = ["#" + str(i) + " - " + str(c.get('Cliente')) for i, c in enumerate(cred)]
            a_borrar = st.selectbox("Anular credito:", ops)
            if st.button("Anular", type="primary"):
                idx = int(a_borrar.split("#")[1].split(" ")[0])
                item = cred.pop(idx)
                if item.get("Lleva Tarjeta") == "Si" and item.get("Tarjeta Entregada") != "N/A":
                    t = item.get("Tarjeta Entregada")
                    inventario[t] = inventario.get(t, 0) + 1
                    guardar_inv(inventario)
                guardar_lista("cred", cred)
                st.success("Anulado.")
                st.rerun()

    elif sub == "Tarjetas Registradas":
        df_r = pd.DataFrame(reg_tarjetas) if reg_tarjetas else pd.DataFrame()
        st.dataframe(df_r, use_container_width=True)
        if not df_r.empty:
            st.download_button("Excel", a_excel(df_r), "tarjetas_registradas.xlsx")

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

# ---------------------------------------------------------
# 9. GESTIÓN ASESORES Y MARCAS (PROTEGIDO)
# ---------------------------------------------------------
elif menu == "Gestion Asesores":
    st.header("Gestion de Asesores y Marcas")
    
    st.markdown("---")
    st.subheader("🔐 Acceso Restringido")
    pass_ingresada = st.text_input("Ingrese Contraseña de Administrador", type="password")
    
    if pass_ingresada == ADMIN_PASS:
        st.success("Contraseña Correcta. Acceso Concedido.")
        
        tab1, tab2 = st.tabs(["👥 Gestion de Asesores", "📱 Gestion de Marcas"])
        
        with tab1:
            with st.form("form_nuevo_asesor", clear_on_submit=True):
                st.subheader("Crear Asesor")
                nuevo_nombre = st.text_input("Nombre Asesor").strip().title()
                nueva_pass = st.text_input("Contrasena", type="password").strip()

                if st.form_submit_button("Crear"):
                    if not nuevo_nombre or not nueva_pass:
                        st.error("Campos obligatorios.")
                    elif any(str(a.get("Asesor")) == nuevo_nombre for a
