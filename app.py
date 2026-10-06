import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# 1. Configuración de tu API Key de Gemini
os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6KCh4111fIN7Tc2OEojSxW274hOOY0WPjheAVexnNXsow"

# 2. Inicializar el cliente oficial de GenAI
client = genai.Client()

# 3. Inicializar FastAPI
app = FastAPI(
    title="Servidor de IA con Gemini",
    description="Backend conectado de forma nativa a Gemini 2.5",
    version="1.0"
)

# 4. Habilitar seguridad CORS para tu index.html
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Consulta(BaseModel):
    texto: str

# 5. Endpoint de comunicación del chat
@app.post("/preguntar")
async def consultar_gemini(consulta: Consulta):
    if not consulta.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    
    try:
        # Consulta al modelo gemini-2.5-flash utilizando la API Key provista
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=consulta.texto,
        )
        
        return {
            "status": "success",
            "pregunta": consulta.texto,
            "respuesta_ia": response.text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Gemini: {str(e)}")

@app.get("/")
def estado():
    return {"status": "online", "modelo": "gemini-2.5-flash"}
