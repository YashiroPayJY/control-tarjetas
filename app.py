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
    "users": "usuarios.csv",
    "asesores": "asesores_control.csv",
}

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
    
    df_u = cargar_csv(ARCHIVOS["users"])
    if df_u.empty or "Usuario" not in df_u.columns:
        df_u = pd.DataFrame([{"Usuario": "Administrador", "Contrasena": "admin123", "Rol": "Admin"}])
        df_u.to_csv(ARCHIVOS["users"], index=False)
    usuarios_list = df_u.to_dict("records")

    df_as = cargar_csv(ARCHIVOS["asesores"])
    asesores_base = [
        {"Asesor": "Edgardo", "Rol": "Estandar", "Contrasena": "1234"},
        {"Asesor": "Alexandra", "Rol": "Estandar", "Contrasena": "1234"},
        {"Asesor": "Yeriz", "Rol": "Estandar", "Contrasena": "1234"},
        {"Asesor": "Alejandro", "Rol": "Estandar", "Contrasena": "1234"},
        {"Asesor": "P Marca", "Rol": "Estandar", "Contrasena": "1234"},
        {"Asesor": "A Rutero", "Rol": "Estandar", "Contrasena": "1234"}
    ]

    if df_as.empty or "Asesor" not in df_as.columns:
        df_as = pd.DataFrame(asesores_base)
        df_as.to_csv(ARCHIVOS["asesores"], index=False)
    else:
        if "Rol" not in df_as.columns:
            df_as["Rol"] = "Estandar"
        if "Contrasena" not in df_as.columns:
            df_as["Contrasena"] = "1234"
        if "Nombre" in df_as.columns and "Asesor" not in df_as.columns:
            df_as["Asesor"] = df_as["Nombre"]

    asesores_list = df_as.to_dict("records")

    for a in asesores_list:
        nombre_a = a.get("Asesor")
        pass_a = str(a.get("Contrasena", "1234"))
        rol_a = a.get("Rol", "Estandar")
        if nombre_a and not any(u.get("Usuario") == nombre_a for u in usuarios_list):
            usuarios_list.append({"Usuario": nombre_a, "Contrasena": pass_a, "Rol": rol_a})
        else:
            for u in usuarios_list:
                if u.get("Usuario") == nombre_a:
                    u["Contrasena"] = pass_a
                    u["Rol"] = rol_a

    pd.DataFrame(usuarios_list).to_csv(ARCHIVOS["users"], index=False)
    return inv, ent, tras, cred, usuarios_list, asesores_list

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

inventario, entradas, traslados, cred, lista_usuarios, lista_asesores = cargar_datos()

TIPOS_VENTA = ["Venta en tienda", "Cliente agendado"]
MARCAS = ["Samsung", "Motorola", "Oppo", "Infinix", "Vivo", "Xiaomi", "Honor", "Tecno", "Realme"]
META = 200

st.title("Control Operativo Payjoy")
st.markdown("---")

st.sidebar.markdown("### Menu Principal")
menu = st.sidebar.selectbox(
    "Selecciona opcion",
    [
        "Registrar Venta",
        "Dashboard y Cumplimiento",
        "Entregar Tarjeta Pendiente",
        "Stock (Inventario)",
        "Ingresar Lote",
        "Traslado",
        "Historiales",
        "Gestion Asesores"
    ]
)

menus_protegidos = [
    "Dashboard y Cumplimiento",
    "Entregar Tarjeta Pendiente",
    "Stock (Inventario)",
    "Ingresar Lote",
    "Traslado",
    "Historiales",
    "Gestion Asesores"
]

sesion_activa = False
rol_actual = None

if menu in menus_protegidos:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Autenticacion")
    
    if not lista_usuarios:
        lista_usuarios = [{"Usuario": "Administrador", "Contrasena": "admin123", "Rol": "Admin"}]

    nombres_u = [u["Usuario"] for u in lista_usuarios]
    user_sel = st.sidebar.selectbox("Usuario", nombres_u)
    pass_ingresada = st.sidebar.text_input("Contrasena", type="password")

    if st.sidebar.button("Ingresar"):
        user_obj = next((u for u in lista_usuarios if u["Usuario"] == user_sel), None)
        if user_obj and user_obj["Contrasena"] == pass_ingresada:
            st.session_state["usuario_actual"] = user_obj["Usuario"]
            st.session_state["rol_actual"] = user_obj["Rol"]
            st.sidebar.success("Bienvenido")
            st.rerun()
        else:
            st.sidebar.error("Error")

if "usuario_actual" in st.session_state:
    sesion_activa = True
    rol_actual = st.session_state["rol_actual"]
    st.sidebar.markdown("---")
    st.sidebar.info("Activo: " + st.session_state["usuario_actual"] + " | Rol: " + rol_actual)
    if st.sidebar.button("Salir"):
        del st.session_state["usuario_actual"]
        del st.session_state["rol_actual"]
        st.rerun()

nombres_asesores_plana = [a["Asesor"] for a in lista_asesores if "Asesor" in a] if lista_asesores else ["Sin Asesor"]

if menu == "Registrar Venta":
    st.header("Registrar Venta Payjoy")
    
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
                st.error("No hay stock.")
            else:
                tarj_sel = st.selectbox("Tarjeta", list(inventario.keys()))
                stock_act = inventario[tarj_sel]
                st.write("Stock: " + str(stock_act))
                cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
            tag_dispositivo = st.text_input("Tag del Dispositivo").strip()

    fecha_v = st.date_input("Fecha", value=obtener_hora().date())
    asesor = st.selectbox("Asesor", nombres_asesores_plana)

    if st.button("Registrar", type="primary"):
        if not cliente:
            st.warning("Falta el cliente.")
        elif aprobaron_tarjeta == "Si" and lleva_t == "Si" and cant_t > stock_act:
            st.error("Stock insuficiente.")
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
                st.success("Guardado en Pendientes.")
            else:
                st.success("Registrado con exito.")
            st.rerun()

elif menu == "Dashboard y Cumplimiento":
    st.header("Dashboard Gerencial")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
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
            st.info("Sin registros este mes.")

elif menu == "Entregar Tarjeta Pendiente":
    st.header("Entregar Tarjeta Pendiente")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
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

elif menu == "Stock (Inventario)":
    st.header("Stock de Tarjetas")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
        if not inventario:
            st.info("Vacio.")
        else:
            df_i = pd.DataFrame(list(inventario.items()), columns=["Tarjeta", "Cantidad"])
            st.dataframe(df_i, use_container_width=True)

elif menu == "Ingresar Lote":
    st.header("Ingresar Tarjetas")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
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

elif menu == "Traslado":
    st.header("Traslado")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
        with st.form("f_tras", clear_on_submit=True):
            t_sel = st.selectbox("Tarjeta", list(inventario.keys()))
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

elif menu == "Historiales":
    st.header("Historiales")
    if not sesion_activa:
        st.warning("Inicia sesion.")
    else:
        sub = st.radio("Ver:", ["Creditos", "Entradas", "Traslados"])
        st.markdown("---")

        if sub == "Creditos":
            df_r = pd.DataFrame(cred) if cred else pd.DataFrame()
            st.dataframe(df_r, use_container_width=True)
            if not df_r.empty:
                st.download_button("Excel", a_excel(df_r), "creditos.xlsx")

            if rol_actual == "Admin" and cred:
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

elif menu == "Gestion Asesores":
    st.header("Gestion Asesores y Accesos")
    
    if not sesion_activa or rol_actual != "Admin":
        st.error("Acceso exclusivo para Administradores.")
    else:
        st.success("Admin Activo")
        
        with st.form("form_nuevo_asesor_user", clear_on_submit=True):
            st.subheader("Crear Asesor")
            nuevo_nombre = st.text_input("Nombre Usuario").strip().title()
            nueva_pass = st.text_input("Contrasena", type="password").strip()
            nuevo_rol = st.selectbox("Rol", ["Estandar", "Admin"])

            if st.form_submit_button("Crear"):
                if not nuevo_nombre or not nueva_pass:
                    st.error("Campos obligatorios.")
                elif any(str(a.get("Asesor")) == nuevo_nombre for a in lista_asesores):
                    st.warning("Ya existe.")
                else:
                    lista_asesores.append({"Asesor": nuevo_nombre, "Rol": nuevo_rol, "Contrasena": nueva_pass})
                    guardar_lista("asesores", lista_asesores)

                    if not any(u.get("Usuario") == nuevo_nombre for u in lista_usuarios):
                        lista_usuarios.append({"Usuario": nuevo_nombre, "Contrasena": nueva_pass, "Rol": nuevo_rol})
                    else:
                        for u in lista_usuarios:
                            if u.get("Usuario") == nuevo_nombre:
                                u["Contrasena"] = nueva_pass
                                u["Rol"] = nuevo_rol
                    guardar_lista("users", lista_usuarios)

                    st.success("Creado con exito.")
                    st.rerun()

        st.markdown("---")
        st.subheader("Lista de Accesos (Contraseñas y Roles)")
        if lista_asesores:
            df_temp = pd.DataFrame(lista_asesores)
            cols_mostrar = [c for c in ["Asesor", "Rol", "Contrasena"] if c in df_temp.columns]
            st.dataframe(df_temp[cols_mostrar], use_container_width=True)

            nombres_borrar = [str(a.get("Asesor")) for a in lista_asesores if a.get("Asesor") != "Administrador" and "Asesor" in a]
            if nombres_borrar:
                st.markdown("---")
                st.subheader("Eliminar o Recrear Asesor (Para cambiar contraseña)")
                asesor_a_borrar = st.selectbox("Seleccionar", nombres_borrar)
                if st.button("Eliminar Asesor Seleccionado", type="primary"):
                    lista_asesores = [a for a in lista_asesores if str(a.get("Asesor")) != asesor_a_borrar]
                    guardar_lista("asesores", lista_asesores)

                    lista_usuarios = [u for u in lista_usuarios if str(u.get("Usuario")) != asesor_a_borrar]
                    guardar_lista("users", lista_usuarios)

                    st.success("Eliminado. Ahora puedes volver a crearlo arriba con su nueva contraseña.")
                    st.rerun()
            else:
                st.info("No hay asesores adicionales para eliminar.")
        else:
            st.info("Sin 
