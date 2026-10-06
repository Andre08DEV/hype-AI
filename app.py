import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# 1. SEGURIDAD: Leer la API Key de las variables de entorno del sistema (Codespaces o Vercel)
# Esto evita que GitHub te bloquee el código por filtrar claves privadas en internet.
api_key = os.environ.get("GEMINI_API_KEY", "")

# Inicializar el cliente de Google GenAI con la clave del entorno
client = genai.Client(api_key=api_key) if api_key else None

app = FastAPI(title="Mi App de IA con Gemini", version="14.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Consulta(BaseModel):
    texto: str

# 2. Endpoint inteligente con Auto-Reintentos
@app.post("/preguntar")
async def consultar_gemini(consulta: Consulta):
    if not client:
        raise HTTPException(status_code=500, detail="Error: La variable GEMINI_API_KEY no está configurada en el servidor.")
        
    if not consulta.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    
    intentos_maximos = 4
    for intento in range(intentos_maximos):
        try:
            # Consultamos al modelo más moderno exigido por Google
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=consulta.texto,
            )
            
            if hasattr(response, 'text') and response.text:
                return {"status": "success", "respuesta_ia": response.text}
            else:
                return {"status": "error", "respuesta_ia": "⚠️ Google devolvió una respuesta vacía. Intenta de nuevo."}
                
        except Exception as e:
            error_str = str(e).lower()
            # Si hay picos de alta demanda (503), el sistema insiste automáticamente
            if "503" in error_str or "demand" in error_str or "unavailable" in error_str:
                print(f"\n[Saturación - Intento {intento + 1}/{intentos_maximos}]: Reintentando en 2 segundos...\n")
                time.sleep(2)
                continue
            else:
                return {"status": "error", "respuesta_ia": f"⚠️ Error en la API de Google: {str(e)}"}
                
    return {
        "status": "error", 
        "respuesta_ia": "⚠️ Los servidores de Google están extremadamente saturados en este momento debido a la alta demanda global. Por favor, dale al botón Enviar una vez más."
    }

# 3. Interfaz Gráfica del Chat con soporte Markdown (Cajas de código organizadas)
@app.get("/", response_class=HTMLResponse)
async def obtener_interfaz():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat con Gemini</title>
        <!-- Librería Marked para procesar las respuestas con código limpio -->
        <script src="https://jsdelivr.net"></script>
        <style>
            body { background-color: #111827; color: #f3f4f6; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; justify-content: space-between; }
            header { background-color: #1f2937; padding: 15px; text-align: center; border-bottom: 1px solid #374151; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            h1 { color: #2dd4bf; margin: 0; font-size: 24px; }
            header p { color: #9ca3af; font-size: 12px; margin: 5px 0 0 0; }
            main { flex: 1; overflow-y: auto; padding: 20px; max-width: 850px; width: 100%; margin: 0 auto; box-sizing: border-box; }
            .msg-container { display: flex; margin-bottom: 15px; width: 100%; }
            .msg-user { justify-content: flex-end; }
            .msg-ia { justify-content: flex-start; }
            .bubble { padding: 12px 18px; max-width: 85%; box-shadow: 0 2px 4px rgba(0,0,0,0.2); font-size: 14px; line-height: 1.5; border-radius: 12px; }
            .bubble-user { background-color: #0d9488; color: white; border-top-right-radius: 0; }
            .bubble-ia { background-color: #1f2937; color: #f3f4f6; border-top-left-radius: 0; }
            pre { background-color: #030712; padding: 12px; border-radius: 8px; overflow-x: auto; border: 1px solid #374151; margin: 10px 0; }
            code { font-family: monospace; color: #f43f5e; background-color: #1e1b4b; padding: 2px 4px; border-radius: 4px; font-size: 13px; }
            pre code { color: #34d399; background-color: transparent; padding: 0; font-size: 13px; }
            #loading { display: none; text-align: center; font-size: 13px; color: #9ca3af; padding-bottom: 10px; }
            footer { background-color: #1f2937; padding: 15px; border-top: 1px solid #374151; }
            form { max-width: 850px; margin: 0 auto; display: flex; gap: 10px; }
            input { flex: 1; background-color: #374151; border: 1px solid #4b5563; border-radius: 8px; padding: 12px 15px; color: white; font-size: 14px; outline: none; }
            input:focus { border-color: #2dd4bf; }
            button { background-color: #14b8a6; border: none; border-radius: 8px; padding: 12px 24px; color: #111827; font-weight: bold; cursor: pointer; font-size: 14px; }
            button:hover { background-color: #0d9488; }
        </style>
    </head>
    <body>
        <header>
            <h1>🤖 Mi Asistente IA</h1>
            <p>Ecosistema Seguro & Profesional</p>
        </header>
        <main id="chat-box"></main>
        <div id="loading">Gemini está procesando tu mensaje... 🤔</div>
        <footer>
            <form id="chat-form">
                <input type="text" id="user-input" placeholder="Escribe tu mensaje aquí..." required autocomplete="off">
                <button type="submit">Enviar</button>
            </form>
        </footer>
        <script>
            const chatForm = document.getElementById('chat-form');
            const userInput = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const loading = document.getElementById('loading');
            const API_URL = `${window.location.origin}/preguntar`;

            agregarMensaje("¡Tu entorno está completamente protegido bro! El código está listo para subirse a GitHub y desplegarse en Vercel de forma profesional.", 'ia');

            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const mensajeTexto = userInput.value.trim();
                if (!mensajeTexto) return;

                agregarMensaje(mensajeTexto, 'usuario');
                userInput.value = '';
                loading.style.display = 'block';
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ texto: mensajeTexto })
                    });
                    const data = await response.json();
                    agregarMensaje(data.respuesta_ia, 'ia');
                } catch (error) {
                    agregarMensaje('⚠️ Error: Asegúrate de configurar la variable GEMINI_API_KEY en tu entorno.', 'ia');
                } finally {
                    loading.style.display = 'none';
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            });

            function agregarMensaje(texto, remitente) {
                const container = document.createElement('div');
                const bubble = document.createElement('div');
                container.classList.add('msg-container');
                bubble.classList.add('bubble');
                if (remitente === 'usuario') {
                    container.classList.add('msg-user');
                    bubble.classList.add('bubble-user');
                    bubble.innerText = texto;
                } else {
                    container.classList.add('msg-ia');
                    bubble.classList.add('bubble-ia');
                    bubble.innerHTML = marked.parse(texto);
                }
                container.appendChild(bubble);
                chatBox.appendChild(container);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
