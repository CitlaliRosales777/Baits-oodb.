# ============================================================
# crud_interactivo.py
#
# permite al usuario:
# -crear usuarios, emociones y tracks emocionales
# -listar usuarios, emociones y tracks
# -actualizar el teléfono de un usuario
# -eliminar un usuario (con borrado en cascada de sus tracks)
#
# se ejecuta con:
#   python crud_interactivo.py
# ============================================================

from datetime import date, time, datetime

from repository import MoodsittoRepo
from models import Emotion, EmotionMedium


# ------------------------------------------------------------
# utilidades de entrada
# ------------------------------------------------------------
def pedir(texto, default=None, obligatorio=False):
    """pide un valor por consola. si hay default, lo usa al presionar enter."""
    while True:
        entrada = input(f"{texto}" + (f" [{default}]" if default else "") + ": ").strip()
        if not entrada:
            if default is not None:
                return default
            if obligatorio:
                print("este campo es obligatorio.")
                continue
            return ""
        return entrada


def pedir_entero(texto, minimo=None, maximo=None):
    """pide un entero valido, opcionalmente en un rango."""
    while True:
        try:
            v = int(input(f"{texto}: ").strip())
            if minimo is not None and v < minimo:
                print(f"debe ser >= {minimo}.")
                continue
            if maximo is not None and v > maximo:
                print(f"debe ser <= {maximo}.")
                continue
            return v
        except ValueError:
            print("ingresa un numero entero valido.")


def pedir_fecha(texto, default=None):
    """pide una fecha en formato YYYY-MM-DD."""
    while True:
        raw = input(f"{texto}" + (f" [{default}]" if default else "") + " (YYYY-MM-DD): ").strip()
        if not raw and default:
            return default
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("formato erroneo. Usa YYYY-MM-DD.")


def pedir_hora(texto, default=None):
    """pide una hora en formato HH:MM."""
    while True:
        raw = input(f"{texto}" + (f" [{default}]" if default else "") + " (HH:MM): ").strip()
        if not raw and default:
            return default
        try:
            return datetime.strptime(raw, "%H:%M").time()
        except ValueError:
            print("formato erroneo. Usa HH:MM.")


def pausa():
    input("\nPresiona Enter para continuar...")


def separador(titulo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


# ------------------------------------------------------------
# Operaciones CRUD
# ------------------------------------------------------------
def crear_usuario(repo: MoodsittoRepo):
    separador("CREAR USUARIO")
    calle = pedir("Calle", obligatorio=True)
    colonia = pedir("Colonia", obligatorio=True)
    num_ext = pedir("Número exterior", "S/N")
    cp = pedir("Código postal", "00000")

    loc = repo.add_location(calle=calle, colonia=colonia,
                            num_ext=num_ext, cp=cp)

    name = pedir("Nombre", obligatorio=True)
    lastname1 = pedir("Apellido paterno", obligatorio=True)
    lastname2 = pedir("Apellido materno")
    fecha_nac = pedir_fecha("Fecha de nacimiento")
    phone = pedir("Teléfono", obligatorio=True)
    emer = pedir("Teléfono de emergencia")
    mail = pedir("Correo", obligatorio=True)
    passw = pedir("Contraseña (mín. 8 caracteres)", obligatorio=True)

    try:
        uid = repo.register_user(
            name=name, lastname1=lastname1, lastname2=lastname2,
            date_b=fecha_nac, phone=phone, emer_phone=emer,
            mail=mail, passw=passw, location=loc,
        )
        print(f"\nusuario creado con id={uid}")
    except ValueError as e:
        print(f"\nerror de validación: {e}")


def crear_emocion(repo: MoodsittoRepo):
    separador("CREAR EMOCION")
    print("1) Emocion central (Emotion)")
    print("2) Emocion media   (EmotionMedium)")
    tipo = pedir("elige tipo", "1")

    nombre = pedir("nombre de la emocipn", obligatorio=True)
    desc = pedir("Descripcion")
    intensidad = pedir_entero("intensidad (1-10)", 1, 10)

    if tipo == "2":
        # Pedimos a que emoción central pertenece
        centrales = [(i, e) for i, e in repo.emotions.items()
                     if not isinstance(e, EmotionMedium)]
        if not centrales:
            print("\nno hay emociones centrales. crea una primero.")
            return
        print("\nemociones centrales disponibles:")
        for i, e in centrales:
            print(f"  [{i}] {e.nombre}")
        pid = pedir_entero("ID de la emocion central padre")
        parent = repo.emotions.get(pid)
        if parent is None or isinstance(parent, EmotionMedium):
            print("\nID invalido.")
            return
        emo = EmotionMedium(nombre, parent=parent,
                            descripcion=desc, intensidad=intensidad)
    else:
        emo = Emotion(nombre, descripcion=desc, intensidad=intensidad)

    eid = repo.register_emotion(emo)
    print(f"\nEmocion creada con id={eid}")


def crear_track(repo: MoodsittoRepo):
    separador("CREAR TRACK EMOCIONAL")
    if not repo.users:
        print("No hay usuarios. Crea uno primero.")
        return
    if not repo.emotions:
        print("No hay emociones. Crea una primero.")
        return

    print("\nUsuarios disponibles:")
    for uid, u in repo.users.items():
        print(f"  [{uid}] {u}")

    uid = pedir_entero("ID del usuario")
    user = repo.get_user(uid)
    if user is None:
        print("\nisuario no encontrado.")
        return

    print("\nEmociones disponibles:")
    for eid, e in repo.emotions.items():
        print(f"  [{eid}] {e.nombre} (intensidad {e.intensidad})")

    eid = pedir_entero("ID de la emocion")
    emo = repo.emotions.get(eid)
    if emo is None:
        print("\nEmocion no encontrada.")
        return

    fecha = pedir_fecha("Fecha", default=date.today().isoformat())
    hora = pedir_hora("Hora", default="12:00")
    contexto = pedir("Contexto / nota")

    tid = repo.register_track(user, emo, fecha, hora, contexto)
    print(f"\nTrack creado con id={tid}")


def listar_usuarios(repo: MoodsittoRepo):
    separador("USUARIOS")
    if not repo.users:
        print("(sin usuarios)")
        return
    for uid, u in repo.users.items():
        print(f"  [{uid}] {u} | tel: {u.phone} | dir: {u.location}")


def listar_emociones(repo: MoodsittoRepo):
    separador("EMOCIONES")
    if not repo.emotions:
        print("(sin emociones)")
        return
    for eid, e in repo.emotions.items():
        print(f"  [{eid}] {e.describe()}")


def listar_tracks(repo: MoodsittoRepo):
    separador("TRACKS EMOCIONALES")
    if not repo.tracks:
        print("(sin tracks)")
        return
    for tid, t in repo.tracks.items():
        print(f"  [{tid}] {t.describe()}")

def eliminar_usuario(repo: MoodsittoRepo):
    separador("ELIMINAR USUARIO (con cascada de tracks)")
    if not repo.users:
        print("(sin usuarios)")
        return
    for uid, u in repo.users.items():
        print(f"  [{uid}] {u}")
    uid = pedir_entero("ID del usuario a eliminar")
    if uid not in repo.users:
        print("\nusuario no encontrado.")
        return
    confirm = pedir(f"¿Seguro que deseas eliminar al usuario {uid}? (s/n)", "n")
    if confirm.lower() != "s":
        print("Operación cancelada.")
        return
    repo.delete_user(uid)
    print(f"\nusuario {uid} eliminado (junto con sus tracks).")


# ------------------------------------------------------------
# menu
# ------------------------------------------------------------
def menu():
    repo = MoodsittoRepo()
    try:
        while True:
            print("\n" + "=" * 60)
            print("  MOODSITTO")
            print("=" * 60)
            print("  1) Crear usuario")
            print("  2) Crear emoción")
            print("  3) Crear track emocional")
            print("  4) Listar usuarios")
            print("  5) Listar emociones")
            print("  6) Listar tracks")
            print("  7) Eliminar Usuario")
            print("  0) Salir")
            print("=" * 60)

            opcion = pedir("Elige una opción", "0")

            if opcion == "1":
                crear_usuario(repo)
            elif opcion == "2":
                crear_emocion(repo)
            elif opcion == "3":
                crear_track(repo)
            elif opcion == "4":
                listar_usuarios(repo)
            elif opcion == "5":
                listar_emociones(repo)
            elif opcion == "6":
                listar_tracks(repo)
            elif opcion == "7":
                eliminar_usuario(repo)
            elif opcion == "0":
                print("\nsaliendo... Los datos estan guardados en data/moodsitto.durus")
                break
            else:
                print("opcion invalida.")

            pausa()
    finally:
        repo.close()


if __name__ == "__main__":
    menu()