datetime, os, io
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
    "novedades": "novedades.csv",
}


def cargar_datos():
  inventario = (
      dict(
          zip(
              pd.read_csv(ARCHIVOS_DATOS["inventario"])["Tipo de Tarjeta"],
              pd.read_csv(ARCHIVOS_DATOS["inventario"])["Cantidad Disponible"],
          )
      )
      if os.path.exists(ARCHIVOS_DATOS["inventario"])
      else {}
  )
  entradas = (
      pd.read_csv(ARCHIVOS_DATOS["entradas"])
      .dropna(how="all")
      .to_dict("records")
      if os.path.exists(ARCHIVOS_DATOS["entradas"])
      else []
  )
  traslados = (
      pd.read_csv(ARCHIVOS_DATOS["traslados"])
      .dropna(how="all")
      .to_dict("records")
      if os.path.exists(ARCHIVOS_DATOS["traslados"])
      else []
  )
  entregas = (
      pd.read_csv(ARCHIVOS_DATOS["entregas"])
      .dropna(how="all")
      .to_dict("records")
      if os.path.exists(ARCHIVOS_DATOS["entregas"])
      else []
  )
  novedades = (
      pd.read_csv(ARCHIVOS_DATOS["novedades"])
      .dropna(how="all")
      .to_dict("records")
      if os.path.exists(ARCHIVOS_DATOS["novedades"])
      else []
  )
  return inventario, entradas, traslados, entregas, novedades


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


# Función para exportar DataFrames a Excel en memoria
def convertir_a_excel(df):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Reporte")
  processed_data = output.getvalue()
  return processed_data


# Cargar datos
inventario, entradas, traslados, entregas, novedades = cargar_datos()

RESPONSABLES = ["Edgardo", "Alexandra", "Yeriz", "Alejandro"]
SUCURSALES = ["Sucursal Principal", "Norte", "Sur", "Centro", "Otra Sucursal"]

st.title("💳 Control de Inventario y Entregas")
st.markdown("Gestión operativa avanzada con panel de administrador.")

# Control de Acceso de Administrador en el Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Acceso Administrador")
es_admin = False
password_ingresada = st.sidebar.text_input(
    "Contraseña Admin", type="password", key="pass_admin"
)
if password_ingresada == "admin123":  # Puedes cambiar la contraseña aquí
  st.sidebar.success("Modo Administrador Activo 🔓")
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
        "Reportar Novedad (Sucursal)",
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
        "Fecha de Llegada", value=datetime.date.today()
    )
    responsable = st.selectbox(
        "Responsable de Ingreso", RESPONSABLES, key="resp_ingreso"
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
      sucursal_destino = st.selectbox(
          "Sucursal de Destino", SUCURSALES
      )
      responsable_salida = st.selectbox(
          "Responsable del Traslado", RESPONSABLES, key="resp_traslado"
      )
      submit_traslado = st.form_submit_button("Confirmar Traslado")

      if submit_traslado:
        if cantidad_traslado > stock_actual:
          st.error(
              f"Stock insuficiente. Solo hay {stock_actual} unidades"
              " disponibles."
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
          guardar_inventario(inventario)
          guardar_lista("traslados", traslados)
          st.success(
              f"¡Traslado exitoso a {sucursal_destino} registrado y guardado!"
          )

# 4. REGISTRAR ENTREGA DE TARJETA CON EQUIPO FINANCIADO
elif menu == "Registrar Entrega a Cliente":
  st.header("👤 Registrar Entrega de Tarjeta y Equipo Financiado")
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
      equipo_financiado = (
          st.text_input(
              "Referencia del Equipo Financiado (Ej: Samsung Galaxy A54)"
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
          st.warning("Completa la referencia del equipo y los datos del cliente.")
        elif cantidad_entrega > stock_actual:
          st.error(f"Stock insuficiente ({stock_actual} disponibles).")
        else:
          inventario[tarjeta_sel] -= cantidad_entrega
          entregas.append({
              "Fecha/Hora": datetime.datetime.now().strftime(
                  "%Y-%m-%d %H:%M"
              ),
              "Cliente / Celular": nombre_cliente,
              "Equipo Financiado": equipo_financiado,
              "Tarjeta": tarjeta_sel,
              "Cantidad": cantidad_entrega,
              "Responsable": responsable_entrega,
          })
          guardar_inventario(inventario)
          guardar_lista("entregas", entregas)
          st.success("¡Entrega registrada y inventario actualizado con éxito!")

# 5. REPORTAR NOVEDAD (SUCURSAL DIFERENTE)
elif menu == "Reportar Novedad (Sucursal)":
  st.header("📢 Cuadro de Novedades por Sucursal")
  st.markdown(
      "Registra incidencias, ajustes o novedades operativas de sucursales."
  )

  with st.form("form_novedad"):
    sucursal_afectada = st.selectbox(
        "Selecciona Sucursal", SUCURSALES, key="nov_suc"
    )
    tipo_novedad = st.selectbox(
        "Tipo de Novedad",
        [
            "Diferencia en inventario físico",
            "Faltante en traslado",
            "Devolución de cliente / anulación",
            "Otro",
        ],
    )
    descripcion = st.text_area("Descripción detallada de la novedad")
    reporta = st.selectbox("Reporta", RESPONSABLES, key="nov_rep")
    submit_nov = st.form_submit_button("Enviar Novedad al Cuadro")

    if submit_nov:
      if not descripcion:
        st.warning("Por favor escribe la descripción de la novedad.")
      else:
        novedades.append({
            "Fecha/Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Sucursal": sucursal_afectada,
            "Tipo Novedad": tipo_novedad,
            "Descripción": descripcion,
            "Reportado Por": reporta,
        })
        guardar_lista("novedades", novedades)
        st.success("¡Novedad registrada correctamente en el cuadro de control!")

# 6. HISTORIALES, FILTROS Y EXCEL (CON OPCIÓN DE BORRAR / DEVOLVER PARA ADMIN)
elif menu == "Historiales y Registros":
  st.header("📊 Historiales, Filtros, Auditoría y Exportación")

  sub_menu = st.radio(
      "Selecciona el registro:",
      [
          "Entradas (Llegadas)",
          "Traslados",
          "Entregas a Clientes (Gestión de Devoluciones)",
          "Cuadro de Novedades",
      ],
  )

  st.markdown("---")
  st.subheader("🔍 Filtros de Búsqueda")
  col1, col2 = st.columns(2)
  with col1:
    filtro_texto = st.text_input("Buscar por palabra clave:").lower()
  with col2:
    activar_fechas = st.checkbox("Filtrar por rango de fechas")

  fecha_inicio, fecha_fin = None, None
  if activar_fechas:
    c1, c2 = st.columns(2)
    with c1:
      fecha_inicio = st.date_input("Fecha inicio", datetime.date.today())
    with c2:
      fecha_fin = st.date_input("Fecha fin", datetime.date.today())

  st.markdown("---")


  def aplicar_filtros(lista_datos, col_fecha):
    if not lista_datos:
      return pd.DataFrame()
    df = pd.DataFrame(lista_datos)
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


  if sub_menu == "Entradas (Llegadas)":
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
          "entradas_tarjetas.xlsx",
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
          "traslados_tarjetas.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

  elif sub_menu == "Entregas a Clientes (Gestión de Devoluciones)":
    st.subheader("👤 Registro de Entregas y Devoluciones")
    df_res = aplicar_filtros(entregas, "Fecha/Hora")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )

    if not df_res.empty:
      excel_data = convertir_a_excel(df_res)
      st.download_button(
          "📥 Descargar Entregas en Excel",
          excel_data,
          "entregas_tarjetas.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

    # OPCIÓN EXCLUSIVA DE ADMINISTRADOR PARA BORRAR / DEVOLVER AL INVENTARIO
    st.markdown("---")
    st.subheader("⚙️ Panel de Devoluciones y Anulación (Admin)")
    if not es_admin:
      st.warning(
          "🔒 Ingresa la contraseña de Administrador en el menú lateral para"
          " poder borrar entregas y devolver stock al inventario."
      )
    else:
      if entregas:
        indices_entregas = [
            f"#{i} - {e['Fecha/Hora']} | {e['Cliente / Celular']} | Tarjeta:"
            f" {e['Tarjeta']} (Cant: {e['Cantidad']})"
            for i, e in enumerate(entregas)
        ]
        entrega_a_borrar = st.selectbox(
            "Selecciona la entrega a eliminar/devolver", indices_entregas
        )

        if st.button("🗑️ Borrar Entrega y Devolver Tarjetas al Inventario"):
          idx = int(entrega_a_borrar.split("#")[1].split(" -")[0])
          item_eliminado = entregas.pop(idx)

          # Devolver stock al inventario
            tarjeta_devuelta = item_eliminado["Tarjeta"]
          cant_devuelta = item_eliminado["Cantidad"]
          inventario[tarjeta_devuelta] = (
              inventario.get(tarjeta_devuelta, 0) + cant_devuelta
          )

          # Guardar cambios
          guardar_inventario(inventario)
          guardar_lista("entregas", entregas)

          st.success(
              f"¡Entrega eliminada con éxito! Se devolvieron {cant_devuelta}"
              f" unidad(es) de '{tarjeta_devuelta}' al inventario."
          )
          st.rerun()

  elif sub_menu == "Cuadro de Novedades":
    st.subheader("📢 Reporte de Novedades de Sucursales")
    df_res = aplicar_filtros(novedades, "Fecha/Hora")
    st.dataframe(
        df_res if not df_res.empty else pd.DataFrame(),
        use_container_width=True,
    )
    if not df_res.empty:
      excel_data = convertir_a_excel(df_res)
      st.download_button(
          "📥 Descargar Novedades en Excel",
          excel_data,
          "novedades_sucursales.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
      
