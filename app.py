import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Control de Tarjetas de Crédito",
    page_icon="💳",
    layout="centered",
)


# Función para conectar a Google Sheets usando los Secrets
def conectar_gsheets():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  # Cargamos las credenciales desde los Secrets de Streamlit
  creds_dict = {
      "type": "service_account",
      "project_id": st.secrets["google_sheets"]["project_id"],
      "private_key_id": "dummy_key_id",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3...-----END PRIVATE KEY-----\n",  # Se maneja por partes o directo desde secrets si se desea
      "client_email": st.secrets["google_sheets"]["client_email"],
  }
  # Una forma más directa usando directamente el secret global si lo configuraste completo,
  # pero usaremos gspread con credenciales seguras de st.secrets:
  creds = ServiceAccountCredentials.from_json_keyfile_dict(
      dict(st.secrets["gcp_service_account"]), scope
  )
  client = gspread.authorize(creds)
  sheet = client.open(st.secrets["google_sheets"]["sheet_name"])
  return sheet


# Método alternativo seguro con st.secrets de gcp_service_account
@st.cache_resource
def get_sheets_client():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  creds = ServiceAccountCredentials.from_json_keyfile_dict(
      dict(st.secrets["gcp_service_account"]), scope
  )
  client = gspread.authorize(creds)
  return client


try:
  client = get_sheets_client()
  db = client.open(st.secrets["google_sheets"]["sheet_name"])


  def leer_hoja(nombre_pestania):
    try:
      ws = db.worksheet(nombre_pestania)
      data = ws.get_all_records()
      return pd.DataFrame(data)
    except:
      return pd.DataFrame()


  def guardar_hoja(nombre_pestania, df):
    try:
      ws = db.worksheet(nombre_pestania)
    except:
      ws = db.add_worksheet(title=nombre_pestania, rows="100", cols="20")
    ws.clear()
    if not df.empty:
      ws.update(
          [df.columns.values.tolist()] + df.values.tolist()
      )  # type: ignore[attr-defined]


  # Cargar datos
  df_inv = leer_hoja("Inventario")
  if not df_inv.empty and "Tipo de Tarjeta" in df_inv.columns:
    inventario = dict(
        zip(df_inv["Tipo de Tarjeta"], df_inv["Cantidad Disponible"])
    )
  else:
    inventario = {}

  df_ent = leer_hoja("Entradas")
  entradas = df_ent.to_dict("records") if not df_ent.empty else []

  df_tras = leer_hoja("Traslados")
  traslados = df_tras.to_dict("records") if not df_tras.empty else []

  df_cli = leer_hoja("Entregas")
  entregas = df_cli.to_dict("records") if not df_cli.empty else []

except Exception as e:
  st.error(
      "Error al conectar con Google Sheets. Revisa tus Secrets en la"
      f" configuración. Detalle: {e}"
  )
  inventario, entradas, traslados, entregas = {}, [], [], []

RESPONSABLES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro"]

st.title("💳 Control de Inventario y Entregas de Tarjetas")
st.markdown("Gestión sincronizada con Google Drive de forma permanente.")

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

if menu == "Ver Inventario":
  st.header("📋 Inventario Actual de Tarjetas")
  if not inventario:
    st.info("No hay tarjetas registradas en el inventario.")
  else:
    df_inv_view = pd.DataFrame(
        list(inventario.items()),
        columns=["Tipo de Tarjeta", "Cantidad Disponible"],
    )
    st.dataframe(df_inv_view, use_container_width=True)

elif menu == "Ingresar Lote (Inventario)":
  st.header("➕ Ingresar Tarjetas al Inventario")
  with st.form("form_ingreso"):
    tipo_tarjeta = (
        st.text_input("Tipo / Nombre de Tarjeta (Ej: Visa Clásica)")
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
        "Responsable de Ingreso", RESPONSABLES, key="resp_ing"
    )
    submit_ingreso = st.form_submit_button("Guardar Ingreso")

    if submit_ingreso:
      if tipo_tarjeta:
        inventario[tipo_tarjeta] = inventario.get(tipo_tarjeta, 0) + cantidad
        entradas.append({
            "Fecha Registro": datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "Fecha de Llegada": str(fecha_llegada),
            "Tarjeta": tipo_tarjeta,
            "Cantidad": cantidad,
            "Responsable": responsable,
        })
        guardar_hoja(
            "Inventario",
            pd.DataFrame(
                list(inventario.items()),
                columns=["Tipo de Tarjeta", "Cantidad Disponible"],
            ),
        )
        guardar_hoja("Entradas", pd.DataFrame(entradas))
        st.success(
            f"¡Ingresado y guardado en Google Drive con éxito!"
        )
      else:
        st.warning("Ingresa el tipo de tarjeta.")

elif menu == "Traslado a Sucursal":
  st.header("🚚 Traslado de Tarjetas a Otra Sucursal")
  if not inventario:
    st.warning("No hay inventario disponible.")
  else:
    with st.form("form_traslado"):
      tarjeta_sel = st.selectbox("Selecciona la Tarjeta", list(inventario.keys()))
      stock_actual = inventario[tarjeta_sel]
      st.write(f"Stock disponible: **{stock_actual}**")
      cantidad_traslado = st.number_input(
          "Cantidad a Trasladar", min_value=1, step=1, value=1
      )
      sucursal_destino = (
          st.text_input("Sucursal de Destino").strip().title()
      )
      responsable_salida = st.selectbox(
          "Responsable del Traslado", RESPONSABLES, key="resp_tras"
      )
      submit_traslado = st.form_submit_button("Confirmar Traslado")

      if submit_traslado:
        if not sucursal_destino:
          st.warning("Indica la sucursal de destino.")
        elif cantidad_traslado > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades disponibles."
          )
        else:
          inventario[tarjeta_sel] -= cantidad_traslado
          traslados.append({
              "Fecha/Hora": datetime.datetime.now().strftime(
                  "%Y-%m-%d %H:%M"
              ),
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_traslado,
              "Sucursal Destino": sucursal_destino,
              "Responsable": responsable_salida,
          })
          guardar_hoja(
              "Inventario",
              pd.DataFrame(
                  list(inventario.items()),
                  columns=["Tipo de Tarjeta", "Cantidad Disponible"],
              ),
          )
          guardar_hoja("Traslados", pd.DataFrame(traslados))
          st.success("¡Traslado registrado y guardado en Google Drive!")

elif menu == "Registrar Entrega a Cliente":
  st.header("👤 Registrar Entrega a Cliente")
  if not inventario:
    st.warning("No hay inventario disponible.")
  else:
    with st.form("form_entrega"):
      tarjeta_sel = st.selectbox(
          "Selecciona la Tarjeta", list(inventario.keys()), key="sel_e"
      )
      stock_actual = inventario[tarjeta_sel]
      st.write(f"Stock disponible: **{stock_actual}**")
      cantidad_entrega = st.number_input(
          "Cantidad Entregada", min_value=1, step=1, value=1, key="cant_e"
      )
      nombre_cliente = (
          st.text_input("Nombre del Cliente").strip().title()
      )
      responsable_entrega = st.selectbox(
          "Responsable de Entrega", RESPONSABLES, key="resp_e"
      )
      submit_entrega = st.form_submit_button("Confirmar Entrega")

      if submit_entrega:
        if not nombre_cliente:
          st.warning("Ingresa el nombre del cliente.")
        elif cantidad_entrega > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades disponibles."
          )
        else:
          inventario[tarjeta_sel] -= cantidad_entrega
          entregas.append({
              "Fecha/Hora": datetime.datetime.now().strftime(
                  "%Y-%m-%d %H:%M"
              ),
              "Cliente": nombre_cliente,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_entrega,
              "Responsable": responsable_entrega,
          })
          guardar_hoja(
              "Inventario",
              pd.DataFrame(
                  list(inventario.items()),
                  columns=["Tipo de Tarjeta", "Cantidad Disponible"],
              ),
          )
          guardar_hoja("Entregas", pd.DataFrame(entregas))
          st.success("¡Entrega registrada y guardada permanentemente!")

elif menu == "Historiales y Registros":
  st.header("📊 Historiales y Auditoría")
  sub_menu = st.radio(
      "Selecciona:",
      ["Entradas", "Traslados", "Entregas a Clientes"],
  )
  if sub_menu == "Entradas":
    st.dataframe(
        pd.DataFrame(entradas) if entradas else pd.DataFrame(),
        use_container_width=True,
    )
  elif sub_menu == "Traslados":
    st.dataframe(
        pd.DataFrame(traslados) if traslados else pd.DataFrame(),
        use_container_width=True,
    )
  elif sub_menu == "Entregas a Clientes":
    st.dataframe(
        pd.DataFrame(entregas) if entregas else pd.DataFrame(),
        use_container_width=True,
)
      
