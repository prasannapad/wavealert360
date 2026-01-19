import azure.functions as func
import json
import logging
import os
from datetime import datetime

app = func.FunctionApp()

def load_scenario(scenario_name):
    """Load a scenario - hardcoded for now to ensure it works"""
    
    scenarios = {
        "normal_conditions": {
            "type": "FeatureCollection",
            "features": [],
            "title": "Current Watches, Warnings and Advisories for Cheboygan County Lake Huron Areas",
            "updated": "2025-08-10T10:30:00Z"
        },
        "high_surf_advisory": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "https://api.weather.gov/alerts/urn:oid:mock.high.surf.advisory.california",
                    "type": "Feature",
                    "properties": {
                        "event": "High Surf Advisory",
                        "headline": "High Surf Advisory issued August 09 at 3:03PM PDT until August 10 at 5:25PM PDT by NWS San Francisco Bay Area CA",
                        "description": "* WHAT...Large breaking waves of 3 to 6 feet expected along the Lake Huron shoreline.\n\n* WHERE...Cheboygan County including Cheboygan State Park Beach area.\n\n* WHEN...From 3:25 PM EDT August 18 until 9:00 PM EDT August 18.\n\n* IMPACTS...Dangerous swimming conditions and localized beach erosion. Breaking waves can sweep people off piers and breakwaters. Life-threatening swimming conditions. Strong rip currents possible along Lake Huron shoreline.",
                        "severity": "Moderate",
                        "certainty": "Likely",
                        "urgency": "Expected",
                        "areaDesc": "Cheboygan County Lake Huron Areas",
                        "sent": "2025-08-09T22:03:00Z",
                        "effective": "2025-08-09T22:03:00Z",
                        "onset": "2025-08-10T22:25:00Z",
                        "expires": "2025-08-11T00:25:00Z",
                        "ends": "2025-08-11T00:25:00Z",
                        "instruction": "Inexperienced swimmers should remain out of the water due to dangerous surf conditions. Stay off of piers, breakwaters, and other waterside infrastructure. Beware of dangerous rip currents at Cheboygan State Park Beach on Lake Huron."
                    }
                }
            ],
            "title": "Current Watches, Warnings and Advisories for Cheboygan County Lake Huron Areas"
        },
        "coastal_flood_warning": {
            "type": "FeatureCollection", 
            "features": [
                {
                    "id": "https://api.weather.gov/alerts/urn:oid:mock.coastal.flood.warning",
                    "type": "Feature",
                    "properties": {
                        "event": "Coastal Flood Warning",
                        "headline": "Coastal Flood Warning issued",
                        "description": "* WHAT...Minor coastal flooding of 1 to 3 feet above normal high tide levels.\n\n* WHERE...Coastal areas.\n\n* IMPACTS...Flooding of lots, parks, and roads expected.",
                        "severity": "Moderate",
                        "certainty": "Likely", 
                        "urgency": "Expected",
                        "areaDesc": "Coastal Areas"
                    }
                }
            ],
            "title": "Current Watches, Warnings and Advisories"
        }
    }
    
    return scenarios.get(scenario_name)

@app.route(route="alerts/active", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def mock_nws_alerts(req: func.HttpRequest) -> func.HttpResponse:
    """Mock NWS alerts API endpoint with scenario support"""
    
    logging.info('Mock NWS API request received')
    
    # Get scenario parameter
    scenario = req.params.get('scenario', 'normal_conditions')
    logging.info(f'Using scenario: {scenario}')
    
    # Load the requested scenario
    scenario_data = load_scenario(scenario)
    
    if scenario_data is None:
        # Fallback to default empty response
        scenario_data = {
            "type": "FeatureCollection",
            "features": [],
            "title": "Current Watches, Warnings and Advisories",
            "updated": datetime.utcnow().isoformat() + "Z"
        }
        logging.warning(f'Scenario {scenario} not found, using empty response')
    
    # Update timestamp
    scenario_data["updated"] = datetime.utcnow().isoformat() + "Z"
    
    logging.info(f"Returning response with {len(scenario_data.get('features', []))} alerts")
    
    return func.HttpResponse(
        json.dumps(scenario_data, indent=2),
        status_code=200,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache"
        }
    )

@app.route(route="scenarios", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)  
def list_scenarios(req: func.HttpRequest) -> func.HttpResponse:
    """List available test scenarios"""
    
    scenarios = {
        "available_scenarios": [
            "normal_conditions",      # No alerts - shows as NORMAL
            "high_surf_advisory",     # High Surf Advisory - shows as HIGH  
            "coastal_flood_warning",  # Coastal Flood Warning - shows as HIGH
            "rip_current_statement",  # Rip Current Statement - shows as HIGH
            "rip_current_california"  # California Rip Current - shows as HIGH
        ],
        "usage": "Add ?scenario=<name> to alerts/active endpoint",
        "examples": {
            "normal": "alerts/active?scenario=normal_conditions",
            "high_alert": "alerts/active?scenario=high_surf_advisory"
        },
        "default": "normal_conditions (if no scenario specified)"
    }
    
    return func.HttpResponse(
        json.dumps(scenarios, indent=2),
        status_code=200,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*"
        }
    )
