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

  ent = (
      cargar_csv(ARCHIVOS["ent"]).to_dict("records")
      if not cargar_csv(ARCHIVOS["ent"]).empty
      else []
  )
  tras = (
      cargar_csv(ARCHIVOS["tras"]).to_dict("records")
      if not cargar_csv(ARCHIVOS["tras"]).empty
      else []
  )
  cred = (
      cargar_csv(ARCHIVOS["cred"]).to_dict("records")
      if not cargar_csv(ARCHIVOS["cred"]).empty
      else []
  )
  
  df_u = cargar_csv(ARCHIVOS["users"])
  if df_u.empty:
    df_u = pd.DataFrame([{
        "Usuario": "Administrador",
        "Contrasena": "admin123",
        "Rol": "Admin"
    }])
    df_u.to_csv(ARCHIVOS["users"], index=False)
  usuarios_list = df_u.to_dict("records")

  df_as = cargar_csv(ARCHIVOS["asesores"])
  if df_as.empty:
    asesores_base = [
        {"Asesor": "Edgardo", "Rol": "Estándar", "Contrasena": "1234"},
        {"Asesor": "Alexandra", "Rol": "Estándar", "Contrasena": "1234"},
        {"Asesor": "Yeriz", "Rol": "Estándar", "Contrasena": "1234"},
        {"Asesor": "Alejandro", "Rol": "Estándar", "Contrasena": "1234"},
        {"Asesor": "P Marca", "Rol": "Estándar", "Contrasena": "1234"},
        {"Asesor": "A Rutero", "Rol": "Estándar", "Contrasena": "1234"}
    ]
    df_as = pd.DataFrame(asesores_base)
    df_as.to_csv(ARCHIVOS["asesores"], index=False)
    for a in asesores_base:
      if not any(u["Usuario"] == a["Asesor"] for u in usuarios_list):
        usuarios_list.append({"Usuario": a["Asesor"], "Contrasena": a["Contrasena"], "Rol": a["Rol"]})
    pd.DataFrame(usuarios_list).to_csv(ARCHIVOS["users"], index=False)
  
  asesores_list = df_as.to_dict("records")
  return inv, ent, tras, cred, usuarios_list, asesores_list


def guardar_inv(inv):
  cols = ["Tipo de Tarjeta", "Cantidad Disponible"]
  df = (
      pd.DataFrame(list(inv.items()), columns=cols)
      if inv
      else pd.DataFrame(columns=cols)
  )
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
MARCAS = [
    "Samsung",
    "Motorola",
    "Oppo",
    "Infinix",
    "Vivo",
    "Xiaomi",
    "Honor",
    "Tecno",
    "Realme",
]
META = 200

st.title("📱 Control Operativo Payjoy")
st.markdown("---")

st.sidebar.markdown("### 📱 Menú Principal")
menu = st.sidebar.selectbox(
    "Selecciona una opción",
    [
        "📱 Registrar Venta",
        "📊 Dashboard & Cumplimiento",
        "💳 Entregar Tarjeta Pendiente",
        "📦 Stock (Inventario)",
        "➕ Ingresar Lote",
        "🚚 Traslado",
        "📂 Historiales",
        "👥 Gestión de Asesores y Accesos (Admin)",
    ],
)

menus_protegidos = [
    "📊 Dashboard & Cumplimiento",
    "💳 Entregar Tarjeta Pendiente",
    "📦 Stock (Inventario)",
    "➕ Ingresar Lote",
    "🚚 Traslado",
    "📂 Historiales",
    "👥 Gestión de Asesores y Accesos (Admin)",
]

sesion_activa = False
rol_actual = None

if menu in menus_protegidos:
  st.sidebar.markdown("---")
  st.sidebar.markdown("### 🔐 Autenticación de Usuario")
  
  if not lista_usuarios:
    lista_usuarios = [{"Usuario": "Administrador", "Contrasena": "admin123", "Rol": "Admin"}]

  nombres_u = [u["Usuario"] for u in lista_usuarios]
  user_sel = st.sidebar.selectbox("Selecciona tu Usuario", nombres_u)
  pass_ingresada = st.sidebar.text_input("Contraseña", type="password")

  if st.sidebar.button("🔓 Iniciar Sesión"):
    user_obj = next((u for u in lista_usuarios if u["Usuario"] == user_sel), None)
    if user_obj and user_obj["Contrasena"] == pass_ingresada:
      st.session_state["usuario_actual"] = user_obj["Usuario"]
      st.session_state["rol_actual"] = user_obj["Rol"]
      st.sidebar.success(f"¡Bienvenido {user_obj['Usuario']}!")
      st.rerun()
    else:
      st.sidebar.error("Contraseña incorrecta.")

if "usuario_actual" in st.session_state:
  sesion_activa = True
  rol_actual = st.session_state["rol_actual"]
  st.sidebar.markdown("---")
  st.sidebar.info(f"👤 Activo: **{st.session_state['usuario_actual']}**\n\n📌 Rol: **{rol_actual}**")
  if st.sidebar.button("🔒 Cerrar Sesión"):
    del st.session_state["usuario_actual"]
    del st.session_state["rol_actual"]
    st.rerun()

nombres_asesores_plana = [a["Asesor"] for a in lista_asesores] if lista_asesores else ["Sin Asesor"]

if menu == "📱 Registrar Venta":
  st.header("📱 Registrar Venta Payjoy")
  
  cliente = st.text_input("Nombre del Cliente").strip().title()
  marca = st.selectbox("Marca", MARCAS)
  tipo = st.selectbox("Tipo de Venta", TIPOS_VENTA)
  
  aprobaron_tarjeta = st.selectbox("¿Le aprobaron tarjeta?", ["Sí", "No"])
  
  lleva_t = "No"
  tarj_sel = None
  cant_t = 0
  stock_act = 0
  tag_dispositivo = "N/A"

  if aprobaron_tarjeta == "Sí":
    lleva_t = st.selectbox("¿Lleva Tarjeta Física?", ["Sí", "No"])
    if lleva_t == "Sí":
      if not inventario:
        st.error("No hay tarjetas en stock.")
      else:
        tarj_sel = st.selectbox("Tarjeta a Entregar", list(inventario.keys()))
        stock_act = inventario[tarj_sel]
        st.write(f"Stock actual: **{stock_act}**")
        cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
      
      tag_dispositivo = st.text_input("Tag del Dispositivo").strip()

  fecha_v = st.date_input("Fecha", value=obtener_hora().date())
  asesor = st.selectbox("Asesor", nombres_asesores_plana)

  if st.button("Registrar Venta", type="primary"):
    if not cliente:
      st.warning("⚠️ Falta el nombre del cliente.")
    elif aprobaron_tarjeta == "Sí" and lleva_t == "Sí" and cant_t > stock_act:
      st.error("⚠️ Stock insuficiente para la cantidad seleccionada.")
    else:
      if aprobaron_tarjeta == "Sí" and lleva_t == "Sí" and tarj_sel:
        inventario[tarj_sel] -= cant_t
        guardar_inv(inventario)

      cred.append({
          "Fecha": str(fecha_v),
          "Cliente": cliente,
          "Marca de Celular": marca,
          "Tipo de Venta": tipo,
          "¿Aprobaron Tarjeta?": aprobaron_tarjeta,
          "¿Lleva Tarjeta?": lleva_t,
          "Tarjeta Entregada": tarj_sel if (aprobaron_tarjeta == "Sí" and lleva_t == "Sí") else "N/A",
          "Tag Dispositivo": tag_dispositivo if (aprobaron_tarjeta == "Sí" and lleva_t == "Sí" and tag_dispositivo) else "N/A",
          "Cantidad": 1,
          "Asesor": asesor,
      })
      guardar_lista("cred", cred)
      if aprobaron_tarjeta == "Sí" and lleva_t == "No":
        st.success("✅ ¡Venta registrada! Como no llevó tarjeta física, quedó guardada en Pendientes de Entrega.")
      else:
        st.success("✅ ¡Venta registrada con éxito!")
      st.rerun()

elif menu == "📊 Dashboard & Cumplimiento":
  st.header("📈 Dashboard Gerencial")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    ahora = obtener_hora()
    dias_mes = calendar.monthrange(ahora.year, ahora.month)[1]
    df_mes = pd.DataFrame()
    ventas_mes = 0

    if cred:
      df_c = pd.DataFrame(cred)
      if "Fecha" in df_c.columns and "Cantidad" in df_c.columns:
        df_c["_dt"] = pd.to_datetime(df_c["Fecha"], errors="coerce")
        df_mes = df_c[
            (df_c["_dt"].dt.month == ahora.month)
            & (df_c["_dt"].dt.year == ahora.year)
        ]
        ventas_mes = int(df_mes["Cantidad"].sum()) if not df_mes.empty else 0

    pct = min(round((ventas_mes / META) * 100, 2), 100.0)
    prom_diario = (ventas_mes / ahora.day) if ahora.day > 0 else 0
    proy = int(prom_diario * dias_mes)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 Meta", f"{META}")
    c2.metric("✅ Vendidos", f"{ventas_mes}")
    c3.metric("📊 Cumplimiento", f"{pct}%")
    c4.metric("🔮 Proyección", f"{proy}")

    st.progress(min(ventas_mes / META, 1.0))
    st.markdown("---")

    if not df_mes.empty and "Marca de Celular" in df_mes.columns:
      g1, g2 = st.columns(2)
      with g1:
        st.subheader("🥧 Por Asesor")
        df_a = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
        fig1 = px.pie(df_a, names="Asesor", values="Cantidad", hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
      with g2:
        st.subheader("📱 Por Marca")
        df_m = df_mes.groupby("Marca de Celular")["Cantidad"].sum().reset_index()
        fig2 = px.bar(df_m, x="Marca de Celular", y="Cantidad")
        st.plotly_chart(fig2, use_container_width=True)

      st.subheader("🏆 Detalle Asesores")
      t_asesor = df_mes.groupby("Asesor")["Cantidad"].sum().reset_index()
      t_asesor["% Meta"] = (
          (t_asesor["Cantidad"] / META) * 100
      ).round(2).astype(str) + "%"
      st.dataframe(t_asesor, use_container_width=True)
    else:
      st.info("Sin registros este mes.")

elif menu == "💳 Entregar Tarjeta Pendiente":
  st.header("💳 Entregar Tarjeta Pendiente")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    pendientes = [
        (i, c) for i, c in enumerate(cred) if c.get("¿Aprobaron Tarjeta?") == "Sí" and c.get("¿Lleva Tarjeta?") == "No"
    ]

    if not pendientes:
      st.info("No hay créditos pendientes de tarjeta física.")
    elif not inventario:
      st.error("No hay stock en inventario.")
    else:
      with st.form("f_pend", clear_on_submit=True):
        ops = []
        for i, c in pendientes:
          ops.append(
              f"#{i} - Cliente: {c.get('Cliente')} - Asesor: {c.get('Asesor')}"
          )

        elegido = st.selectbox("Crédito Pendiente", ops)
        t_ent = st.selectbox("Tarjeta a Asignar", list(inventario.keys()))
        stock_b = inventario[t_ent]
        st.write(f"Stock disponible: **{stock_b}**")
        tag_pend = st.text_input("Tag del Dispositivo").strip()

        if st.form_submit_button("Confirmar Entrega"):
          if stock_b < 1:
            st.error("Stock insuficiente.")
          else:
            idx = int(elegido.split("#")[1].split(" -")[0])
            inventario[t_ent] -= 1
            guardar_inv(inventario)
            cred[idx]["¿Lleva Tarjeta?"] = "Sí"
            cred[idx]["Tarjeta Entregada"] = t_ent
            if tag_pend:
              cred[idx]["Tag Dispositivo"] = tag_pend
            guardar_lista("cred", cred)
            st.success("¡Tarjeta entregada con éxito!")
            st.rerun()

elif menu == "📦 Stock (Inventario)":
  st.header("📦 Stock de Tarjetas")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    if not inventario:
      st.info("Inventario vacío.")
    else:
      df_i = pd.DataFrame(
          list(inventario.items()), columns=["Tarjeta", "Cantidad"]
      )
      st.dataframe(df_i, use_container_width=True)

elif menu == "➕ Ingresar Lote":
  st.header("➕ Ingresar Tarjetas")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    with st.form("f_lote", clear_on_submit=True):
      t_nombre = st.text_input("Nombre de Tarjeta").strip().title()
      cant = st.number_input("Cantidad", min_value=1, step=1, value=10)
      f_lleg = st.date_input("Fecha de Llegada", value=obtener_hora().date())
      resp = st.selectbox("Responsable", nombres_asesores_plana)

      if st.form_submit_button("Guardar Lote"):
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
          st.success("¡Lote ingresado correctamente!")
        else:
          st.warning("Falta el nombre de la tarjeta.")

elif menu == "🚚 Traslado":
  st.header("🚚 Traslado a Sucursales")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    if not inventario:
      st.warning("No hay stock para trasladar.")
    else:
      with st.form("f_tras", clear_on_submit=True):
        t_sel = st.selectbox("Tarjeta", list(inventario.keys()))
        stock_a = inventario[t_sel]
        st.write(f"Stock actual: **{stock_a}**")
        cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
        destino = st.text_input("Destino").strip().title()
        resp_s = st.selectbox("Responsable", nombres_asesores_plana)

        if st.form_submit_button("Trasladar"):
          if not destino:
            st.warning("Indica el destino.")
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
            st.success("¡Traslado exitoso!")

elif menu == "📂 Historiales":
  st.header("📂 Reportes y Exportación")
  if not sesion_activa:
    st.warning("🔒 Por favor, inicia sesión en la barra lateral con tu usuario y contraseña.")
  else:
    sub = st.radio("Ver:", ["Créditos", "Entradas", "Traslados"])
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
      f_txt = st.text_input("Buscar texto:").lower()
    with col2:
      activar_f = st.checkbox("Filtrar por fechas")

    f_ini, f_fin = None, None
    if activar_f:
      c1, c2 = st.columns(2)
      with c1:
        f_ini = st.date_input("Inicio", obtener_hora().date())
      with c2:
        f_fin = st.date_input("Fin", obtener_hora().date())


    def procesar_df(lista, col_fecha):
      if not lista:
        return pd.DataFrame()
      df = pd.DataFrame(lista)
      if f_txt:
        mask = df.astype(str).apply(
            lambda x: x.str.lower().str.contains(f_txt).any(), axis=1
        )
        df = df[mask]
      if activar_f and col_fecha in df.columns:
        df["_t"] = pd.to_datetime(df[col_fecha]).dt.date
        df = df[(df["_t"] >= f_ini) & (df["_t"] <= f_fin)].drop(columns=["_t"])
      return df


    if sub == "Créditos":
      df_r = procesar_df(cred, "Fecha")
      st.dataframe(df_r, use_container_width=True)
      if not df_r.empty:
        st.download_button("📥 Descargar Reporte Excel", a_excel(df_r), "creditos.xlsx")

      st.markdown("---")
      st.subheader("⚙️ Anulación / Reversión de Créditos Mal Gestionados")
      if rol_actual != "Admin":
        st.warning("⚠️ Solo los usuarios con rol **Admin** pueden anular o revertir créditos.")
      elif cred:
        ops = [f"#{i} - Cliente: {c.get('Cliente')} - Fecha: {c.get('Fecha')}" for i, c in enumerate(cred)]
        a_borrar = st.selectbox("Seleccione el crédito a anular:", ops)
        if st.button("🗑️ Anular / Revertir Crédito", type="primary"):
          idx = int(a_borrar.split("#")[1].split(" -")[0])
          item = cred.pop(idx)
          if (
              item.get("¿Lleva Tarjeta?") == "Sí"
              and item.get("Tarjeta Entregada") != "N/A"
          ):
            t = item.get("Tarjeta Entregada")
            inventario[t] = inventario.get(t, 0) + 1
            guardar_inv(inventario)
          guardar_lista("cred", cred)
          st.success("✅ Crédito anulado correctamente y stock devuelto (si aplica).")
          st.rerun()

    elif sub == "Entradas":
      df_r = procesar_df(entradas, "Fecha de Llegada")
      st.dataframe(df_r, use_container_width=True)
      if not df_r.empty:
        st.download_button("📥 Descargar Reporte Excel", a_excel(df_r), "entradas.xlsx")

    elif sub == "Traslados":
      df_r = procesar_df(traslados, "Fecha/Hora")
      st.dataframe(df_r, use_container_width=True)
      if not df_r.empty:
        st.download_button("📥 Descargar Reporte Excel", a_excel(df_r), "traslados.xlsx")

elif menu == "👥 Gestión de Asesores y Accesos (Admin)":
  st.header("👥 Gestión Unificada de Asesores y Contraseñas")
  
  if not sesion_activa:
    st.warning("🔒 Inicia sesión en la barra lateral con tu cuenta de **Administrador** (Ej: Administrador / admin123) para gestionar los accesos.")
    st.markdown("---")
    st.subheader("📋 Asesores Registrados en el Sistema")
    if lista_asesores:
      df_as_view = pd.DataFrame(lista_asesores)[["Asesor", "Rol"]]
      st.dataframe(df_as_view, use_container_width=True)
  elif rol_actual != "Admin":
    st.error("⛔ Tu usuario actual es Estándar. Acceso restringido exclusivamente para administradores.")
  else:
    st.success("✅ Modo Administrador Activo. Al registrar un nuevo asesor, este quedará creado automáticamente en el sistema con su contraseña de acceso.")
    
    with st.form("form_nuevo_asesor_user", clear_on_submit=True):
      nuevo_nombre = st.text_input("Nombre del Asesor (Nombre de Usuario)").strip().title()
      nueva_pass = st.text_input("Contraseña Asignada", type="password").strip()
      nuevo_rol = st.selectbox("Rol en el Sistema", ["Estándar", "Admin"])

      if st.form_submit_button("➕ Registrar Asesor y Acceso"):
        if not nuevo_nombre or not nueva_pass:
          st.error("El nombre y la contraseña son obligatorios.")
        elif any(a["Asesor"] == nuevo_nombre for a in lista_asesores):
          st.warning("Ya existe un asesor/usuario con este nombre.")
        else:
          lista_asesores.append({
              "Asesor": nuevo_nombre,
              "Rol": nuevo_rol,
              "Contrasena": nueva_pass
          })
          guardar_lista("asesores", lista_asesores)

          if not any(u["Usuario"] == nuevo_nombre for u in lista_usuarios):
            lista_usuarios.append({
                "Usuario": nuevo_nombre,
                "Contrasena": nueva_pass,
                "Rol": nuevo_rol
            })
          else:
            for u in lista_usuarios:
              if u["Usuario"] == nuevo_nombre:
                u["Contrasena"] = nueva_pass
                u["Rol"] = nuevo_rol
          guardar_lista("users", lista_usuarios)

          st.success(f"¡Asesor y usuario '{nuevo_nombre}' creado con éxito!")
          st.rerun()

    st.markdown("---")
    st.subheader("📋 Listado de Asesores y Roles Actuales")
    if lista_asesores:
      df_view_asesores = pd.DataFrame(lista_asesores)[["Asesor", "Rol"]]
      st.dataframe(df_view_asesores, use_container_width=True)

      nombres_borrar = [a["Asesor"] for a in lista_asesores if a["Asesor"] != "Administrador"]
      if nombres_borrar:
        asesor_a_borrar = st.selectbox("Selecc
