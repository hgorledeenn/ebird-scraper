#!/usr/bin/env python3
"""
eBird Notable Sightings Scraper
Fetches notable bird sightings from eBird API and generates static HTML/JSON.
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path


def load_config():
    """Load configuration from config.json."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


def fetch_notable_observations(api_key, region_code, days_back=7, max_results=100):
    """
    Fetch notable observations from eBird API.

    API Endpoint: GET /v2/data/obs/{regionCode}/recent/notable
    Docs: https://documenter.getpostman.com/view/664302/S1ENwy59
    """
    url = f"https://api.ebird.org/v2/data/obs/{region_code}/recent/notable"
    headers = {"X-eBirdApiToken": api_key}
    params = {
        "back": days_back,
        "maxResults": max_results,
        "detail": "full"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def format_observation(obs):
    """Format a single observation for display."""
    return {
        "species": obs.get("comName", "Unknown"),
        "scientific_name": obs.get("sciName", ""),
        "count": obs.get("howMany", "X"),
        "location": obs.get("locName", "Unknown location"),
        "date": obs.get("obsDt", ""),
        "lat": obs.get("lat"),
        "lng": obs.get("lng"),
        "checklist_url": f"https://ebird.org/checklist/{obs.get('subId', '')}" if obs.get("subId") else None,
        "species_url": f"https://ebird.org/species/{obs.get('speciesCode', '')}" if obs.get("speciesCode") else None,
        "location_id": obs.get("locId", ""),
        "observer": obs.get("userDisplayName", ""),
        "is_valid": obs.get("obsValid", True),
        "is_reviewed": obs.get("obsReviewed", False)
    }


def generate_html(all_observations, config, last_updated):
    """Generate the HTML page for GitHub Pages."""

    # Group by region
    regions_html = ""
    for region_data in all_observations:
        region_name = region_data["name"]
        observations = region_data["observations"]

        if not observations:
            obs_html = "<p>No notable sightings in the past week.</p>"
        else:
            obs_items = ""
            for obs in observations:
                count_str = f"{obs['count']}" if obs['count'] != "X" else "present"
                checklist_link = f'<a href="{obs["checklist_url"]}" target="_blank">View checklist</a>' if obs["checklist_url"] else ""
                species_link = f'<a href="{obs["species_url"]}" target="_blank">{obs["species"]}</a>' if obs["species_url"] else obs["species"]

                obs_items += f"""
                <div class="observation">
                    <div class="species-name">{species_link}</div>
                    <div class="species-scientific">{obs['scientific_name']}</div>
                    <div class="details">
                        <span class="count">{count_str}</span> at
                        <span class="location">{obs['location']}</span>
                    </div>
                    <div class="meta">
                        <span class="date">{obs['date']}</span>
                        {checklist_link}
                    </div>
                </div>
                """
            obs_html = obs_items

        regions_html += f"""
        <section class="region">
            <h2>{region_name}</h2>
            <div class="observations">
                {obs_html}
            </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBird Notable Sightings</title>
    <style>
        :root {{
            --primary: #2e7d32;
            --primary-light: #4caf50;
            --bg: #f5f5f5;
            --card-bg: #ffffff;
            --text: #333333;
            --text-light: #666666;
            --border: #e0e0e0;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid var(--primary);
            margin-bottom: 30px;
        }}

        h1 {{
            color: var(--primary);
            font-size: 2rem;
            margin-bottom: 10px;
        }}

        .last-updated {{
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        .region {{
            margin-bottom: 40px;
        }}

        .region h2 {{
            color: var(--primary);
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        .observation {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-light);
        }}

        .species-name {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary);
        }}

        .species-name a {{
            color: inherit;
            text-decoration: none;
        }}

        .species-name a:hover {{
            text-decoration: underline;
        }}

        .species-scientific {{
            font-style: italic;
            color: var(--text-light);
            font-size: 0.9rem;
            margin-bottom: 8px;
        }}

        .details {{
            margin: 8px 0;
        }}

        .count {{
            font-weight: 600;
            background: var(--primary-light);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
        }}

        .location {{
            color: var(--text);
        }}

        .meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            font-size: 0.85rem;
            color: var(--text-light);
        }}

        .meta a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .meta a:hover {{
            text-decoration: underline;
        }}

        footer {{
            text-align: center;
            padding: 30px 0;
            color: var(--text-light);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}

        footer a {{
            color: var(--primary);
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}

            h1 {{
                font-size: 1.5rem;
            }}

            .observation {{
                padding: 12px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Notable Bird Sightings</h1>
            <p class="last-updated">Last updated: {last_updated}</p>
        </header>

        <main>
            {regions_html}
        </main>

        <footer>
            <p>Data from <a href="https://ebird.org" target="_blank">eBird</a> |
            Updated automatically via GitHub Actions</p>
        </footer>
    </div>
</body>
</html>
"""
    return html


def main():
    # Get API key from environment
    api_key = os.environ.get("EBIRD_API_KEY")
    if not api_key:
        raise ValueError("EBIRD_API_KEY environment variable not set")

    # Load config
    config = load_config()

    # Fetch observations for each region
    all_observations = []
    for region in config["regions"]:
        print(f"Fetching notable observations for {region['name']} ({region['code']})...")
        try:
            raw_obs = fetch_notable_observations(
                api_key,
                region["code"],
                days_back=config.get("days_back", 7),
                max_results=config.get("max_results", 100)
            )
            formatted = [format_observation(obs) for obs in raw_obs]
            all_observations.append({
                "code": region["code"],
                "name": region["name"],
                "observations": formatted
            })
            print(f"  Found {len(formatted)} notable sightings")
        except requests.exceptions.HTTPError as e:
            print(f"  Error fetching {region['code']}: {e}")
            all_observations.append({
                "code": region["code"],
                "name": region["name"],
                "observations": [],
                "error": str(e)
            })

    # Generate timestamp
    last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Create output directory
    output_dir = Path(__file__).parent / "docs"
    output_dir.mkdir(exist_ok=True)

    # Save JSON data
    json_output = {
        "last_updated": last_updated,
        "config": config,
        "regions": all_observations
    }
    with open(output_dir / "data.json", "w") as f:
        json.dump(json_output, f, indent=2)
    print(f"Saved data to {output_dir / 'data.json'}")

    # Generate and save HTML
    html = generate_html(all_observations, config, last_updated)
    with open(output_dir / "index.html", "w") as f:
        f.write(html)
    print(f"Saved HTML to {output_dir / 'index.html'}")


if __name__ == "__main__":
    main()
