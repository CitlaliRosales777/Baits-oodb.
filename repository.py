# ============================================================
# repository.py
# capa de acceso a datos para Moodsitto con Durus.
#
# caracteristicas cubiertas:
#   #5 persistencia por alcanzabilidad (connection.get_root())
#   #6 transacciones (commit / abort)
#   #7 navegacion del grafo (consultas con referencias directas)
#   #8 CRUD funcional (alta, consulta, update, delete con cascada)
# ============================================================

import logging
import os

# fileStorage: guarda los objetos persistidos en un archivo en disco
from durus.file_storage import FileStorage

# vonnection: maneja la sesión y las transacciones con el storage
from durus.connection import Connection

# persistentdict: diccionario persistente para los contenedores raíz
from durus.persistent_dict import PersistentDict

# importacion de  clases persistente
from models import Location, User, Emotion, EmotionMedium, EmotionTrack

# durus imprime un log INFO en cada commit. estA en WARNING
# para que la consola no se llene de mensajes
logging.getLogger("durus").setLevel(logging.WARNING)


class MoodsittoRepo:
    """
    repositorio que encapsula el storage y la conexión de Durus.
    todos los objetos creados aqui viven en el root y por tanto
    son persistidos automaticamente en cada commit().
    """

    def __init__(self, db_path: str = "data/moodsitto.durus"):
        # creamos el directorio 'data' si no existe
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # se abre o creA el archivo de storage
        self.storage = FileStorage(db_path)

        #se abre una conexión al storage
        self.connection = Connection(self.storage)

        # se obtiene el ROOT (raiz del grafo de objetos)
        #  -todo objeto alcanzable desde aqui
        #    sera persistido por Durus.
        self.root = self.connection.get_root()

        # inicializacion de contenedores PersistentDict si no existen
        #    (esto se ejecuta solo la primera vez)
        for key in ("users", "emotions", "tracks"):
            if key not in self.root:
                self.root[key] = PersistentDict()

        #inicializacion confirmada
        self.connection.commit()

        #atajo de lso contenedores
        self.users = self.root["users"]
        self.emotions = self.root["emotions"]
        self.tracks = self.root["tracks"]

        # se calcula el siguiente ID de cada contenedor.
        #    IMPORTANTE: no se usa un contador en memoria porque
        #    se perdería al reiniciar. se deriva de las claves.
        self._next_id = {
            "users": self._calc_next("users"),
            "emotions": self._calc_next("emotions"),
            "tracks": self._calc_next("tracks"),
        }

    def _calc_next(self, key) -> int:
        """
        devuelve el siguiente ID disponible para un contenedor.
        Corrige el bug del ejemplo base de Auto Repair Shop,
        donde '_next_id' se reiniciaba a 1 en cada arranque.
        """
        d = self.root[key]
        return max(d.keys(), default=0) + 1

    # --------------------------------------------------------
    # Ciclo de vida
    # --------------------------------------------------------
    def close(self):
        """cierra el storage. se hace commit defensivo antes."""
        try:
            self.connection.commit()
        finally:
            self.storage.close()

    # --------------------------------------------------------
    # ALTAS
    # --------------------------------------------------------
    def add_location(self, **kw) -> Location:
        """crea un Location (no lo persiste por si solo, se
        persiste cuando es referenciado desde un User)."""
        return Location(**kw)

    def register_user(self, **kw) -> int:
        """
        alta de un User. Devuelve el id asignado
        hace commit() para demostrar transacciones
        """
        user = User(**kw)
        uid = self._next_id["users"]
        self.users[uid] = user          # queda alcanzable desde root
        self._next_id["users"] += 1
        self.connection.commit()        # confirma transaccion
        return uid

    def register_emotion(self, obj: Emotion) -> int:
        """alta de Emotion o EmotionMedium (polimorfismo)."""
        eid = self._next_id["emotions"]
        self.emotions[eid] = obj
        self._next_id["emotions"] += 1
        self.connection.commit()
        return eid

    def register_track(self, user: User, emotion: Emotion,
                       fecha, hora, contexto) -> int:
        """
        alta de un EmotionTrack.
        - guarda referencias DIRECTAS a user y emotion
        - añade el track también a user.tracks (composición bidireccional)
        """
        track = EmotionTrack(fecha, hora, contexto, user, emotion)
        tid = self._next_id["tracks"]
        self.tracks[tid] = track
        user.tracks.append(track)       # PersistentList: Si detecta el cambio
        self._next_id["tracks"] += 1
        self.connection.commit()
        return tid

    # --------------------------------------------------------
    # CONSULTAS Y NAVEGACION DEL GRAFO
    # --------------------------------------------------------
    def get_user(self, uid) -> User:
        return self.users.get(uid)

    def get_tracks_by_user(self, uid):
        """
        SQL equivalente:
            SELECT * FROM trackeo_emo WHERE id_user = ?;
        En OO navegamos la referencia directa 't.user'.
        """
        user = self.users.get(uid)
        if user is None:
            return []
        return [t for t in self.tracks.values() if t.user is user]

    def get_tracks_by_emotion_name(self, nombre):
        """
        SQL equivalente (join a traves de emocion_conjunto):
            SELECT t.* FROM trackeo_emo t
            JOIN emocion_conjunto ec ON ec.id_emocion_conjun = t.id_emo_conjunto
            JOIN emocion_especifica ee ON ee.id_emo_espe = ec.id_emo_espe
            WHERE ee.nombre = ?;
        En OO basta con acceder a t.emotion.nombre.
        """
        return [t for t in self.tracks.values()
                if t.emotion.nombre == nombre]

    def tracks_of_child_of(self, central: Emotion):
        """
        navegacion polimorfica: devuelve los tracks cuya emocion
        sea una EmotionMedium hija de 'central'.
        """
        return [t for t in self.tracks.values()
                if isinstance(t.emotion, EmotionMedium)
                and t.emotion.parent is central]

    # --------------------------------------------------------
    # TRANSACCIONES
    # --------------------------------------------------------
    def demo_abort(self):
        """
        demuestra que abort() revierte los cambios no confirmados.
        """
        from datetime import date
        ghost = User("Ghost", "Test", date(2000, 1, 1), "555",
                     "ghost@test.com", "password1")
        gid = self._next_id["users"]
        self.users[gid] = ghost
        # nO hacemos commit: en su lugar abortamos
        self.connection.abort()
        # verificamos que el alta no quedó
        assert gid not in self.users, "abort() no revirtió el alta"
        return f"Alta de usuario {gid} revertida con abort(): OK"

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------
    def update_user_phone(self, uid, new_phone):
        u = self.users[uid]
        u.phone = new_phone             # modificacion de atributo
        self.connection.commit()        # persistimos el cambio

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------
    def delete_user(self, uid):
        """
        baja en cascada:
        - elimina todos los EmotionTrack del usuario
        - vacía su PersistentList
        - elimina el User del contenedor
        """
        user = self.users[uid]
        #borrar tracks del usuario
        for tid, t in list(self.tracks.items()):
            if t.user is user:
                del self.tracks[tid]
        # vaciar la lista persistente del usuario
        user.tracks = type(user.tracks)()
        # eliminar el usuario
        del self.users[uid]
        self.connection.commit()

    # --------------------------------------------------------
    # UTILIDADES
    # --------------------------------------------------------
    def list_users(self):
        return [(uid, str(u)) for uid, u in self.users.items()]