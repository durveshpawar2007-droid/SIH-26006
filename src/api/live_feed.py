from datetime import datetime
import httpx

async def fetch_live_marine_telemetry():
    """
    Fetches real-time sea-state telemetry from Open-Meteo Marine API
    and live USD/INR exchange rate from Frankfurter API.
    Zero API key required.
    """
    telemetry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sea_state": {},
        "forex": {"usd_inr": 83.50, "status": "fallback"},
        "weather_risk_index": "LOW",
        "voyage_delay_hours": 0
    }

    async with httpx.AsyncClient(timeout=6.0) as client:
        # 1. Fetch Bay of Bengal Marine Data (15.0N, 88.0E)
        try:
            bob_resp = await client.get(
                "https://marine-api.open-meteo.com/v1/marine",
                params={
                    "latitude": 15.0,
                    "longitude": 88.0,
                    "current": "wave_height,wave_period"
                }
            )
            if bob_resp.status_code == 200:
                cur = bob_resp.json().get("current", {})
                wave_h = cur.get("wave_height", 1.8)
                telemetry["sea_state"]["bay_of_bengal"] = {
                    "wave_height_m": wave_h,
                    "wave_period_s": cur.get("wave_period", 6.2),
                    "status": "Rough (High Delay Risk)" if wave_h > 2.5 else "Moderate / Normal"
                }
        except Exception as e:
            telemetry["sea_state"]["bay_of_bengal"] = {"wave_height_m": 1.8, "status": "Estimated", "error": str(e)}

        # 2. Fetch Malacca Strait Marine Data (2.5N, 101.5E)
        try:
            malacca_resp = await client.get(
                "https://marine-api.open-meteo.com/v1/marine",
                params={
                    "latitude": 2.5,
                    "longitude": 101.5,
                    "current": "wave_height,wave_period"
                }
            )
            if malacca_resp.status_code == 200:
                cur = malacca_resp.json().get("current", {})
                wave_h = cur.get("wave_height", 0.9)
                telemetry["sea_state"]["malacca_strait"] = {
                    "wave_height_m": wave_h,
                    "wave_period_s": cur.get("wave_period", 4.8),
                    "status": "Rough" if wave_h > 2.0 else "Calm / Clear"
                }
        except Exception as e:
            telemetry["sea_state"]["malacca_strait"] = {"wave_height_m": 0.9, "status": "Estimated", "error": str(e)}

        # 3. Fetch Live USD to INR Rate
        try:
            fx_resp = await client.get("https://api.frankfurter.app/latest?from=USD&to=INR")
            if fx_resp.status_code == 200:
                rates = fx_resp.json().get("rates", {})
                telemetry["forex"] = {
                    "usd_inr": rates.get("INR", 83.50),
                    "status": "LIVE"
                }
        except Exception as e:
            telemetry["forex"] = {"usd_inr": 83.45, "status": "Cached Fallback"}

    # Compute operational risk penalty for solver consumption
    bob_wave = telemetry["sea_state"].get("bay_of_bengal", {}).get("wave_height_m", 1.5)
    if bob_wave > 2.8:
        telemetry["weather_risk_index"] = "HIGH"
        telemetry["voyage_delay_hours"] = 24
    elif bob_wave > 2.0:
        telemetry["weather_risk_index"] = "ELEVATED"
        telemetry["voyage_delay_hours"] = 12
    else:
        telemetry["weather_risk_index"] = "LOW"
        telemetry["voyage_delay_hours"] = 0

    return telemetry