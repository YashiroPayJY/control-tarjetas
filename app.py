import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración inicial de la página
st.set_page_config(
    page_title="Control de Tarjetas de Crédito",
    page_icon="💳",
    layout="centered",
)

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos desde Google Sheets (o inicializar si está vacío)
try:
  df_inv_Rem = conn.read(worksheet="Inventario", ttl=0)
  if df_inv_Rem.empty:
    inventario = {}
  else:
    inventario = dict(
        zip(df_inv_Rem["Tipo de Tarjeta"], df_inv_Rem["Cantidad Disponible"])
    )
except:
  inventario = {}

try:
  entradas = conn.read(worksheet="Entradas", ttl=0).dropna(how="all").to_dict("records")
except:
  entradas = []

try:
  traslados = conn.read(worksheet="Traslados", ttl=0).dropna(how="all").to_dict("records")
except:
  traslados = []

try:
  entregas = conn.read(worksheet="Entregas", ttl=0).dropna(how="all").to_dict("records")
except:
  entregas = []

RESPONSABLES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro"]

st.title("💳 Control de Inventario y Entregas de Tarjetas")
st.markdown("Gestión de stock, traslados y entregas (Guardado Permanente).")

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

        # Actualizar Google Sheets
        conn.update(
            worksheet="Inventario",
            data=pd.DataFrame(
                list(inventario.items()),
                columns=["Tipo de Tarjeta", "Cantidad Disponible"],
            ),
        )
        conn.update(worksheet="Entradas", data=pd.DataFrame(entradas))

        st.success(
            f"¡Se ingresaron {cantidad} tarjetas de '{tipo_tarjeta}' y se guardó"
            " en Google Drive!"
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

          conn.update(
              worksheet="Inventario",
              data=pd.DataFrame(
                  list(inventario.items()),
                  columns=["Tipo de Tarjeta", "Cantidad Disponible"],
              ),
          )
          conn.update(worksheet="Traslados", data=pd.DataFrame(traslados))

          st.success(
              f"¡Traslado exitoso y guardado en Google Sheets!"
          )

# 4. REGISTRAR ENTREGA A CLIENTE
elif menu == "Registrar Entrega a Cliente":
  st.header("👤 Registrar Entrega a Cliente")

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
      nombre_cliente = (
          st.text_input("Nombre del Cliente / Beneficiario").strip().title()
      )
      responsable_entrega = st.selectbox(
          "Responsable de la Entrega", RESPONSABLES, key="resp_entrega"
      )

      submit_entrega = st.form_submit_button("Confirmar Entrega a Cliente")

      if submit_entrega:
        if not nombre_cliente:
          st.warning("Por favor, ingresa el nombre del cliente.")
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
              "Cliente": nombre_cliente,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_entrega,
              "Responsable": responsable_entrega,
          })

          conn.update(
              worksheet="Inventario",
              data=pd.DataFrame(
                  list(inventario.items()),
                  columns=["Tipo de Tarjeta", "Cantidad Disponible"],
              ),
          )
          conn.update(worksheet="Entregas", data=pd.DataFrame(entregas))

          st.success(
              f"¡Entrega registrada y guardada permanentemente en Google Sheets!"
          )

# 5. HISTORIALES Y REGISTROS
elif menu == "Historiales y Registros":
  st.header("📊 Historiales y Auditoría")

  sub_menu = st.radio(
      "Selecciona el historial que deseas ver:",
      [
          "Historial de Entradas (Llegadas)",
          "Historial de Traslados",
          "Historial de Entregas a Clientes",
      ],
  )

  if sub_menu == "Historial de Entradas (Llegadas)":
    st.subheader("📥 Registro de Llegadas de Tarjetas")
    if not entradas:
      st.info("No hay registros de entradas.")
    else:
      st.dataframe(pd.DataFrame(entradas), use_container_width=True)

  elif sub_menu == "Historial de Traslados":
    st.subheader("🚚 Registro de Traslados a Sucursales")
    if not traslados:
      st.info("No hay registros de traslados.")
    else:
      st.dataframe(pd.DataFrame(traslados), use_container_width=True)

  elif sub_menu == "Historial de Entregas a Clientes":
    st.subheader("👤 Registro de Entregas a Clientes")
    if not entregas:
      st.info("No hay registros de entregas a clientes.")
    else:
      st.dataframe(pd.DataFrame(entregas), use_container_width=True)
            
