#========
# Models.py
#
# Modelo de datos persistentes de Moodsitto con Durus
#
# Tablas utilizadas de Moodsitto:
# 
# Users = User (Persistente)
# locations = Location (Persistente)
# emocion_central = Emotion (Persistente y supperclase)
# emocion_media = emocionMedium (emocion y subclase)
# trackeo_emocion = EmotionTrack(Peristente y compuesta)
# 
# Caractetisticas de la tabla 2 que son cubiertas:
# -clase persistente
# -encapsulamiento y abstraccion
# -herencia y polimorfismo
# -objetos compplejos
# =================='0'0'
# 
# Persistentes: clase base de durus, toda subclase se guarda
# automaticamente en el almacenamiento cuando es alcanzable desde el root 
from durus.persistent import Persistent

#peristentlist: igual que la lista de python pero en durus
#en esta seccion es donde se hace enfasis la nota tecnica del documento de la parte practica
#Si se detecta u cambio cuando se modifica. No se debe de usar list() nativo dentro del objeto que sea persistente
# de lo contrario Durus no detectara el cambio 
from durus.persistent_list import PersistentList


#---
#Location

class Location(Persistent):
    """
    Direccion del usuario o del doctor.
    CLase persistente independiente: que se podra referenciar
    desde user o otras entidades
    """

    def __init__(self, calle="", colonia="", num_ext="", cp="",
                num_int="", descripcion=""):
        #todos los atributos se guardaran en automatico cuando el objeto sea alcanzable en el root)
        self.calle= calle
        self.colonia= colonia
        self.num_ext= num_ext
        self.cp= cp
        self.num_int= num_int
        self.descripcion= descripcion

    def __str__(self):
        #Pa imprimir en la consola
        return f"{self.calle}{self.num_ext},{self.colonia}, CP: {self.cp}"

#------------------------------{}
#tabla de ususuarios: Users
#usa encapsulamiento
#atributos se protegen con _
#setters con validaciones
#properties para solo lectura

class User(Persistent):

    def __init__(self, name, lastname1, date_b, phone, mail, passw,
                 lastname2="", emer_phone="", location=None):
        # inicializacion de datos protegidos a None y luego pasamos por
        # los setters para que las validaciones se apliquen siempre.
        self._name = None
        self._mail = None
        self._passw = None

        self.set_name(name)          # valida el nombre
        self.lastname1 = lastname1
        self.lastname2 = lastname2
        self.date_b = date_b
        self.phone = phone
        self.emer_phone = emer_phone  

        self.set_mail(mail)
        self.set_passw(passw)

        # referencia DIRECTA a Location (no un id_location)
        self.location = location

        # persistentList vacía: aquí se iran agregando los
        # EmotionTrack del usuario (composición bidireccional).
        self.tracks = PersistentList()

    #---encapsulamiento: setters con validacion-------__
    def set_name(self, name):
        if not name or len(name.strip())<2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        self._name=name.strip()

    def set_mail(self, mail):
        #validacion en donde debe de haber @ y un . despues del @
        if "@" not in mail or "." not in mail.split("@")[-1]:
            raise ValueError("Formato de correo invalido")
        self._mail=mail.lower()

    def set_passw(self, passw):
        if len(passw)<6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        #en produccion se va a guardar en hash
        #pero como no se como se hace aqui finjiremos demencia y haremos como que si se guardo en hash

        self._passw= f"Hash::{passw} "

    #Propiedades de solo lectura (abstraccion)
    @property
    def name(self):
        return self._name
    
    @property
    def mail(self):
        return self._mail

    def __str__(self):
        return f"{self.name} {self.lastname1} <{self.mail}"

#-----.-.--------------------------
#Emotion =emocion_central
#superclase de las jerarquias
#chambea con Herencia
class Emotion(Persistent):

    def __init__(self, nombre, descripcion="", intensidad=5):
        self.nombre=nombre
        self.descripcion=descripcion
        #en sql intensidad es una fk a tabla intensidad
        #se simplifica a un entero de 1 a 10
        self.intensidad=intensidad

    def describe(self) -> str:
        """
        metodo que las subclases sobrecribiran
        al ser llamdo de Emotiontrack se invoca por poliformismo
        """
        return f"[Emocion central]{self.nombre}(intensidad {self.intensidad})"

#-----------------------------
#EmocionMedium= emocion_media
#hereda de emotion: poliformismo al sobrescribir el metodo describe
#..........

class EmotionMedium(Emotion):

    def __init__(self, nombre, parent: Emotion, descripcion="", intensidad=5):
        # super().__init__ corrobora que se ejecute la inicialización
        # de la clase base (nombre, descripcion, intensidad)
        super().__init__(nombre, descripcion, intensidad)

        # referencia directa a la emoción central a la que pertenece
        self.parent = parent

    def describe(self) -> str:
        # Sobrescribe el método del padre (polimorfismo)
        return (f"[Emoción media] {self.nombre} "
                f"→ pertenece a '{self.parent.nombre}' "
                f"(intensidad {self.intensidad})")

#-----------------------------
#emotiontrack = trackeo_emocion
#referencias directas 
#------
class EmotionTrack(Persistent):

    def __init__(self, fecha, hora, contexto, user: User, emotion: Emotion):
        # validamos tipos para reforzar la abstracción
        if not isinstance(user, User):
            raise TypeError("user debe ser un objeto User")
        if not isinstance(emotion, Emotion):
            raise TypeError("emotion debe ser un objeto Emotion")

        self.fecha = fecha           # datetime.date
        self.hora = hora             # datetime.time
        self.contexto = contexto

        # referencia directa al objeto User (no id_user)
        self.user = user

        # referencia directa al objeto Emotion
        # (puede ser Emotion o EmotionMedium indistintamente)
        self.emotion = emotion

    def describe(self):
        # aqui se ve el polimorfismo: self.emotion.describe() ejecuta
        # la versión de Emotion o la de EmotionMedium segun corresponda
        return (f"{self.fecha} {self.hora} — {self.user.name}: "
                f"{self.emotion.describe()} | {self.contexto}")