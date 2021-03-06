"""
Versión recontrabeta del script que analiza las actas de la Asamblea Legislativa.

No me gusta así que ya lo estoy refactoreando, pero lo subo para ir compartiendo.

¿Comentarios, sugerencias, madrazos? (no mejor madrazos no)
asambleaabiertacr[arroba]gmail[punto]com
"""

import re
import os
import sys
import difflib
import pdftotext


# ESTRUCTURA DE DATOS DE DIPUTADOS

# No me odien porque empieza en 1 y no en 0, fue culpa de MySQL :\
# Esto tiene que cambiarse para consultarlo de la DB usando una clase ORM

DIPS = {
    1: {'nombres': 'Pablo Heriberto', 'apellidos': 'Abarca Mora'},
    2: {'nombres': 'Ivonne', 'apellidos': 'Acuña Cabrera'},
    3: {'nombres': 'Luis Antonio', 'apellidos': 'Aiza Campos'},
    4: {'nombres': 'Ignacio Alberto', 'apellidos': 'Alpízar Castro'},
    5: {'nombres': 'Mileidy', 'apellidos': 'Alvarado Arias'},
    6: {'nombres': 'Carlos Luis', 'apellidos': 'Avendaño Calvo'},
    7: {'nombres': 'Marolin Raquel', 'apellidos': 'Azofeifa Trejos'},
    8: {'nombres': 'Carlos Ricardo', 'apellidos': 'Benavides Jiménez'},
    9: {'nombres': 'Luis Ramón', 'apellidos': 'Carranza Cascante'},
    10: {'nombres': 'Oscar Mauricio', 'apellidos': 'Cascante Cascante'},
    11: {'nombres': 'Mario Eduardo', 'apellidos': 'Castillo Melendez'},
    12: {'nombres': 'Nidia Lorena', 'apellidos': 'Céspedes Cisneros'},
    13: {'nombres': 'Luis Fernando', 'apellidos': 'Chacón Monge'},
    14: {'nombres': 'Carmen Irene', 'apellidos': 'Chan Mora'},
    15: {'nombres': 'María José', 'apellidos': 'Corrales Chacón'},
    16: {'nombres': 'Eduardo Newton', 'apellidos': 'Cruickshank Smith'},
    17: {'nombres': 'Ana Lucía', 'apellidos': 'Delgado Orozco'},
    18: {'nombres': 'Dragos', 'apellidos': 'Dolanescu Valenciano'},
    19: {'nombres': 'Shirley', 'apellidos': 'Díaz Mejías'},
    20: {'nombres': 'Jorge Luis', 'apellidos': 'Fonseca Fonseca'},
    21: {'nombres': 'David Hubert', 'apellidos': 'Gourzong Cerdas'},
    22: {'nombres': 'Laura', 'apellidos': 'Guido Pérez'},
    23: {'nombres': 'Giovanni Alberto', 'apellidos': 'Gómez Obando'},
    24: {'nombres': 'Silvia', 'apellidos': 'Hernández Sánchez'},
    25: {'nombres': 'Carolina', 'apellidos': 'Hidalgo Herrera'},
    26: {'nombres': 'Harllan', 'apellidos': 'Hoepelman Páez'},
    27: {'nombres': 'Wagner', 'apellidos': 'Jiménez Zúñiga'},
    28: {'nombres': 'Yorleny', 'apellidos': 'León Marchena'},
    29: {'nombres': 'Erwen Yanan', 'apellidos': 'Masís Castro'},
    30: {'nombres': 'María Vita', 'apellidos': 'Monge Granados'},
    31: {'nombres': 'Catalina', 'apellidos': 'Montero Gómez'},
    32: {'nombres': 'Aida María', 'apellidos': 'Montiel Héctor'},
    33: {'nombres': 'Víctor Manuel', 'apellidos': 'Morales Mora'},
    34: {'nombres': 'Walter', 'apellidos': 'Muñoz Céspedes'},
    35: {'nombres': 'Pedro Miguel', 'apellidos': 'Muñoz Fonseca'},
    36: {'nombres': 'Franggi', 'apellidos': 'Nicolás Solano'},
    37: {'nombres': 'Ana Karine', 'apellidos': 'Niño Gutiérrez'},
    38: {'nombres': 'Melvin Ángel', 'apellidos': 'Nuñez Piña'},
    39: {'nombres': 'Rodolfo Rodrigo', 'apellidos': 'Peña Flores'},
    40: {'nombres': 'Jonathan', 'apellidos': 'Prendas Rodríguez'},
    41: {'nombres': 'Nielsen', 'apellidos': 'Pérez Pérez'},
    42: {'nombres': 'Welmer', 'apellidos': 'Ramos González'},
    43: {'nombres': 'Xiomara Priscilla', 'apellidos': 'Rodríguez Hernández'},
    44: {'nombres': 'Erick', 'apellidos': 'Rodríguez Steller'},
    45: {'nombres': 'Aracelly', 'apellidos': 'Salas Eduarte'},
    46: {'nombres': 'Floria', 'apellidos': 'Segreda Sagot'},
    47: {'nombres': 'María Inés', 'apellidos': 'Solís Quirós'},
    48: {'nombres': 'Enrique', 'apellidos': 'Sánchez Carballo'},
    49: {'nombres': 'Roberto Hernán', 'apellidos': 'Thompson Chacón'},
    50: {'nombres': 'Daniel Isaac', 'apellidos': 'Ulate Valenciano'},
    51: {'nombres': 'Paola', 'apellidos': 'Valladares Rosado'},
    52: {'nombres': 'Otto Roberto', 'apellidos': 'Vargas Víquez'},
    53: {'nombres': 'Paola Viviana', 'apellidos': 'Vega Rodríguez'},
    54: {'nombres': 'Gustavo Alonso', 'apellidos': 'Viales Villegas'},
    55: {'nombres': 'José María', 'apellidos': 'Villalta Flórez-Estrada'},
    56: {'nombres': 'Sylvia Patricia', 'apellidos': 'Villegas Álvarez'},
    57: {'nombres': 'Zoila Rosa', 'apellidos': 'Volio Pacheco'}
}


# REGEXES ----

IGNORAR_LINEA = [
    re.compile(r'ACTA ORDINARIA N'),
    re.compile(r'^[0-9]{1,2}$'),
    re.compile('^$'),
    re.compile(r'(^[\sA-ZÁÉÍÓÚ°0-9\.\(\),º\-]+$)'),
    re.compile(r'^\n$')
]

HABLA_DIP = re.compile(r'Diputad. (?P<dip>[\w\s]*):')
HABLA_PRES = re.compile(r'President. (a\.? í\.?)?[\w\s]*:')

NOMBRE_ASIST = '\w+(\s+\w+)?,\s+\w+(\s{1,2}\w+)?(\s\(cc \w+\))?'
RE_TABLA_ASISTENCIA = r'\s*(?P<dip1>{0})\s*(?P<dip2>{0})?'.format(NOMBRE_ASIST)
LINEA_NOMBRES_DIP = re.compile(RE_TABLA_ASISTENCIA, re.I)

NOMBRE_CC = re.compile(r'(?P<apellidos>[\w\s]+?), (?P<nombres>[\s\w]+?) (?P<nombre_cc>\(cc \w+?\))')

# ----------

db = os.environ['AA_db']

# ----------

def sacar_indice(nombre):
    """
    Devuelve el índice de ``DIPS`` al que corresponde el ``nombre``. Busca ya sea que los nombres
    y apellidos correspondan exactamente a un conjunto de ``DIPS``, o que haya diferencias leves
    (p.ej. faltas de ortografía, o solamente se usó uno de los nombres de pila).

    Esta función se debería reemplazar por algo más eficiente, tal vez usando word2vec.

    :param str nombre: nombre por analizar

    :returns i: "índice" (realmente es el 'key') de ``DIPS``
    :rtype: int
    """
    apd, nmb = nombre.split(', ')
    for i, info in DIPS.items():
        match_nmb = nmb == info['nombres']
        match_apd = apd == info['apellidos']
        if match_apd and match_nmb:
            # Si corresponde exactamente, devolver el índice-llave...
            return i

    # Si no, se da otra pasada haciendo un análisis más detallado. Se espera que las posibilidades
    # sean que: 1. los apellidos correspondan, pero el nombre es un poco diferente, 2. los
    # apellidos son un poco diferentes, 3. Tiene una nota de "Conocido como" (cc).
    # Para 1 y 2, determina que corresponden los nombres y/o apellidos cuando el coeficiente de
    # similitud es mayor a 0.9
    opciones = [nombre]
    for i, info in DIPS.items():
        match_apd = apd == info['apellidos']
        match_apd_prob = difflib.SequenceMatcher(None, apd, info['apellidos']).ratio() > 0.9
        if match_apd or match_apd_prob:
            contiene_cc = NOMBRE_CC.search(nombre)
            if contiene_cc:
                # Ejemplo: "Monge Salas, Rony (cc Ronny)"
                nmb_cc_info = contiene_cc.groupdict()
                if nmb_cc_info['nombre_cc'] == info['nombres']:
                    return i
                opciones.append(nmb_cc_info['apellidos'] + ', ' + nmb_cc_info['nombres'])
                opciones.append(nmb_cc_info['apellidos'] + ', ' + nmb_cc_info['nombre_cc'])
            nombres = nmb.split()
            for _nombre in nombres:
                opciones.append(apd + ', ' + _nombre)

        nombre_completo = info['apellidos'] + ', ' + info['nombres']
        if any([difflib.SequenceMatcher(None, nombre_completo, opc).ratio() > 0.9
                for opc in opciones]):
            print('nombre: {} - id: {} - por probabilidad, opciones: {}'.format(nombre, i,
                                                                                opciones))
            return i
    raise ValueError('Ni idea quién es {}'.format(nombre))


def asistencia(pag):
    """
    Analiza la página de asistencia y saca la lista de nombres. Con eso, prepara la estructura de
    datos donde se llevará la cuenta de intervenciones y uso de la palabra en el plenario.

    :param str pag: transcripción de una página extraída por la función ``leer_pdf``

    :returns data: estructura de datos donde la llave es el índice que corresponde en ``DIPS``,
        y las llaves de intervenciones y palabras inicializadas en 0
    :returns bitacora: información para reportar bitácora
    :rtype: dict, str
    """
    presentes = []
    bitacora = []
    for linea in pag.splitlines():
        nombres = LINEA_NOMBRES_DIP.search(linea)
        if nombres:
            c = 0
            for v in nombres.groupdict().values():
                if v is None:
                    continue
                presentes.append(v.strip())
                c += 1
            bitacora.append(('nombres={}'.format(c), linea))
        else:
            bitacora.append(('', linea))
    presentes.sort()
    data = {}
    for nombre in presentes:
        i = sacar_indice(nombre)
        data[i] = {}
        data[i]['intervenciones'] = 0
        data[i]['palabras'] = 0
    return data, bitacora


def analizar(contenido):
    """
    Extrae las métricas. Es un desorden, ¡pero funciona! (igual hay que mejorarlo)

    Empieza ignorando hasta encontrar la página donde se lista los/as asistentes. Saca esos datos
    a una estructura.

    Luego va a la siguiente página y línea por línea busca el encabezado cuando alguna/ún
    diputada/o tiene la palabra. Cuando la palabra la tiene el/la presidente/a, lo ignora (ya
    que en ese caso su función es solamente coordinar el uso de la palabra), pero cuando alguien
    tiene la palabra en calidad de diputada/o, busca quién es, y suma una intervención y aumenta
    el contador de palabras según la cantidad que haya en la línea, hasta encontrar otro encabezado.
    Así sigue hasta encontrar que se levanta la sesión, y ahí para de contar.

    :param object contenido: objeto ``pdftotext.PDF``

    :returns data: estructura de datos con los contadores actualizados
    :rtype: dict
    """
    levanta_sesion = 'se levanta la sesión'
    bitacora = []

    asistencia_tomada = False
    midiendo_intervenciones = False
    terminar = False
    habla_presidente = False
    for num_pag, pag in enumerate(contenido):
        num_pag += 1
        if not asistencia_tomada:
            if 'diputados presentes' in pag.lower():
                data, _bitacora = asistencia(pag)
                asistencia_tomada = True
                bitacora.extend(_bitacora)
                continue
            else:
                bitacora.extend([('{}:{}:'.format(num_pag, num_linea), linea)
                                  for num_linea, linea
                                  in enumerate(pag.splitlines())])
                continue
        if not midiendo_intervenciones:
            if not HABLA_DIP.search(pag) and not HABLA_PRES.search(pag):
                bitacora.extend([('{}:{}:'.format(num_pag, num_linea), linea)
                                  for num_linea, linea
                                  in enumerate(pag.splitlines())])
                continue
            midiendo_intervenciones = True
        for num_linea, linea in enumerate(pag.splitlines()):
            if terminar:
                bitacora.append(('', linea))
                continue
            if levanta_sesion in linea:
                terminar = True
                bitacora.append(('{}:{}:Finaliza el análisis'.format(num_pag, num_linea), linea))
                continue
            if any([regex.search(linea) for regex in IGNORAR_LINEA]):
                bitacora.append(('{}:{}:ignorar línea'.format(num_pag, num_linea), linea))
                continue
            if HABLA_PRES.search(linea):
                habla_presidente = True
            if HABLA_DIP.search(linea):
                habla_presidente = False
                se_quien_es = False
                for i, info in DIPS.items():
                    if info['apellidos'] in linea:
                        data[i]['intervenciones'] += 1
                        se_quien_es = True
                        bitacora.append(('{}:{}:habla dip, id: {}, intervención # {}'
                                         .format(num_pag, num_linea, i, data[i]['intervenciones']),
                                                 linea))
                        break
                if not se_quien_es:
                    raise ValueError('¿Quién es {}?'.format(linea))
                continue
            if habla_presidente:
                bitacora.append(('{}:{}:habla presidenta/e'.format(num_pag, num_linea), linea))
                continue
            data[i]['palabras'] += len(linea.split())
            bitacora.append(('{}:{}:habla dip, id: {}, palabras {}'
                            .format(num_pag, num_linea, i, data[i]['palabras']), linea))

    if not terminar:
        raise ValueError('No se encontró el final del acta, frase esperada: '
                         '"{}"'.format(levanta_sesion))

    return data, bitacora


def leer_pdf(archivo):
    """Convierte un pdf a una serie de strings que contienen cada página."""
    with open(archivo, 'rb') as f:
        contenido = pdftotext.PDF(f)
    return contenido


def obtener_cmd_db(arch, fecha):
    """
    Como todavía no he montado el ORM lo que hago es imprimir el comando para insertar la info
    a la DB, y agrego los datos manualmente.
    """
    cont = leer_pdf(arch)
    data, bitacora = analizar(cont)
    records = []
    for i, info in data.items():
        records.append(str((fecha, i, info['intervenciones'], info['palabras'])))
    stmt = 'insert into {} (fecha, iddip, intervenciones, palabras) values '.format(db)
    stmt += ', '.join(records)
    print('Total diputados/as presentes:', len(records), '\n')
    print(stmt+'\n')
    return bitacora


def escribir_bitacora(bitacora):
    """Escribe archivo de bitacora."""
    print('Escribiendo bitácora')
    with open(os.path.join('bitacoras', fecha+'.log'), 'w') as f:
        for info in bitacora:
            f.write('{:45} | {}\n'.format(info[0], info[1]))


if __name__ == '__main__':
    archivo = sys.argv[1]
    fecha = sys.argv[2]

    bitacora = obtener_cmd_db(archivo, fecha)
    escribir_bitacora(bitacora)
