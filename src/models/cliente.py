class Cliente:
    def __init__(self, codigo, nombre=None, sexo=None, fecha_nacimiento=None, tipo_documento=None):
        self.codigo = codigo
        self.nombre = nombre
        self.sexo = sexo
        self.fecha_nacimiento = fecha_nacimiento
        self.tipo_documento = tipo_documento
