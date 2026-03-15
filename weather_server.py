"""
Serveur MCP Meteo
=================
Un serveur MCP qui donne la meteo en temps reel.

Utilise l'API gratuite Open-Meteo (pas de cle API requise).
https://open-meteo.com/

Tools exposes :
  - get_weather       : meteo actuelle d'une ville
  - get_forecast      : previsions sur plusieurs jours
  - compare_weather   : comparer la meteo de 2 villes
"""

import json
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialisation du serveur
server = FastMCP("weather_mcp")

# Client HTTP reutilisable
API_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
API_WEATHER = "https://api.open-meteo.com/v1/forecast"


# --- Fonctions utilitaires ---

async def geocode(ville: str) -> dict:
    """Convertit un nom de ville en coordonnees GPS."""
    async with httpx.AsyncClient() as client:
        r = await client.get(API_GEOCODING, params={
            "name": ville,
            "count": 1,
            "language": "fr",
        })
        data = r.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    result = data["results"][0]
    return {
        "name": result.get("name", ville),
        "country": result.get("country", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


async def fetch_weather(lat: float, lon: float, forecast_days: int = 1) -> dict:
    """Recupere les donnees meteo depuis Open-Meteo."""
    async with httpx.AsyncClient() as client:
        r = await client.get(API_WEATHER, params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": forecast_days,
        })
        return r.json()


def weather_code_to_text(code: int) -> str:
    """Convertit un code meteo WMO en texte lisible."""
    codes = {
        0: "Ciel degage",
        1: "Principalement degage",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine legere",
        53: "Bruine moderee",
        55: "Bruine dense",
        61: "Pluie legere",
        63: "Pluie moderee",
        65: "Pluie forte",
        71: "Neige legere",
        73: "Neige moderee",
        75: "Neige forte",
        80: "Averses legeres",
        81: "Averses moderees",
        82: "Averses violentes",
        85: "Averses de neige legeres",
        86: "Averses de neige fortes",
        95: "Orage",
        96: "Orage avec grele legere",
        99: "Orage avec grele forte",
    }
    return codes.get(code, f"Code {code}")


def weather_code_to_emoji(code: int) -> str:
    """Convertit un code meteo en emoji."""
    if code == 0: return "☀️"
    if code <= 2: return "🌤️"
    if code == 3: return "☁️"
    if code <= 48: return "🌫️"
    if code <= 55: return "🌦️"
    if code <= 65: return "🌧️"
    if code <= 75: return "🌨️"
    if code <= 82: return "🌧️"
    if code <= 86: return "🌨️"
    return "⛈️"


# --- Tool 1 : Meteo actuelle ---

class GetWeatherInput(BaseModel):
    ville: str = Field(..., description="Nom de la ville (ex: Paris, Lyon, Tokyo)", min_length=1)


@server.tool(name="get_weather")
async def get_weather(params: GetWeatherInput) -> str:
    """Donne la meteo actuelle d'une ville.

    Retourne la temperature, le ressenti, l'humidite, le vent et les conditions.
    """
    location = await geocode(params.ville)
    if not location:
        return f"Erreur : Ville '{params.ville}' introuvable. Verifiez l'orthographe."

    data = await fetch_weather(location["latitude"], location["longitude"])
    current = data.get("current", {})

    code = current.get("weather_code", 0)
    emoji = weather_code_to_emoji(code)
    condition = weather_code_to_text(code)

    return (
        f"{emoji} Meteo a {location['name']} ({location['country']}) :\n"
        f"\n"
        f"  Condition   : {condition}\n"
        f"  Temperature : {current.get('temperature_2m', '?')} C\n"
        f"  Ressenti    : {current.get('apparent_temperature', '?')} C\n"
        f"  Humidite    : {current.get('relative_humidity_2m', '?')} %\n"
        f"  Vent        : {current.get('wind_speed_10m', '?')} km/h"
    )


# --- Tool 2 : Previsions ---

class GetForecastInput(BaseModel):
    ville: str = Field(..., description="Nom de la ville", min_length=1)
    jours: Optional[int] = Field(default=3, description="Nombre de jours de prevision (1 a 7)", ge=1, le=7)


@server.tool(name="get_forecast")
async def get_forecast(params: GetForecastInput) -> str:
    """Donne les previsions meteo sur plusieurs jours.

    Retourne pour chaque jour : temperatures min/max, precipitations et conditions.
    """
    location = await geocode(params.ville)
    if not location:
        return f"Erreur : Ville '{params.ville}' introuvable."

    data = await fetch_weather(location["latitude"], location["longitude"], forecast_days=params.jours)
    daily = data.get("daily", {})

    dates = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    codes = daily.get("weather_code", [])

    lines = [f"Previsions a {location['name']} ({location['country']}) sur {params.jours} jour(s) :\n"]

    for i in range(len(dates)):
        emoji = weather_code_to_emoji(codes[i]) if i < len(codes) else ""
        condition = weather_code_to_text(codes[i]) if i < len(codes) else ""
        pluie = f"{precip[i]} mm" if i < len(precip) and precip[i] > 0 else "pas de pluie"

        lines.append(
            f"  {dates[i]} {emoji} {condition}\n"
            f"             Min {t_min[i]} C / Max {t_max[i]} C / {pluie}"
        )

    return "\n".join(lines)


# --- Tool 3 : Comparer 2 villes ---

class CompareWeatherInput(BaseModel):
    ville1: str = Field(..., description="Premiere ville", min_length=1)
    ville2: str = Field(..., description="Deuxieme ville", min_length=1)


@server.tool(name="compare_weather")
async def compare_weather(params: CompareWeatherInput) -> str:
    """Compare la meteo actuelle de deux villes cote a cote."""
    loc1 = await geocode(params.ville1)
    loc2 = await geocode(params.ville2)

    if not loc1:
        return f"Erreur : Ville '{params.ville1}' introuvable."
    if not loc2:
        return f"Erreur : Ville '{params.ville2}' introuvable."

    data1 = await fetch_weather(loc1["latitude"], loc1["longitude"])
    data2 = await fetch_weather(loc2["latitude"], loc2["longitude"])

    c1 = data1.get("current", {})
    c2 = data2.get("current", {})

    code1 = c1.get("weather_code", 0)
    code2 = c2.get("weather_code", 0)

    t1 = c1.get("temperature_2m", "?")
    t2 = c2.get("temperature_2m", "?")

    diff = ""
    if isinstance(t1, (int, float)) and isinstance(t2, (int, float)):
        d = round(t1 - t2, 1)
        if d > 0:
            diff = f"\n  -> {loc1['name']} est {d} C plus chaud que {loc2['name']}"
        elif d < 0:
            diff = f"\n  -> {loc2['name']} est {abs(d)} C plus chaud que {loc1['name']}"
        else:
            diff = f"\n  -> Meme temperature dans les 2 villes"

    return (
        f"Comparaison meteo :\n"
        f"\n"
        f"  {weather_code_to_emoji(code1)} {loc1['name']} ({loc1['country']})\n"
        f"     {weather_code_to_text(code1)}\n"
        f"     {t1} C (ressenti {c1.get('apparent_temperature', '?')} C)\n"
        f"     Vent {c1.get('wind_speed_10m', '?')} km/h | Humidite {c1.get('relative_humidity_2m', '?')}%\n"
        f"\n"
        f"  {weather_code_to_emoji(code2)} {loc2['name']} ({loc2['country']})\n"
        f"     {weather_code_to_text(code2)}\n"
        f"     {t2} C (ressenti {c2.get('apparent_temperature', '?')} C)\n"
        f"     Vent {c2.get('wind_speed_10m', '?')} km/h | Humidite {c2.get('relative_humidity_2m', '?')}%\n"
        f"{diff}"
    )


# --- Point d'entree ---

if __name__ == "__main__":
    server.run()
