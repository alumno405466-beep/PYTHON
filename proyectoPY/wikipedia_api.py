# wikipedia_api.py
import requests
import wikipediaapi

def buscar_articulo_wikipedia(titulo):
    """
    Busca un artículo en Wikipedia y devuelve sus datos
    """
    try:
        # Configurar Wikipedia en español
        wiki_wiki = wikipediaapi.Wikipedia(
            language='es',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='MiAppWikipedia/1.0 (contacto@email.com)'
        )
        
        # Buscar página
        page = wiki_wiki.page(titulo)
        
        if not page.exists():
            return None, "El artículo no existe en Wikipedia"
        
        # Devolver datos
        return {
            'titulo': page.title,
            'resumen': page.summary[:500] + "..." if len(page.summary) > 500 else page.summary,
            'url': page.fullurl,
            'categoria_sugerida': sugerir_categoria(page.summary),
            'imagen': obtener_imagen_principal(titulo)  # Opcional
        }, None
        
    except Exception as e:
        return None, f"Error al conectar con Wikipedia: {str(e)}"

def sugerir_categoria(texto):
    """
    Sugiere una categoría basada en el contenido
    """
    texto_lower = texto.lower()
    
    categorias = {
        'Ciencia': ['ciencia', 'física', 'química', 'biología', 'matemáticas'],
        'Historia': ['historia', 'guerra', 'imperio', 'revolución', 'siglo'],
        'Arte': ['arte', 'pintura', 'música', 'literatura', 'escultura'],
        'Tecnología': ['tecnología', 'informática', 'internet', 'software'],
        'Deportes': ['deporte', 'fútbol', 'baloncesto', 'olímpico'],
        'Biografías': ['nació', 'falleció', 'biografía', 'vida'],
        'Geografía': ['país', 'ciudad', 'río', 'montaña', 'océano']
    }
    
    for cat, palabras in categorias.items():
        for palabra in palabras:
            if palabra in texto_lower:
                return cat
    
    return 'Otros'

def obtener_imagen_principal(titulo):
    """
    Obtiene la imagen principal del artículo (opcional, más complejo)
    """
    # Implementación simplificada
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{titulo.replace(' ', '_')}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'thumbnail' in data:
                return data['thumbnail']['source']
    except:
        pass
    return None