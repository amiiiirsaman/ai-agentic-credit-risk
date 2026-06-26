"""Quick test to submit one application via HTTP and check the result"""
import requests
import json
import random
import time

BASE_URL = "http://localhost:8000/api/v1"

def get_synthetic_app():
    """Get a synthetic application from the API"""
    response = requests.get(f"{BASE_URL}/synthetic/application")
    if response.status_code != 200:
        print(f"Error getting synthetic app: {response.status_code} - {response.text}")
        return None
    return response.json()

def submit_application(app_data):
    """Submit an application and return the result"""
    response = requests.post(f"{BASE_URL}/applications", json=app_data)
    print(f"Submit response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error submitting application: {response.status_code} - {response.text[:200]}")
        return None
    data = response.json()
    print(f"Submit response: {data}")
    return data

def trigger_underwriting(app_id):
    """Trigger the underwriting process"""
    response = requests.post(f"{BASE_URL}/underwrite/{app_id}")
    if response.status_code not in [200, 202]:
        print(f"Error triggering underwriting: {response.status_code} - {response.text}")
        return None
    return response.json()

def get_decision(app_id, retries=30, delay=3):
    """Get the decision for an application, with retries"""
    for i in range(retries):
        response = requests.get(f"{BASE_URL}/decisions/{app_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("chief_underwriter"):
                return data
            print(f"  Waiting for decision... ({i+1}/{retries})")
        elif response.status_code == 202:
            print(f"  Processing... ({i+1}/{retries})")
        elif response.status_code != 404:
            print(f"Error getting decision: {response.status_code}")
            return None
        time.sleep(delay)
    return None

def main():
    print("=" * 60)
    print("QUICK TEST - Using Synthetic Data Generator")
    print("=" * 60)
    
    results = []
    
    for i in range(3):
        print(f"\n--- Test Application {i+1} ---")
        
        # Get synthetic app
        app_data = get_synthetic_app()
        if not app_data:
            continue
        
        risk_profile = app_data.get("_metadata", {}).get("risk_profile", "unknown")
        credit_score = app_data.get("credit", {}).get("credit_score", "N/A")
        income = app_data.get("employment", {}).get("annual_income", 0)
        
        print(f"Profile: {risk_profile} | Credit: {credit_score} | Income: ${income:,}")
        
        # Submit application
        result = submit_application(app_data)
        if not result:
            continue
        
        app_id = result.get("application_id") or result.get("id")
        print(f"Application ID: {app_id}")
        
        # Trigger underwriting
        print("Triggering underwriting...")
        trigger_underwriting(app_id)
        
        # Wait and get decision
        decision = get_decision(app_id)
        if decision:
            chief = decision.get("chief_underwriter", {})
            conf = chief.get("confidence_score", chief.get("confidence", "N/A"))
            def_prob = chief.get("default_probability", "N/A")
            risk = chief.get("risk_level", "N/A")
            dec = chief.get("decision", "N/A")
            pctl = chief.get("risk_percentile", "N/A")
            
            print(f"\nRESULT:")
            print(f"  Decision: {dec}")
            print(f"  Confidence: {conf}")
            print(f"  Default Prob: {def_prob}")
            print(f"  Risk Level: {risk}")
            print(f"  Percentile: {pctl}")
            
            results.append({
                "profile": risk_profile,
                "credit": credit_score,
                "decision": dec,
                "confidence": conf,
                "default_prob": def_prob,
                "risk": risk
            })
        else:
            print("Could not get decision in time")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"{r['profile']:12} | Credit: {r['credit']:4} | {r['decision']:12} | Conf: {r['confidence']} | Def: {r['default_prob']} | Risk: {r['risk']}")

if __name__ == "__main__":
    main()
