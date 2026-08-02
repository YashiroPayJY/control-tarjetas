import calendar
import datetime
from zoneinfo import ZoneInfo
import io
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Control Pro - Payjoy & Créditos", page_icon="📱", layout="wide"
)

ARCHIVOS_DATOS = {
    "inventario": "inventario.csv",
    "entradas": "entradas.csv",
    "creditos": "creditos.csv",
    "traslados": "traslados.csv",
}


def obtener_hora_colombia():
  return datetime.datetime.now(ZoneInfo("America/Bogota"))


def cargar_datos():
  inventario = {}
  if (
      os.path.exists(ARCHIVOS_DATOS["inventario"])
      and os.path.getsize(ARCHIVOS_DATOS["inventario"]) > 0
  ):
    try:
      df_inv = pd.read_csv(ARCHIVOS_DATOS["inventario"])
      if not df_inv.empty and "Tipo de Tarjeta" in df_inv.columns:
        inventario = dict(
            zip(df_inv["Tipo de Tarjeta"], df_inv["Cantidad Disponible"])
        )
    except:
      inventario = {}

  entradas = []
  if (
      os.path.exists(ARCHIVOS_DATOS["entradas"])
      and os.path.getsize(ARCHIVOS_DATOS["entradas"]) > 0
  ):
    try:
      entradas = (
          pd.read_csv(ARCHIVOS_DATOS["entradas"])
          .dropna(how="all")
          .to_dict("records")
      )
    except:
      entradas = []

  traslados = []
  if (
      os.path.exists(ARCHIVOS_DATOS["traslados"])
      and os.path.getsize(ARCHIVOS_DATOS["traslados"]) > 0
  ):
    try:
      traslados = (
          pd.read_csv(ARCHIVOS_DATOS["traslados"])
          .dropna(how="all")
          .to_dict("records")
      )
    except:
      traslados = []

  creditos = []
  if (
      os.path.exists(ARCHIVOS_DATOS["creditos"])
      and os.path.getsize(ARCHIVOS_DATOS["creditos"]) > 0
  ):
    try:
      creditos = (
          pd.read_csv(ARCHIVOS_DATOS["creditos"])
          .dropna(how="all")
          .to_dict("records")
      )
    except:
      creditos = []

  return inventario, entradas, traslados, creditos


def guardar_inventario(inventario):
  df = (
      pd.DataFrame(
          list(inventario.items()),
          columns=["Tipo de Tarjeta", "Cantidad Disponible"],
      )
      if inventario
      else pd.DataFrame(columns=["Tipo de Tarjeta", "Cantidad Disponible"])
  )
  df.to_csv(ARCHIVOS_DATOS["inventario"], index=False)


def guardar_lista(nombre_clave, lista_datos):
  df = pd.DataFrame(lista_datos) if lista_datos else pd.DataFrame()
  df.to_csv(ARCHIVOS_DATOS[nombre_clave], index=False)


def convertir_a_excel(df):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Reporte")
  return output.getvalue()


inventario, entradas, traslados, creditos = cargar_datos()

RESPONSABLES = [
    "Edgardo",
    "Alexandra",
    "Yeriz",
    "Alejandro",
    "P Marca",
    "A Rutero",
]
TIPOS_VENTA = ["Venta en tienda", "Cliente agendado"]
MARCAS_CELULAR = [
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
META_MENSUAL = 185

st.title("📱 Control Operativo Payjoy & Financiación de Celulares")
st.markdown("---")

st.sidebar.markdown("### 🔐 Panel de Control")
password_ingresada = st.sidebar.text_input(
    "Contraseña Administrador", type="password", key="pass_admin"
)
es_admin = password_ingresada == "admin123"
if es_admin:
  st.sidebar.success("Modo Admin Activo 🔓")
elif password_ingresada:
  st.sidebar.error("Contraseña incorrecta")

st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Menú Principal",
    [
        "📊 Dashboard & Cumplimiento de Meta",
        "📱 Registrar Venta de Crédito Payjoy",
        "💳 Entregar Tarjeta Pendiente",
        "📦 Stock de Tarjetas (Inventario)",
        "➕ Ingresar Lote de Tarjetas",
        "🚚 Traslado de Tarjetas",
        "📂 Historiales y Reportes",
    ],
)

if menu == "📊 Dashboard & Cumplimiento de Meta":
  st.header("📈 Dashboard Gerencial - Meta Mensual de Créditos")
  ahora = obtener_hora_colombia()
  dia_actual = ahora.day
  dias_mes_total = calendar.monthrange(ahora.year, ahora.month)[1]

  total_ventas_mes = 0
  df_mes_actual = pd.DataFrame()

  if creditos:
    df_creditos = pd.DataFrame(creditos)
    if "Fecha" in df_creditos.columns and "Cantidad" in df_creditos.columns:
      df_creditos["_fecha_dt"] = pd.to_datetime(
          df_creditos["Fecha"], errors="coerce"
      )
      df_mes_actual = df_creditos[
          (df_creditos["_fecha_dt"].dt.month == ahora.month)
          & (df_creditos["_fecha_dt"].dt.year == ahora.year)
      ]
      total_ventas_mes = (
          int(df_mes_actual["Cantidad"].sum())
          if not df_mes_actual.empty
          else 0
      )

  porcentaje_cumplimiento = min(
      round((total_ventas_mes / META_MENSUAL) * 100, 2), 100.0
  )
  promedio_diario = total_ventas_mes / dia_actual if dia_actual > 0 else 0
  proyeccion_cierre = int(promedio_diario * dias_mes_total)

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("🎯 Meta Mensual", f"{META_MENSUAL} Créditos")
  c2.metric("✅ Créditos Vendidos (Mes)", f"{total_ventas_mes}")
  c3.metric("📊 % Cumplimiento Global", f"{porcentaje_cumplimiento}%")
  c4.metric("🔮 Proyección Cierre de Mes", f"{proyeccion_cierre} Créditos")

  st.markdown("### Progreso hacia la Meta Mensual")
  st.progress(min(total_ventas_mes / META_MENSUAL, 1.0))
  st.markdown("---")

  if not df_mes_actual.empty and "Marca de Celular" in df_mes_actual.columns:
    g1, g2 = st.columns(2)
    with g1:
      st.subheader("🥧 Participación por Asesor (% de la Meta / Ventas)")
      df_asesor = (
          df_mes_actual.groupby("Asesor")["Cantidad"].sum().reset_index()
      )
      fig_pie = px.pie(
          df_asesor,
          names="Asesor",
          values="Cantidad",
          hole=0.4,
          color_discrete_sequence=px.colors.sequential.Teal,
      )
      st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
      st.subheader("📱 Participación por Marca de Celular")
      df_marca = (
          df_mes_actual.groupby("Marca de Celular")["Cantidad"]
          .sum()
          .reset_index()
      )
      fig_marca = px.bar(
          df_marca, x="Marca de Celular", y="Cantidad", color="Marca de Celular"
      )
      st.plotly_chart(fig_marca, use_container_width=True)

    st.markdown("### 🏆 Rendimiento Detallado por Asesor (Mes Actual)")
    tabla_asesores = (
        df_mes_actual.groupby("Asesor")["Cantidad"]
        .sum()
        .reset_index(name="Créditos Realizados")
    )
    tabla_asesores["% de la Meta (185)"] = (
        (tabla_asesores["Créditos Realizados"] / META_MENSUAL * 100)
        .round(2)
        .astype(str)
        + "%"
    )
    st.dataframe(tabla_asesores, use_container_width=True)
  else:
    st.info(
        "💡 Aún no hay créditos registrados en el mes actual. Comienza a"
        " registrar ventas en el menú lateral para ver las gráficas y"
        " estadísticas en vivo."
    )

elif menu == "📱 Registrar Venta de Crédito Payjoy":
  st.header("📱 Registrar Nueva Venta de Crédito Payjoy")
  with st.form("form_credito"):
    nombre_cliente = (
        st.text_input("Nombre del Cliente / Celular de Contacto")
        .strip()
        .title()
    )
    marca_celular = st.selectbox("Marca del Equipo Financiado", MARCAS_CELULAR)
    tipo_venta = st.selectbox("Tipo de Venta", TIPOS_VENTA)
    lleva_tarjeta = st.selectbox(
        "¿Lleva Tarjeta Física (Mastercard By Payjoy)?", ["Sí", "No"]
    )

    cantidad_tarjetas, tarjeta_sel, stock_actual = 0, None, 0
    if lleva_tarjeta == "Sí":
      if not inventario:
        st.error(
            "⚠️ No hay stock de tarjetas en inventario. Ingresa un lote"
            " primero."
        )
      else:
        tarjeta_sel = st.selectbox(
            "Selecciona la Tarjeta a Entregar del Stock", list(inventario.keys())
        )
        stock_actual = inventario[tarjeta_sel]
        st.write(f"Stock disponible de esta tarjeta: **{stock_actual}**")
        cantidad_tarjetas = st.number_input(
            "Cantidad de Tarjetas a Entregar", min_value=1, step=1, value=1
        )

    fecha_venta = st.date_input(
        "Fecha de Venta", value=obtener_hora_colombia().date()
    )
    asesor_responsable = st.selectbox("Asesor Responsable", RESPONSABLES)

    if st.form_submit_button("Registrar Venta de Crédito"):
      if not nombre_cliente:
        st.warning("Por favor completa el nombre del cliente o celular.")
      elif lleva_tarjeta == "Sí" and cantidad_tarjetas > stock_actual:
        st.error(
            f"Stock insuficiente de tarjetas ({stock_actual} disponibles)."
        )
      else:
        if lleva_tarjeta == "Sí" and tarjeta_sel:
          inventario[tarjeta_sel] -= cantidad_tarjetas
          guardar_inventario(inventario)

        creditos.append({
            "Fecha": str(fecha_venta),
            "Cliente": nombre_cliente,
            "Marca de Celular": marca_celular,
            "Tipo de Venta": tipo_venta,
            "¿Lleva Tarjeta?": lleva_tarjeta,
            "Tarjeta Entregada": tarjeta_sel if lleva_tarjeta == "Sí" else "N/A",
            "Cantidad": 1,
            "Asesor": asesor_responsable,
        })
        guardar_lista("creditos", creditos)
        st.success("¡Crédito Payjoy registrado con éxito!")

elif menu == "💳 Entregar Tarjeta Pendiente":
  st.header("💳 Entregar Tarjeta Física a Créditos Pendientes")
  st.markdown(
      "Selecciona un cliente que haya quedado sin tarjeta física para"
      " entregarla ahora y descontarla del inventario."
  )

  # Filtrar créditos que tengan "¿Lleva Tarjeta?": "No"
  creditos_pendientes = [
      (i, c) for i, c in enumerate(creditos) if c.get("¿Lleva Tarjeta?") == "No"
  ]

  if not creditos_pendientes:
    st.info("🎉 ¡Excelente! No hay créditos pendientes por entrega de tarjeta.")
  elif not inventario:
    st.error(
        "⚠️ No hay stock físico de tarjetas en inventario para realizar la"
        " entrega. Ingresa un lote primero."
    )
  else:
    with st.form("form_pendiente"):
      opciones_select = []
      for idx, c in creditos_pendientes:
        opciones_select.append(
            f"#{idx} - Fecha: {c.get('Fecha')} | Cliente: {c.get('Cliente')} |"
            f" Asesor: {c.get('Asesor')} | Equipo: {c.get('Marca de Celular')}"
        )

      credito_elegido = st.selectbox(
          "Selecciona el Crédito Pendiente", opciones_select
      )
      tarjeta_entrega = st.selectbox(
          "Selecciona la Tarjeta del Stock", list(inventario.keys())
      )
      stock_bodega = inventario[tarjeta_entrega]
      st.write(f"Stock disponible de esta tarjeta: **{stock_bodega}**")

      if st.form_submit_button("Confirmar Entrega de Tarjeta Pendiente"):
        if stock_bodega < 1:
          st.error("Stock insuficiente de esta tarjeta.")
        else:
          idx_real = int(credito_elegido.split("#")[1].split(" -")[0])

          # Descontar inventario
          inventario[tarjeta_entrega] -= 1
          guardar_inventario(inventario)

          # Actualizar el registro del crédito
          creditos[idx_real]["¿Lleva Tarjeta?"] = "Sí"
          creditos[idx_real]["Tarjeta Entregada"] = tarjeta_entrega
          guardar_lista("creditos", creditos)

          st.success(
              "¡Tarjeta entregada y stock actualizado con éxito para este"
              " cliente!"
          )
          st.rerun()

elif menu == "📦 Stock de Tarjetas (Inventario)":
  st.header("📦 Stock Actual de Tarjetas Físicas")
  if not inventario:
    st.info("No hay tarjetas registradas en inventario.")
  else:
    st.dataframe(
        pd.DataFrame(
            list(inventario.items()),
            columns=["Tipo de Tarjeta", "Cantidad Disponible en Bodega"],
        ),
        use_container_width=True,
    )

elif menu == "➕ Ingresar Lote de Tarjetas":
  st.header("➕ Ingresar Lote de Tarjetas Físicas")
  with st.form("form_ingreso_tarjeta"):
    tipo_tarjeta = (
        st.text_input("Nombre de Tarjeta (Ej: Mastercard By Payjoy)")
        .strip()
        .title()
    )
    cantidad = st.number_input(
        "Cantidad de Tarjetas", min_value=1, step=1, value=10
    )
    fecha_llegada = st.date_input(
        "Fecha de Llegada", value=obtener_hora_colombia().date()
    )
    responsable = st.selectbox("Responsable de Recepción", RESPONSABLES)
    if st.form_submit_button("Guardar Lote en Inventario"):
      if tipo_tarjeta:
        inventario[tipo_tarjeta] = inventario.get(tipo_tarjeta, 0) + cantidad
        entradas.append({
            "Fecha Registro": obtener_hora_colombia().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "Fecha de Llegada": str(fecha_llegada),
            "Tarjeta": tipo_tarjeta,
            "Cantidad": cantidad,
            "Responsable": responsable,
        })
        guardar_inventario(inventario)
        guardar_lista("entradas", entradas)
        st.success(f"¡Se ingresaron {cantidad} tarjetas con éxito!")
      else:
        st.warning("Por favor ingresa el nombre de la tarjeta.")

elif menu == "🚚 Traslado de Tarjetas":
  st.header("🚚 Traslado de Tarjetas Físicas a Sucursales")
  if not inventario:
    st.warning("No hay stock físico disponible para traslados.")
  else:
    with st.form("form_traslado"):
      tarjeta_sel = st.selectbox("Selecciona la Tarjeta", list(inventario.keys()))
      stock_actual = inventario[tarjeta_sel]
      st.write(f"Stock disponible actual: **{stock_actual}**")
      cantidad_traslado = st.number_input(
          "Cantidad a Trasladar", min_value=1, step=1, value=1
      )
      sucursal_destino = (
          st.text_input("Sucursal de Destino").strip().title()
      )
      responsable_salida = st.selectbox("Responsable del Traslado", RESPONSABLES)
      if st.form_submit_button("Confirmar Traslado"):
        if not sucursal_destino:
          st.warning("Indica la sucursal de destino.")
        elif cantidad_traslado > stock_actual:
          st.error(f"Stock insuficiente ({stock_actual} disponibles).")
        else:
          inventario[tarjeta_sel] -= cantidad_traslado
          traslados.append({
              "Fecha/Hora": obtener_hora_colombia().strftime("%Y-%m-%d %H:%M"),
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_traslado,
              "Sucursal Destino": sucursal_destino,
              "Responsable": responsable_salida,
          })
          guardar_inventario(inventario)
          guardar_lista("traslados", traslados)
          st.success("¡Traslado de stock registrado con éxito!")

elif menu == "📂 Historiales y Reportes":
  st.header("📂 Historiales, Filtros y Exportación Excel")
  sub_menu = st.radio(
      "Selecciona el reporte:",
      ["Créditos Payjoy Vendidos", "Lotes de Tarjetas Ingresados", "Traslados"],
  )
  st.markdown("---")

  c1, c2 = st.columns(2)
  with c1:
    filtro_texto = st.text_input(
        "Buscar por Cliente o Asesor:"
    ).lower()
  with c2:
    activar_fechas = st.checkbox("Filtrar por rango de fechas")

  filtro_tipo_venta, filtro_asesor, filtro_marca, filtro_tarjeta_estado = (
      "Todos",
      "Todos",
      "Todos",
      "Todos",
  )
  if sub_menu == "Créditos Payjoy Vendidos":
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
      filtro_tipo_venta = st.selectbox(
          "Filtrar por Tipo de Venta:", ["Todos"] + TIPOS_VENTA
      )
    with cc2:
      filtro_asesor = st.selectbox(
          "Filtrar por Asesor:", ["Todos"] + RESPONSABLES
      )
    with cc3:
      filtro_marca = st.selectbox(
          "Filtrar por Marca:", ["Todos"] + MARCAS_CELULAR
      )
    with cc4:
      filtro_tarjeta_estado = st.selectbox(
          "Filtrar por Tarjeta Física:", ["Todos", "Sí", "No"]
      )

  fecha_inicio, fecha_fin = None, None
  if activar_fechas:
    fc1, fc2 = st.columns(2)
    with fc1:
      fecha_inicio = st.date_input(
          "Fecha inicio", obtener_hora_colombia().date()
      )
    with fc2:
      fecha_fin = st.date_input("Fecha fin", obtener_hora_colombia().date())
  st.markdown("---")


  def aplicar_filtros(lista_datos, col_fecha):
    if not lista_datos:
      return pd.DataFrame()
    df = pd.DataFrame(lista_datos)
    if sub_menu == "Créditos Payjoy Vendidos":
      if filtro_tipo_venta != "Todos" and "Tipo de Venta" in df.columns:
        df = df[df["Tipo de Venta"] == filtro_tipo_venta]
      if filtro_asesor != "Todos" and "Asesor" in df.columns:
        df = df[df["Asesor"] == filtro_asesor]
      if filtro_marca != "Todos" and "Marca de Celular" in df.columns:
        df = df[df["Marca de Celular"] == filtro_marca]
      if filtro_tarjeta_estado != "Todos" and "¿Lleva Tarjeta?" in df.columns:
        df = df[df["¿Lleva Tarjeta?"] == filtro_tarjeta_estado]
    if filtro_texto:
      mask = df.astype(str).apply(
          lambda x: x.str.lower().str.contains(filtro_texto).any(), axis=1
      )
      df = df[mask]
    if activar_fechas and col_fecha in df.columns:
      df["_fecha_temp"] = pd.to_datetime(df[col_fecha]).dt.date
      df = df[
          (df["_fecha_temp"] >= fecha_inicio)
          & (df["_fecha_temp"] <= fecha_fin)
      ]
      df = df.drop(columns=["_fecha_temp"])
    return df


  if sub_menu == "Créditos Payjoy Vendidos":
    st.subheader("📱 Reporte Detallado de Créditos Payjoy")
    df_res = aplicar_filtros(creditos, "Fecha")

    if not df_res.empty and "Marca de Celular" in df_res.columns:
      st.markdown("##### 📊 Análisis de Ventas por Marca")
      df_marca_rep = (
          df_res.groupby("Marca de Celular")["Cantidad"].sum().reset_index()
      )
      df_marca_rep["Aporte (%)"] = (
          (df_marca_rep["Cantidad"] / df_res["Cantidad"].sum() * 100)
          .round(2)
          .astype(str)
          + "%"
      )
      fig_marca_rep = px.bar(
          df_marca_rep,
          x="Marca de Celular",
          y="Cantidad",
          text="Aporte (%)",
          color="Marca de Celular",
      )
      st.plotly_chart(fig_marca_rep, use_container_width=True)

    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )

    if not df_res.empty:
      st.download_button(
          "📥 Descargar Créditos en Excel",
          convertir_a_excel(df_res),
          "reporte_creditos.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

    st.markdown("---")
    st.subheader("⚙️ Panel de Anulación de Créditos (Solo Administrador)")
    if not es_admin:
      st.warning("🔒 Ingresa la contraseña de Administrador en la barra lateral.")
    else:
      if creditos:
        indices_creditos = [
            f"#{i} - {c.get('Fecha')} | Asesor: {c.get('Asesor')} | {c.get('Cliente')} | {c.get('Marca de Celular')}"
            for i, c in enumerate(creditos)
        ]
        credito_a_borrar = st.selectbox(
            "Selecciona el crédito a anular", indices_creditos
        )
        if st.button("🗑️ Anular Crédito y Devolver Tarjeta (Si aplica)"):
          idx = int(credito_a_borrar.split("#")[1].split(" -")[0])
          item_eliminado = creditos.pop(idx)
          if (
              item_eliminado.get("¿Lleva Tarjeta?") == "Sí"
              and item_eliminado.get("Tarjeta Entregada") != "N/A"
          ):
            tarj = item_eliminado.get("Tarjeta Entregada")
            inventario[tarj] = inventario.get(tarj, 0) + 1
            guardar_inventario(inventario)
          guardar_lista("creditos", creditos)
          st.success("¡Crédito anulado con éxito!")
          st.rerun()

  elif sub_menu == "Lotes de Tarjetas Ingresados":
    st.subheader("📦 Reporte de Lotes de Tarjetas")
    df_res = aplicar_filtros(entradas, "Fecha de Llegada")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )
    if not df_res.empty:
      st.download_button(
          "📥 Descargar Entradas en Excel",
          convertir_a_excel(df_res),
          "reporte_entradas.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.shee
