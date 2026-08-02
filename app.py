import datetime
from zoneinfo import ZoneInfo
import io
import os
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Control de Tarjetas de Crédito",
    page_icon="💳",
    layout="centered",
)

# Archivos locales de persistencia
ARCHIVOS_DATOS = {
    "inventario": "inventario.csv",
    "entradas": "entradas.csv",
    "traslados": "traslados.csv",
    "entregas": "entregas.csv",
}


# Función oficial para obtener la fecha y hora de Colombia
def obtener_hora_colombia():
  return datetime.datetime.now(ZoneInfo("America/Bogota"))


def cargar_datos():
  # Inventario
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

  # Entradas
  entradas = []
  if (
      os.path.exists(ARCHIVOS_DATOS["entradas"])
      and os.path.getsize(ARCHIVOS_DATOS["entradas"]) > 0
  ):
    try:
      entradas = (
          pd.read_csv(ARCHIVOS_DATOS["entradas"]).dropna(how="all").to_dict("records")
      )
    except:
      entradas = []

  # Traslados
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

  # Entregas
  entregas = []
  if (
      os.path.exists(ARCHIVOS_DATOS["entregas"])
      and os.path.getsize(ARCHIVOS_DATOS["entregas"]) > 0
  ):
    try:
      entregas = (
          pd.read_csv(ARCHIVOS_DATOS["entregas"]).dropna(how="all").to_dict("records")
      )
    except:
      entregas = []

  return inventario, entradas, traslados, entregas


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
  processed_data = output.getvalue()
  return processed_data


# Cargar datos
inventario, entradas, traslados, entregas = cargar_datos()

RESPONSABLES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro"]
TIPOS_VENTA = ["Venta en tienda", "Cliente agendado"]

st.title("💳 Control de Inventario y Entregas")
st.markdown("Gestión operativa con control de inventario permanente.")

# Control de Acceso de Administrador exclusivo para borrar entregas
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Acceso Administrador")
es_admin = False
password_ingresada = st.sidebar.text_input(
    "Contraseña Admin", type="password", key="pass_admin"
)
if password_ingresada == "admin123":  # Puedes cambiar la contraseña aquí
  st.sidebar.success("Modo Admin Activo 🔓 (Permite borrar entregas)")
  es_admin = True
elif password_ingresada:
  st.sidebar.error("Contraseña incorrecta")

# Menú lateral de navegación
menu = st.sidebar.selectbox(
    "Menú de Navegación",
    [
        "Ver Inventario",
        "Ingresar Lote (Inventario)",
        "Traslado a Sucursal",
        "Registrar Entrega a Cliente",
        "Historiales, Filtros y Excel",
    ],
)

# 1. VER INVENTARIO
if menu == "Ver Inventario":
  st.header("📋 Inventario Actual de Tarjetas")
  if not inventario:
    st.info("No hay tarjetas registradas en el inventario.")
  else:
    df_inv = pd.DataFrame(
        list(inventario.items()),
        columns=["Tipo de Tarjeta", "Cantidad Disponible"],
    )
    st.dataframe(df_inv, use_container_width=True)

# 2. INGRESAR LOTE
elif menu == "Ingresar Lote (Inventario)":
  st.header("➕ Ingresar Tarjetas al Inventario")
  with st.form("form_ingreso"):
    tipo_tarjeta = (
        st.text_input("Tipo / Nombre de Tarjeta (Ej: Visa Clásica, Mastercard)")
        .strip()
        .title()
    )
    cantidad = st.number_input(
        "Cantidad de Tarjetas", min_value=1, step=1, value=1
    )
    fecha_llegada = st.date_input(
        "Fecha de Llegada", value=obtener_hora_colombia().date()
    )
    responsable = st.selectbox(
        "Responsable de Ingreso", RESPONSABLES, key="resp_ingreso"
    )
    submit_ingreso = st.form_submit_button("Guardar Ingreso")

    if submit_ingreso:
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
        st.success(
            f"¡Se ingresaron {cantidad} tarjetas de '{tipo_tarjeta}' y se"
            " guardaron!"
        )
      else:
        st.warning("Por favor, ingresa el tipo de tarjeta.")

# 3. TRASLADO A SUCURSAL
elif menu == "Traslado a Sucursal":
  st.header("🚚 Traslado de Tarjetas a Otra Sucursal")
  if not inventario:
    st.warning("No hay inventario disponible para realizar traslados.")
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
      responsable_salida = st.selectbox(
          "Responsable del Traslado", RESPONSABLES, key="resp_traslado"
      )
      submit_traslado = st.form_submit_button("Confirmar Traslado")

      if submit_traslado:
        if not sucursal_destino:
          st.warning("Indica la sucursal de destino.")
        elif cantidad_traslado > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades"
              " disponibles."
          )
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
          st.success("¡Traslado registrado y guardado con éxito!")

# 4. REGISTRAR ENTREGA A CLIENTE (CON FECHA MANUAL Y SIN HORA)
elif menu == "Registrar Entrega a Cliente":
  st.header("👤 Registrar Entrega de Tarjeta")
  if not inventario:
    st.warning("No hay inventario disponible para entregas.")
  else:
    with st.form("form_entrega"):
      tarjeta_sel = st.selectbox(
          "Selecciona la Tarjeta a Entregar",
          list(inventario.keys()),
          key="sel_ent",
      )
      stock_actual = inventario[tarjeta_sel]
      st.write(f"Stock disponible actual: **{stock_actual}**")

      cantidad_entrega = st.number_input(
          "Cantidad Entregada", min_value=1, step=1, value=1, key="cant_ent"
      )
      nombre_cliente = (
          st.text_input("Nombre del Cliente / Celular").strip().title()
      )
      tipo_venta = st.selectbox("Tipo de Entrega / Venta", TIPOS_VENTA)
      equipo_financiado = (
          st.text_input(
              "Referencia del Equipo Financiado (Ej: Samsung Galaxy A54)"
          )
          .strip()
          .title()
      )

      # Campo de fecha manual para la entrega
      fecha_entrega = st.date_input(
          "Fecha de Entrega", value=obtener_hora_colombia().date()
      )

      responsable_entrega = st.selectbox(
          "Asesor Responsable", RESPONSABLES, key="resp_entrega"
      )

      submit_entrega = st.form_submit_button("Confirmar Entrega")

      if submit_entrega:
        if not nombre_cliente or not equipo_financiado:
          st.warning("Por favor completa el nombre del cliente y el equipo.")
        elif cantidad_entrega > stock_actual:
          st.error(f"Stock insuficiente ({stock_actual} disponibles).")
        else:
          inventario[tarjeta_sel] -= cantidad_entrega
          entregas.append({
              "Fecha": str(fecha_entrega),
              "Cliente": nombre_cliente,
              "Tipo de Venta": tipo_venta,
              "Equipo Financiado": equipo_financiado,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_entrega,
              "Asesor": responsable_entrega,
          })
          guardar_inventario(inventario)
          guardar_lista("entregas", entregas)
          st.success("¡Entrega registrada e inventario actualizado con éxito!")

# 5. HISTORIALES, FILTROS Y EXCEL
elif menu == "Historiales, Filtros y Excel":
  st.header("📊 Historiales, Filtros y Exportación")

  sub_menu = st.radio(
      "Selecciona el historial:",
      [
          "Entregas a Clientes (Gestión y Borrado)",
          "Entradas (Llegadas)",
          "Traslados",
      ],
  )

  st.markdown("---")
  st.subheader("🔍 Filtros de Búsqueda y Reportes")

  col1, col2 = st.columns(2)
  with col1:
    filtro_texto = st.text_input(
        "Buscar por Cliente, Equipo o Asesor:"
    ).lower()
  with col2:
    activar_fechas = st.checkbox("Filtrar por rango de fechas")

  filtro_tipo_venta = "Todos"
  if sub_menu == "Entregas a Clientes (Gestión y Borrado)":
    filtro_tipo_venta = st.selectbox(
        "Filtrar por Tipo de Venta:", ["Todos"] + TIPOS_VENTA
    )

  fecha_inicio, fecha_fin = None, None
  if activar_fechas:
    c1, c2 = st.columns(2)
    with c1:
      fecha_inicio = st.date_input(
          "Fecha inicio", obtener_hora_colombia().date()
      )
    with c2:
      fecha_fin = st.date_input("Fecha fin", obtener_hora_colombia().date())

  st.markdown("---")


  def aplicar_filtros(lista_datos, col_fecha):
    if not lista_datos:
      return pd.DataFrame()
    df = pd.DataFrame(lista_datos)

    if (
        sub_menu == "Entregas a Clientes (Gestión y Borrado)"
        and filtro_tipo_venta != "Todos"
        and "Tipo de Venta" in df.columns
    ):
      df = df[df["Tipo de Venta"] == filtro_tipo_venta]

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


  if sub_menu == "Entregas a Clientes (Gestión y Borrado)":
    st.subheader("👤 Registro de Entregas y Equipos Financiados")
    df_res = aplicar_filtros(entregas, "Fecha")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )

    if not df_res.empty:
      excel_data = convertir_a_excel(df_res)
      st.download_button(
          "📥 Descargar Entregas en Excel",
          excel_data,
          "reporte_entregas.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

    st.markdown("---")
    st.subheader("⚙️ Panel de Anulación y Devolución (Solo Administrador)")
    if not es_admin:
      st.warning(
          "🔒 Ingresa la contraseña de Administrador en la barra lateral para"
          " poder borrar entregas y reponer el stock al inventario."
      )
    else:
      if entregas:
        indices_entregas = []
        for i, e in enumerate(entregas):
          f_fecha = e.get("Fecha", e.get("Fecha/Hora", "S/F"))
          cli = e.get("Cliente", e.get("Cliente / Celular", "S/C"))
          t_venta = e.get("Tipo de Venta", "N/A")
          tarj = e.get("Tarjeta", "N/A")
          cant = e.get("Cantidad", 1)
          indices_entregas.append(
              f"#{i} - {f_fecha} | {cli} | {t_venta} | Tarjeta: {tarj} (Cant:"
              f" {cant})"
          )

        entrega_a_borrar = st.selectbox(
            "Selecciona la entrega a eliminar", indices_entregas
        )

        if st.button(
            "🗑️ Borrar Entrega y Devolver Tarjeta(s) al Inventario de"
            " Inmediato"
        ):
          idx = int(entrega_a_borrar.split("#")[1].split(" -")[0])
          item_eliminado = entregas.pop(idx)

          tarjeta_devuelta = item_eliminado["Tarjeta"]
          cant_devuelta = item_eliminado["Cantidad"]
          inventario[tarjeta_devuelta] = (
              inventario.get(tarjeta_devuelta, 0) + cant_devuelta
          )

          guardar_inventario(inventario)
          guardar_lista("entregas", entregas)

          st.success(
              f"¡Entrega eliminada! Se han devuelto {cant_devuelta} unidad(es)"
              f" de '{tarjeta_devuelta}' al inventario de forma inmediata."
          )
          st.rerun()

  elif sub_menu == "Entradas (Llegadas)":
    st.subheader("📥 Registro de Entradas")
    df_res = aplicar_filtros(entradas, "Fecha de Llegada")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )
    if not df_res.empty:
      excel_data = convertir_a_excel(df_res)
      st.download_button(
          "📥 Descargar Entradas en Excel",
          excel_data,
          "reporte_entradas.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

  elif sub_menu == "Traslados":
    st.subheader("🚚 Registro de Traslados")
    df_res = aplicar_filtros(traslados, "Fecha/Hora")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )
    if not df_res.empty:
      excel_data = convertir_a_excel(df_res)
      st.download_button(
          "📥 Descargar Traslados en Excel",
          excel_data,
          "reporte_traslados.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            
