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
  return inv, ent, tras, cred


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


inventario, entradas, traslados, creditos = cargar_datos()

ASESORES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro", "P Marca", "A Rutero"]
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

st.sidebar.markdown("### 🔐 Panel de Control")
pass_admin = st.sidebar.text_input("Contraseña Admin", type="password")
es_admin = pass_admin == "admin123"

if es_admin:
  st.sidebar.success("Admin Activo 🔓")
elif pass_admin:
  st.sidebar.error("Contraseña incorrecta")

st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Menú Principal",
    [
        "📊 Dashboard & Cumplimiento",
        "📱 Registrar Venta",
        "💳 Entregar Tarjeta Pendiente",
        "📦 Stock (Inventario)",
        "➕ Ingresar Lote",
        "🚚 Traslado",
        "📂 Historiales",
    ],
)

if menu == "📊 Dashboard & Cumplimiento":
  st.header("📈 Dashboard Gerencial")
  ahora = obtener_hora()
  dias_mes = calendar.monthrange(ahora.year, ahora.month)[1]
  df_mes = pd.DataFrame()
  ventas_mes = 0

  if creditos:
    df_c = pd.DataFrame(creditos)
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

elif menu == "📱 Registrar Venta":
  st.header("📱 Registrar Venta Payjoy")
  with st.form("f_venta", clear_on_submit=True):
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
          st.write(f"Stock: **{stock_act}**")
          cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
        
        tag_dispositivo = st.text_input("Tag del Dispositivo").strip()

    fecha_v = st.date_input("Fecha", value=obtener_hora().date())
    asesor = st.selectbox("Asesor", ASESORES)

    if st.form_submit_button("Registrar"):
      if not cliente:
        st.warning("Falta el nombre del cliente.")
      elif aprobaron_tarjeta == "Sí" and lleva_t == "Sí" and cant_t > stock_act:
        st.error("Stock insuficiente.")
      else:
        if aprobaron_tarjeta == "Sí" and lleva_t == "Sí" and tarj_sel:
          inventario[tarj_sel] -= cant_t
          guardar_inv(inventario)

        creditos.append({
            "Fecha": str(fecha_v),
            "Cliente": cliente,
            "Marca de Celular": marca,
            "Tipo de Venta": tipo,
            "¿Aprobaron Tarjeta?": aprobaron_tarjeta,
            "¿Lleva Tarjeta?": lleva_t,
            "Tarjeta Entregada": tarj_sel if (aprobaron_tarjeta == "Sí" and lleva_t == "Sí") else "N/A",
            "Tag Dispositivo": tag_dispositivo if (aprobaron_tarjeta == "Sí" and lleva_t == "Sí") else "N/A",
            "Cantidad": 1,
            "Asesor": asesor,
        })
        guardar_lista("cred", creditos)
        st.success("¡Registrado con éxito! El formulario está listo para otro.")

elif menu == "💳 Entregar Tarjeta Pendiente":
  st.header("💳 Entregar Tarjeta Pendiente")
  pendientes = [
      (i, c) for i, c in enumerate(creditos) if c.get("¿Aprobaron Tarjeta?") == "Sí" and c.get("¿Lleva Tarjeta?") == "No"
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
            f"#{i} - {c.get('Cliente')} - {c.get('Marca de Celular')}"
        )

      elegido = st.selectbox("Crédito", ops)
      t_ent = st.selectbox("Tarjeta", list(inventario.keys()))
      stock_b = inventario[t_ent]
      st.write(f"Stock: **{stock_b}**")
      tag_pend = st.text_input("Tag del Dispositivo").strip()

      if st.form_submit_button("Confirmar Entrega"):
        if stock_b < 1:
          st.error("Stock insuficiente.")
        else:
          idx = int(elegido.split("#")[1].split(" -")[0])
          inventario[t_ent] -= 1
          guardar_inv(inventario)
          creditos[idx]["¿Lleva Tarjeta?"] = "Sí"
          creditos[idx]["Tarjeta Entregada"] = t_ent
          if tag_pend:
            creditos[idx]["Tag Dispositivo"] = tag_pend
          guardar_lista("cred", creditos)
          st.success("¡Tarjeta entregada!")
          st.rerun()

elif menu == "📦 Stock (Inventario)":
  st.header("📦 Stock de Tarjetas")
  if not inventario:
    st.info("Inventario vacío.")
  else:
    df_i = pd.DataFrame(
        list(inventario.items()), columns=["Tarjeta", "Cantidad"]
    )
    st.dataframe(df_i, use_container_width=True)

elif menu == "➕ Ingresar Lote":
  st.header("➕ Ingresar Tarjetas")
  with st.form("f_lote", clear_on_submit=True):
    t_nombre = st.text_input("Nombre de Tarjeta").strip().title()
    cant = st.number_input("Cantidad", min_value=1, step=1, value=10)
    f_lleg = st.date_input("Fecha de Llegada", value=obtener_hora().date())
    resp = st.selectbox("Responsable", ASESORES)

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
        st.success("¡Lote ingresado!")
      else:
        st.warning("Falta el nombre.")

elif menu == "🚚 Traslado":
  st.header("🚚 Traslado a Sucursales")
  if not inventario:
    st.warning("No hay stock para trasladar.")
  else:
    with st.form("f_tras", clear_on_submit=True):
      t_sel = st.selectbox("Tarjeta", list(inventario.keys()))
      stock_a = inventario[t_sel]
      st.write(f"Stock actual: **{stock_a}**")
      cant_t = st.number_input("Cantidad", min_value=1, step=1, value=1)
      destino = st.text_input("Destino").strip().title()
      resp_s = st.selectbox("Responsable", ASESORES)

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
          st.success("¡Traslado exitoso!")

elif menu == "📂 Historiales":
  st.header("📂 Reportes y Exportación")
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
    df_r = procesar_df(creditos, "Fecha")
    st.dataframe(df_r, use_container_width=True)
    if not df_r.empty:
      st.download_button("📥 Excel", a_excel(df_r), "creditos.xlsx")

    st.markdown("---")
    st.subheader("⚙️ Anular Créditos")
    if not es_admin:
      st.warning("Requiere Admin.")
    elif creditos:
      ops = [f"#{i} - {c.get('Cliente')}" for i, c in enumerate(creditos)]
      a_borrar = st.selectbox("Crédito a anular", ops)
      if st.button("🗑️ Anular"):
        idx = int(a_borrar.split("#")[1].split(" -")[0])
        item = creditos.pop(idx)
        if (
            item.get("¿Lleva Tarjeta?") == "Sí"
            and item.get("Tarjeta Entregada") != "N/A"
        ):
          t = item.get("Tarjeta Entregada")
          inventario[t] = inventario.get(t, 0) + 1
          guardar_inv(inventario)
        guardar_lista("cred", creditos)
        st.success("Anulado.")
        st.rerun()

  elif sub == "Entradas":
    df_r = procesar_df(entradas, "Fecha de Llegada")
    st.dataframe(df_r, use_container_width=True)
    if not df_r.empty:
      st.download_button("📥 Excel", a_excel(df_r), "entradas.xlsx")

  elif sub == "Traslados":
    df_r = procesar_df(traslados, "Fecha/Hora")
    st.dataframe(df_r, use_container_width=True)
    if not df_r.empty:
      st.download_button("📥 Excel", a_excel(df_r), "traslados.xlsx")
                             
