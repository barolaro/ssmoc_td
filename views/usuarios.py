"""pages/usuarios.py — Gestión de usuarios (admin)"""
import streamlit as st
from auth import (require_admin, load_users, save_users,
                  ESTABLECIMIENTOS, _hash)


def show(header_fn=None):
    require_admin()
    st.title("👥 Gestión de usuarios")

    users = load_users()

    tab1, tab2 = st.tabs(["📋 Lista de usuarios", "➕ Crear / Editar usuario"])

    with tab1:
        st.subheader("Usuarios registrados en la plataforma")
        rows = []
        for uid, u in users.items():
            estab = ESTABLECIMIENTOS.get(u.get("establecimiento"), {})
            rows.append({
                "Usuario": uid,
                "Nombre": u.get("nombre",""),
                "Rol": u.get("rol","").capitalize(),
                "Establecimiento": estab.get("nombre_corto","— Administrador —"),
                "Email": u.get("email",""),
                "Activo": "✅" if u.get("activo") else "❌",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.subheader("Gestión rápida")
        col1, col2 = st.columns(2)
        with col1:
            uid_sel = st.selectbox("Seleccionar usuario", options=list(users.keys()),
                                   format_func=lambda x: f"{x} — {users[x]['nombre']}")
        with col2:
            u_sel = users.get(uid_sel, {})
            activo_actual = u_sel.get("activo", True)
            if st.button(f"{'🔴 Desactivar' if activo_actual else '🟢 Activar'} usuario",
                         use_container_width=True):
                users[uid_sel]["activo"] = not activo_actual
                save_users(users)
                st.success(f"Usuario '{uid_sel}' {'desactivado' if activo_actual else 'activado'}.")
                st.rerun()

        # Reset contraseña
        with st.expander("🔑 Restablecer contraseña"):
            uid_reset = st.selectbox("Usuario", options=list(users.keys()),
                                     format_func=lambda x: f"{x} — {users[x]['nombre']}",
                                     key="uid_reset")
            new_pwd = st.text_input("Nueva contraseña (mínimo 8 caracteres)", type="password", key="new_pwd")
            if st.button("Restablecer contraseña"):
                if len(new_pwd) < 8:
                    st.error("La contraseña debe tener al menos 8 caracteres.")
                else:
                    users[uid_reset]["password_hash"] = _hash(new_pwd)
                    save_users(users)
                    st.success(f"Contraseña restablecida para '{uid_reset}'.")

    with tab2:
        st.subheader("Crear o editar usuario")

        modo = st.radio("Modo", ["Crear nuevo usuario", "Editar usuario existente"], horizontal=True)

        if modo == "Editar usuario existente":
            uid_edit = st.selectbox("Seleccionar usuario a editar",
                                    options=list(users.keys()),
                                    format_func=lambda x: f"{x} — {users[x]['nombre']}",
                                    key="uid_edit")
            u_edit = users.get(uid_edit, {})
        else:
            uid_edit = None
            u_edit = {}

        with st.form("form_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                if modo == "Crear nuevo usuario":
                    nuevo_uid = st.text_input("Nombre de usuario (login)", placeholder="ej: talagante_jefe")
                else:
                    st.text_input("Nombre de usuario", value=uid_edit, disabled=True)
                    nuevo_uid = uid_edit

                nombre = st.text_input("Nombre completo", value=u_edit.get("nombre",""))
                email  = st.text_input("Correo electrónico", value=u_edit.get("email",""))

            with col2:
                rol = st.selectbox("Rol", ["establecimiento","admin"],
                                   index=0 if u_edit.get("rol","establecimiento")=="establecimiento" else 1)

                estab_opciones = {"": "— Solo administrador (sin establecimiento) —"}
                estab_opciones.update({eid: e["nombre_corto"] for eid,e in ESTABLECIMIENTOS.items()})
                estab_sel = st.selectbox("Establecimiento asignado",
                                         options=list(estab_opciones.keys()),
                                         format_func=lambda x: estab_opciones[x],
                                         index=list(estab_opciones.keys()).index(u_edit.get("establecimiento","") or ""))

                pwd_nueva = st.text_input(
                    "Contraseña" + (" (dejar vacío para no cambiar)" if modo=="Editar usuario existente" else ""),
                    type="password",
                )
                activo = st.checkbox("Usuario activo", value=u_edit.get("activo", True))

            submitted = st.form_submit_button(
                "💾 Guardar usuario" if modo=="Editar usuario existente" else "➕ Crear usuario",
                use_container_width=True, type="primary",
            )

            if submitted:
                uid_final = nuevo_uid.strip().lower()
                errores = []
                if not uid_final:
                    errores.append("El nombre de usuario no puede estar vacío.")
                if not nombre.strip():
                    errores.append("El nombre completo es obligatorio.")
                if modo == "Crear nuevo usuario":
                    if uid_final in users:
                        errores.append(f"Ya existe un usuario con el nombre '{uid_final}'.")
                    if not pwd_nueva:
                        errores.append("La contraseña es obligatoria al crear un usuario.")

                if errores:
                    for e in errores: st.error(e)
                else:
                    if modo == "Crear nuevo usuario" or uid_final not in users:
                        users[uid_final] = {}
                    users[uid_final].update({
                        "nombre": nombre.strip(),
                        "rol": rol,
                        "email": email.strip(),
                        "establecimiento": estab_sel or None,
                        "activo": activo,
                    })
                    if pwd_nueva:
                        users[uid_final]["password_hash"] = _hash(pwd_nueva)
                    save_users(users)
                    st.success(f"✅ Usuario '{uid_final}' {'creado' if modo=='Crear nuevo usuario' else 'actualizado'} correctamente.")
                    st.rerun()

    with st.expander("📋 Credenciales por defecto (referencia)"):
        st.markdown("""
        | Usuario | Contraseña | Rol | Establecimiento |
        |---------|-----------|-----|-----------------|
        | `admin` | `Admin2026*` | Administrador | — |
        | `bayron` | `Ssmoc2026*` | Administrador | — |
        | `traumatologico` | `Trauma2026*` | Establecimiento | Inst. Traumatológico |
        | `direccion` | `Dir2026*` | Establecimiento | Dir. SSMOC |
        | `felix_bulnes` | `Felix2026*` | Establecimiento | H. Félix Bulnes |
        | `san_juan` | `Sjd2026*` | Establecimiento | H. San Juan de Dios |
        | `crs_allende` | `Crs2026*` | Establecimiento | CRS Salvador Allende |
        | `melipilla` | `Meli2026*` | Establecimiento | H. Melipilla |
        | `penaflor` | `Pen2026*` | Establecimiento | H. Peñaflor |
        | `curacavi` | `Cura2026*` | Establecimiento | H. Curacaví |
        | `talagante` | `Tala2026*` | Establecimiento | H. Talagante |

        > ⚠️ Cambie las contraseñas por defecto antes de desplegar en producción.
        """)
