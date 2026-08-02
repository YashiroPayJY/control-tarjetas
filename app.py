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
            
