# ============================================================
# main.py
# punto de entrada de la demo Moodsitto + Durus.
# siembra datos la primera vez y en ejecuciones posteriores
# verifica que los datos persisten en disco.
# ============================================================

from datetime import date, time

from repository import MoodsittoRepo
from models import Emotion, EmotionMedium


def seed(repo: MoodsittoRepo):
    """
    Siembra datos iniciales. devuelve los objetos creados
    para poder reutilizarlos en las demos.
    """
    # --- location (tabla location) ---
    loc = repo.add_location(
        calle="Av. Reforma", colonia="Centro",
        num_ext="123", cp="06000",
        descripcion="Consultorio principal",
    )

    # --- user (tabla users) ---
    uid = repo.register_user(
        name="Ana", lastname1="Garcia", lastname2="Lopez",
        date_b=date(1995, 4, 12),
        phone="5551234567", emer_phone="5559998877",
        mail="ana@gmail.com", passw="secreto123",
        location=loc,
    )

    # --- Emotion central (tabla emocion_central) ---
    alegria = Emotion("Alegria", "Emocion basica positiva", intensidad=8)
    repo.register_emotion(alegria)

    # --- Emotion media (tabla emocion_media) --- HERENCIA
    entusiasmo = EmotionMedium(
        "Entusiasmo", parent=alegria,
        descripcion="Alegria con alta energia", intensidad=9,
    )
    repo.register_emotion(entusiasmo)

    # --- Tracks (tabla trackeo_emo) --- COMPOSICIoN
    user = repo.get_user(uid)
    repo.register_track(user, alegria, date.today(), time(9, 30),
                        "Desayuno en familia")
    repo.register_track(user, entusiasmo, date.today(), time(15, 0),
                        "Termine la tarea de topicos jsjsjsj")

    return uid, alegria, entusiasmo


def main():
    # abrimos el repositorio: si el archivo existe, recupera datos;
    # si no existe, lo crea vacío.
    repo = MoodsittoRepo()

    try:
        # ------- verificación de persistencia -------
        if not repo.list_users():
            print("No hay datos previos: sembrando datos iniciales...\n")
            uid, alegria, entusiasmo = seed(repo)
        else:
            print("datos encontrados en disco (persistencia verificada).\n")
            uid = next(iter(repo.users))
            # recuperamos la emocion central para la demo de polimorfismo
            alegria = next(
                (e for e in repo.emotions.values()
                 if isinstance(e, Emotion) and not isinstance(e, EmotionMedium)),
                None,
            )

        # ------- demos -------
        print("=" * 60)
        print("USUARIOS REGISTRADOS (clases persistentes)")
        print("=" * 60)
        for uid_, s in repo.list_users():
            print(f"  [{uid_}] {s}")

        print("\n" + "=" * 60)
        print("NAVEGACION DEL GRAFO: tracks del usuario")
        print("=" * 60)
        for t in repo.get_tracks_by_user(uid):
            print("  ", t.describe())

        print("\n" + "=" * 60)
        print("POLIMORFISMO: tracks de hijos de la emoción central")
        print("=" * 60)
        if alegria:
            for t in repo.tracks_of_child_of(alegria):
                print("  ", t.describe())
        else:
            print("  (no se encontro emoción central)")

        print("\n" + "=" * 60)
        print("TRANSACCIÓN CON abort()")
        print("=" * 60)
        print("  ", repo.demo_abort())

        print("\n" + "=" * 60)
        print("UPDATE: cambiar telefono del usuario")
        print("=" * 60)
        repo.update_user_phone(uid, "5550001111")
        print("   Nuevo teléfono:", repo.get_user(uid).phone)

        print("\n" + "=" * 60)
        print("DELETE EN CASCADA: eliminar usuario y sus tracks")
        print("=" * 60)
        repo.delete_user(uid)
        print("   Usuarios restantes:", repo.list_users())
        print("   Tracks restantes  :", len(repo.tracks))

    finally:
        repo.close()


if __name__ == "__main__":
    main()