"""Quick E2E test - 3 tests (LOW, MEDIUM, HIGH) with longer delays to avoid throttling"""
import asyncio
from orchestrator import get_orchestrator
from synthetic_data import SyntheticDataGenerator

async def test_profile(orch, profile, test_num):
    """Run a single E2E test for a risk profile"""
    app = SyntheticDataGenerator.generate_application(profile)
    credit = app['credit']['credit_score']
    income = app['employment']['annual_income']
    dti = app.get('loan', {}).get('loan_amount', 0) / max(income, 1) * 12
    
    print(f"\n[Test {test_num}] {profile.upper()}")
    print(f"  Input: Credit={credit}, Income=${income:,.0f}, DTI-approx={dti:.2%}")
    
    try:
        result = await orch.process_application(app)
        
        if result.get('status') == 'completed':
            decision = result.get('decision', {})
            dec = decision.get('decision', 'N/A')
            conf = decision.get('confidence_score', 0)
            prob = decision.get('default_probability', 0)
            risk = decision.get('risk_level', 'N/A')
            
            # Expected outcomes
            expected = {
                'low_risk': ('APPROVE', ['Low', 'Moderate']),
                'medium_risk': ('APPROVE', ['Low', 'Moderate', 'High']),  # Could be approve with conditions
                'high_risk': ('DENY', ['High', 'Critical'])
            }
            exp_dec, exp_risks = expected.get(profile, ('?', []))
            
            # Check if result matches expectations
            match = "✓" if (
                (profile == 'low_risk' and dec == 'APPROVE' and risk in exp_risks) or
                (profile == 'medium_risk' and dec in ['APPROVE', 'CONDITIONAL_APPROVE']) or
                (profile == 'high_risk' and dec in ['DENY', 'CONDITIONAL_APPROVE'] and risk in exp_risks)
            ) else "✗"
            
            print(f"  Result: {dec} | Confidence={conf:.1%} | Default={prob:.1%} | Risk={risk} {match}")
            return {'status': 'pass' if match == '✓' else 'unexpected', 'profile': profile, 'decision': dec, 'risk': risk}
        else:
            print(f"  ERROR: {result.get('error', 'Unknown')[:80]}")
            return {'status': 'error', 'profile': profile, 'error': result.get('error', 'Unknown')}
            
    except Exception as e:
        print(f"  EXCEPTION: {str(e)[:80]}")
        return {'status': 'exception', 'profile': profile, 'error': str(e)}

async def main():
    print("=" * 60)
    print("QUICK E2E TEST - 3 PROFILES (LOW, MEDIUM, HIGH)")
    print("=" * 60)
    
    orch = get_orchestrator()
    results = []
    profiles = ['low_risk', 'medium_risk', 'high_risk']
    
    for i, profile in enumerate(profiles):
        r = await test_profile(orch, profile, i + 1)
        results.append(r)
        
        # Wait 15 seconds between tests to avoid throttling
        if i < len(profiles) - 1:
            print("\n  ... waiting 15s to avoid throttling ...")
            await asyncio.sleep(15)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'pass')
    unexpected = sum(1 for r in results if r['status'] == 'unexpected')
    errors = sum(1 for r in results if r['status'] in ['error', 'exception'])
    
    for r in results:
        status_symbol = {'pass': '✓', 'unexpected': '?', 'error': '✗', 'exception': '✗'}.get(r['status'], '?')
        print(f"  {status_symbol} {r['profile']}: {r.get('decision', 'N/A')} (Risk: {r.get('risk', 'N/A')})")
    
    print(f"\nTotal: {passed} passed, {unexpected} unexpected, {errors} errors")
    
    return passed == 3

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
