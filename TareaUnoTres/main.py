from fastapi import FastAPI
import pandas as pd

app = FastAPI(title="iesazarquiel")

df = pd.read_csv("uno.csv")




#infoalumnos
@app.get("/info-alumnos")
def infoalumnos():
    ids = df["ID"].tolist()
    return {"idsdisponibles": ids}




#asistencia
@app.get("/asistencia")
def asistencia(id = None):
    if id is None:
        return {
            "mododeuso": "Debes introducir un ID",
            "ejemplo": "/asistencia?id=1001",
        }

    alumno = df[df["ID"] == int(id)]

    nombrecompleto = f"{alumno.iloc[0]['Nombre']} {alumno.iloc[0]['Apellidos']}"
    asistencia = alumno.iloc[0]['Asistencia']
    
    asistenciaporcen = f"{asistencia * 100}%"

    return {
        "alumno": nombrecompleto,
        "asistencia": asistenciaporcen
    }





@app.get("/notas")
def notas(id = None, nota = None):
    todasnotas = ["Parcial1", "Parcial2", "Ordinario1", "Practicas", "OrdinarioPracticas"]

    if id is None or nota is None:
        return {
            "mensaje": "Campos sin rellenar",
            "ejemplo": "/notas?id=1001&nota=Parcial1",
            "notasdisponibles": todasnotas
        }

    alumno = df[df["ID"] == int(id)]

    nombrecompleto = f"{alumno.iloc[0]['Nombre']} {alumno.iloc[0]['Apellidos']}"
    calificacion = alumno.iloc[0][nota]

    calificacion = float(calificacion)

    return {
        "alumno": nombrecompleto,
        "nota": nota,
        "calificacion": calificacion
    }