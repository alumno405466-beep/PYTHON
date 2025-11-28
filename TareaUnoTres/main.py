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
def notas(id = None, evaluacion = None):
    evaluacion = ["Parcial1", "Parcial2", "Ordinario1", "Practicas", "OrdinarioPracticas"]

    if id is None or evaluacion is None:
        return {
            "mensaje": "Campos sin rellenar",
            "ejemplo": "/notas?id=1001&evaluacion=Parcial1",
            "notasdisponibles": evaluacion
        }

    alumno = df[df["ID"] == int(id)]

    nombrecompleto = f"{alumno.iloc[0]['Nombre']} {alumno.iloc[0]['Apellidos']}"
    nota = alumno.iloc[0][evaluacion]

    nota = float(nota)

    return {
        "alumno": nombrecompleto,
        "evaluacion": evaluacion,
        "nota": nota
    }