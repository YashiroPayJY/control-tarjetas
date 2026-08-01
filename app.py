import datetime
import os
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Control de Tarjetas de Crédito",
    page_icon="💳",
    layout="centered",
)

# Archivo local donde se guardarán los datos permanentemente en la nube
ARCHIVOS_DATOS = {
    "inventario": "inventario.csv",
    "entradas": "entradas.csv",
    "traslados": "traslados.csv",
    "entregas": "entregas.csv",
}


# Funciones para leer y escribir en archivos CSV persistentes
def cargar_datos():
  # Inventario
  if os.path.exists(ARCHIVOS_DATOS["inventario"]):
    df_inv = pd.read_csv(ARCHIVOS_DATOS["inventario"])
    inventario = dict(
        zip(df_inv["Tipo de Tarjeta"], df_inv["Cantidad Disponible"])
    )
  else:
    inventario = {}

  # Entradas
  if os.path.exists(ARCHIVOS_DATOS["entradas"]):
    entradas = (
        pd.read_csv(ARCHIVOS_DATOS["entradas"]).dropna(how="all").to_dict("records")
    )
  else:
    entradas = []

  # Traslados
  if os.path.exists(ARCHIVOS_DATOS["traslados"]):
    traslados = (
        pd.read_csv(ARCHIVOS_DATOS["traslados"])
        .dropna(how="all")
        .to_dict("records")
    )
  else:
    traslados = []

  # Entregas
  if os.path.exists(ARCHIVOS_DATOS["entregas"]):
    entregas = (
        pd.read_csv(ARCHIVOS_DATOS["entregas"]).dropna(how="all").to_dict("records")
    )
  else:
    entregas = []

  return inventario, entradas, traslados, entregas


def guardar_inventario(inventario):
  if inventario:
    df = pd.DataFrame(
        list(inventario.items()),
        columns=["Tipo de Tarjeta", "Cantidad Disponible"],
    )
  else:
    df = pd.DataFrame(columns=["Tipo de Tarjeta", "Cantidad Disponible"])
  df.to_csv(ARCHIVOS_DATOS["inventario"], index=False)


def guardar_lista(nombre_clave, lista_datos):
  if lista_datos:
    df = pd.DataFrame(lista_datos)
  else:
    df = pd.DataFrame()
  df.to_csv(ARCHIVOS_DATOS[nombre_clave], index=False)


# Cargar estado actual
inventario, entradas, traslados, entregas = cargar_datos()

RESPONSABLES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro"]

st.title("💳 Control de Inventario y Entregas de Tarjetas")
st.markdown("Gestión operativa con persistencia permanente de datos.")

# Menú lateral de navegación
menu = st.sidebar.selectbox(
    "Menú de Navegación",
    [
        "Ver Inventario",
        "Ingresar Lote (Inventario)",
        "Traslado a Sucursal",
        "Registrar Entrega a Cliente",
        "Historiales y Registros",
    ],
)

# 1. VER INVENTARIO ACTUAL
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
        "Fecha de Llegada", value=datetime.date.today()
    )
    responsable = st.selectbox(
        "Responsable de Ingreso", RESPONSABLES, key="resp_ingreso"
    )

    submit_ingreso = st.form_submit_button("Guardar Ingreso")

    if submit_ingreso:
      if tipo_tarjeta:
        if tipo_tarjeta in inventario:
          inventario[tipo_tarjeta] += cantidad
        else:
          inventario[tipo_tarjeta] = cantidad

        entradas.append({
            "Fecha Registro": datetime.datetime.now().strftime(
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
            " guardaron permanentemente!"
        )
      else:
        st.warning("Por favor, ingresa el tipo de tarjeta.")

# 3. TRASLADO A OTRA SUCURSAL
elif menu == "Traslado a Sucursal":
  st.header("🚚 Traslado de Tarjetas a Otra Sucursal")

  if not inventario:
    st.warning("No hay inventario disponible para realizar traslados.")
  else:
    tarjetas_disponibles = list(inventario.keys())

    with st.form("form_traslado"):
      tarjeta_sel = st.selectbox("Selecciona la Tarjeta", tarjetas_disponibles)
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
          st.warning("Debes indicar la sucursal de destino.")
        elif cantidad_traslado > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades"
              " disponibles."
          )
        else:
          inventario[tarjeta_sel] -= cantidad_traslado
          fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

          traslados.append({
              "Fecha/Hora": fecha_hora,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_traslado,
              "Sucursal Destino": sucursal_destino,
              "Responsable": responsable_salida,
          })

          guardar_inventario(inventario)
          guardar_lista("traslados", traslados)

          st.success(
              f"¡Traslado exitoso de {cantidad_traslado} tarjetas de"
              f" '{tarjeta_sel}' hacia {sucursal_destino} (Guardado)!"
          )

# 4. REGISTRAR ENTREGA DE TARJETA CON EQUIPO FINANCIADO
elif menu == "Registrar Entrega a Cliente":
  st.header("👤 Registrar Entrega de Tarjeta y Equipo Financiado")

  if not inventario:
    st.warning("No hay inventario disponible para entregas.")
  else:
    tarjetas_disponibles = list(inventario.keys())

    with st.form("form_entrega"):
      tarjeta_sel = st.selectbox(
          "Selecciona la Tarjeta a Entregar",
          tarjetas_disponibles,
          key="sel_ent",
      )
      stock_actual = inventario[tarjeta_sel]
      st.write(f"Stock disponible actual: **{stock_actual}**")

      cantidad_entrega = st.number_input(
          "Cantidad Entregada", min_value=1, step=1, value=1, key="cant_ent"
      )

      # Campos adaptados para el equipo financiado y el cliente/celular
      equipo_financiado = (
          st.text_input(
              "Referencia del Equipo Financiado (Ej: Samsung Galaxy A54, iPhone"
              " 13)"
          )
          .strip()
          .title()
      )
      nombre_cliente = (
          st.text_input(
              "Nombre del Cliente o Número de Celular de Contacto"
          )
          .strip()
          .title()
      )

      responsable_entrega = st.selectbox(
          "Responsable de la Entrega", RESPONSABLES, key="resp_entrega"
      )

      submit_entrega = st.form_submit_button("Confirmar Entrega")

      if submit_entrega:
        if not equipo_financiado or not nombre_cliente:
          st.warning(
              "Por favor, completa la referencia del equipo financiado y los"
              " datos del cliente/celular."
          )
        elif cantidad_entrega > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades"
              " disponibles."
          )
        else:
          inventario[tarjeta_sel] -= cantidad_entrega
          fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

          entregas.append({
              "Fecha/Hora": fecha_hora,
              "Cliente / Celular": nombre_cliente,
              "Equipo Financiado": equipo_financiado,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_entrega,
              "Responsable": responsable_entrega,
          })

          guardar_inventario(inventario)
          guardar_lista("entregas", entregas)

          st.success(
              f"¡Entrega registrada! Tarjeta '{tarjeta_sel}' vinculada al equipo"
              f" '{equipo_financiado}' para {nombre_cliente} guardada con"
              " éxito."
          )

# 5. HISTORIALES Y REGISTROS CON FILTROS
elif menu == "Historiales y Registros":
  st.header("📊 Historiales, Filtros y Auditoría")

  sub_menu = st.radio(
      "Selecciona el historial que deseas ver:",
      [
          "Historial de Entradas (Llegadas)",
          "Historial de Traslados",
          "Historial de Entregas a Clientes",
      ],
  )

  # Controles de filtrado general para los historiales
  st.markdown("---")
  st.subheader("🔍 Filtros de Búsqueda")
  col1, col2 = st.columns(2)

  with col1:
    filtro_texto = st.text_input(
        "Buscar por Responsable, Cliente, Celular o Equipo:"
    ).lower()

  with col2:
    activar_fechas = st.checkbox("Filtrar por rango de fechas")

  fecha_inicio, fecha_fin = None, None
  if activar_fechas:
    c1, c2 = st.columns(2)
    with c1:
      fecha_inicio = st.date_input("Fecha de inicio", datetime.date.today())
    with c2:
      fecha_fin = st.date_input("Fecha de fin", datetime.date.today())

  st.markdown("---")


  def aplicar_filtros(lista_datos, col_fecha):
    if not lista_datos:
      return pd.DataFrame()

    df = pd.DataFrame(lista_datos)

    # Filtro de texto (busca en cualquier columna)
    if filtro_texto:
      mask = df.astype(str).apply(
          lambda x: x.str.lower().str.contains(filtro_texto).any(), axis=1
      )
      df = df[mask]

    # Filtro de fechas
    if activar_fechas and col_fecha in df.columns:
      df["_fecha_temp"] = pd.to_datetime(df[col_fecha]).dt.date
      df = df[
          (df["_fecha_temp"] >= fecha_inicio)
          & (df["_fecha_temp"] <= fecha_fin)
      ]
      df = df.drop(columns=["_fecha_temp"])

    return df


  if sub_menu == "Historial de Entradas (Llegadas)":
    st.subheader("📥 Registro de Llegadas de Tarjetas")
    df_res = aplicar_filtros(entradas, "Fecha de Llegada")
    if df_res.empty:
      st.info("No hay registros que coincidan con los filtros.")
    else:
      st.dataframe(df_res, use_container_width=True)

  elif sub_menu == "Historial de Traslados":
    st.subheader("🚚 Registro de Traslados a Sucursales")
    df_res = aplicar_filtros(traslados, "Fecha/Hora")
    if df_res.empty:
      st.info("No hay registros que coincidan con los filtros.")
    else:
      st.dataframe(df_res, use_container_width=True)

  elif sub_menu == "Historial de Entregas a Clientes":
    st.subheader("👤 Registro de Entregas y Equipos Financiados")
    df_res = aplicar_filtros(entregas, "Fecha/Hora")
    if df_res.empty:
      st.info("No hay registros que coincidan con los filtros.")
    else:
      st.dataframe(df_res, use_container_width=True)
             
