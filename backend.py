import requests
import pandas as pd
from datetime import datetime, timedelta

OWNER = None
REPO = None
HEADERS = None

def get_github_data(url, params=None):
    """Realiza una solicitud GET a la API de GitHub con manejo de errores y paginación."""
    try:
        all_items = []
        while url:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            items = response.json()
            all_items.extend(items)
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        return all_items
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de {url}: {e}")
        return None
    except ValueError:
        print(f"Error al decodificar JSON de {url}")
        return None

def establecer_configuraciones(owner, repository, pat_file):
    global OWNER, REPO, HEADERS
    if pat_file is not None:
        try:
            OWNER = owner
            REPO = repository
            pat = pat_file.read().decode("utf-8")
            HEADERS = {
                "Authorization": f"token {pat.strip()}",
                "Accept": "application/vnd.github.v3+json",
            }
            print(f"Configuraciones establecidas para: {OWNER}/{REPO}")
        except UnicodeDecodeError as e:
            print(f"Error: {e}")
    else:
        print("No se ha subido ningún archivo.")

def generar_informe_actividad(dias=365):
    """Genera un informe de actividad del repositorio."""
    print("ESTO RECUPERO : ", OWNER, REPO)
    hoy = datetime.now()
    fecha_inicio = hoy - timedelta(days=dias)
    fecha_inicio_iso = fecha_inicio.isoformat()

    issues_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    pulls_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"

    # Obtener issues creados en el periodo
    params_issues = {"since": fecha_inicio_iso, "state": "all", "sort": "created", "direction": "desc", "per_page": 100}
    issues = get_github_data(issues_url, params=params_issues)
    if issues is None:
        print(f"Error al obtener la lista de issues para {OWNER}/{REPO}. El informe de actividad de issues no se generará.")
        return
    issues_creadas = [issue for issue in issues if datetime.fromisoformat(issue['created_at'][:-1]) >= fecha_inicio]

    # Obtener pull requests mergeados en el periodo
    params_pulls = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    pulls = get_github_data(pulls_url, params=params_pulls)
    if pulls is None:
        print(f"Error al obtener la lista de pull requests para {OWNER}/{REPO}. El informe de actividad de pull requests no se generará.")
        return
    pulls_mergeados = [pr for pr in pulls if pr['merged_at'] and datetime.fromisoformat(pr['merged_at'][:-1]) >= fecha_inicio]

    print(f"\n--- Informe de Actividad del Repositorio '{OWNER}/{REPO}' ({dias} días) ---")
    print(f"Issues Creadas: {len(issues_creadas)}")
    print(f"Pull Requests Mergeados: {len(pulls_mergeados)}")
    return(len(issues_creadas), len(pulls_mergeados))

def analizar_contribuciones(desde=None, hasta=None):
    """Analiza las contribuciones de los miembros del equipo."""
    commits_url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    params = {"per_page": 100}
    if desde:
        params["since"] = desde
    if hasta:
        params["until"] = hasta

    commits = get_github_data(commits_url, params=params)
    if commits:
        autor_contribuciones = {}
        for commit in commits:
            autor = commit['author']['login'] if commit['author'] else commit['commit']['author']['name']
            autor_contribuciones[autor] = autor_contribuciones.get(autor, 0) + 1

        data = pd.DataFrame({
            "Usuario": list(autor_contribuciones.keys()),
            "Commits": list(autor_contribuciones.values())
        })

        data = data.sort_values(by="Commits", ascending=False).reset_index(drop=True)

        return data
    else:
        print("No se pudieron obtener los commits para el análisis de contribuciones.")
        return pd.DataFrame(columns=["Usuario", "Commits"])

def seguimiento_metricas(dias=365):
    """Realiza el seguimiento de métricas como el tiempo de respuesta a issues y el tiempo para mergear PRs."""
    hoy = datetime.now()
    fecha_inicio = hoy - timedelta(days=dias)
    fecha_inicio_iso = fecha_inicio.isoformat()

    issues_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    pulls_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"

    # Tiempo de respuesta a issues (primer comentario)
    tiempo_respuesta_issues = []
    params_issues = {"state": "all", "sort": "created", "direction": "desc", "since": fecha_inicio_iso, "per_page": 100}
    issues = get_github_data(issues_url, params=params_issues)
    if issues:
        for issue in issues:
            if issue['comments'] > 0:
                comments_url = issue['comments_url']
                comments = get_github_data(comments_url)
                if comments:
                    primero_comentario = min(comments, key=lambda c: datetime.fromisoformat(c['created_at'][:-1]))
                    tiempo_creacion = datetime.fromisoformat(issue['created_at'][:-1])
                    tiempo_primer_comentario = datetime.fromisoformat(primero_comentario['created_at'][:-1])
                    tiempo_respuesta = tiempo_primer_comentario - tiempo_creacion
                    tiempo_respuesta_issues.append(tiempo_respuesta.total_seconds())
        
    # Tiempo para mergear pull requests
    tiempo_merge_prs = []
    params_pulls = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    pulls = get_github_data(pulls_url, params=params_pulls)
    if pulls:
        for pr in pulls:
            if pr['merged_at'] and pr['created_at']:
                tiempo_creacion_pr = datetime.fromisoformat(pr['created_at'][:-1])
                tiempo_merge_pr = datetime.fromisoformat(pr['merged_at'][:-1])
                tiempo_para_merge = tiempo_merge_pr - tiempo_creacion_pr
                tiempo_merge_prs.append(tiempo_para_merge.total_seconds())

    print(f"\n--- Seguimiento de Métricas del Repositorio '{OWNER}/{REPO}' ({dias} días) ---")
    if tiempo_respuesta_issues:
        promedio_respuesta_issues = timedelta(seconds=sum(tiempo_respuesta_issues) / len(tiempo_respuesta_issues))
        print(f"Tiempo Promedio de Respuesta a Issues: {promedio_respuesta_issues}")
    else:
        print("No hay suficientes issues con comentarios para calcular el tiempo de respuesta.")

    if tiempo_merge_prs:
        promedio_merge_prs = timedelta(seconds=sum(tiempo_merge_prs) / len(tiempo_merge_prs))
        print(f"Tiempo Promedio para Mergear Pull Requests: {promedio_merge_prs}")
    else:
        print("No hay suficientes pull requests mergeados para calcular el tiempo de mergeo.")

    return(formatear_timedelta(promedio_respuesta_issues), formatear_timedelta(promedio_merge_prs))

def formatear_timedelta(td):
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days} days, {hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
