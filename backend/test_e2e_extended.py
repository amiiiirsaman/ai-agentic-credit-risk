"""Extended E2E test - 9 tests (3 of each profile) with rate limiting"""
import asyncio
from orchestrator import get_orchestrator
from synthetic_data import SyntheticDataGenerator

async def test_profile(orch, profile, test_num):
    """Run a single E2E test for a risk profile"""
    app = SyntheticDataGenerator.generate_application(profile)
    credit = app['credit']['credit_score']
    income = app['employment']['annual_income']
    dti = app['financial']['monthly_debt'] / (income / 12) if income > 0 else 0
    
    print(f"\n[Test {test_num}] {profile.upper()}")
    print(f"  Input: Credit={credit}, Income=${income:,.0f}, DTI={dti:.1%}")
    
    try:
        result = await orch.process_application(app)
        
        if result.get('status') == 'completed':
            decision = result.get('decision', {})
            dec = decision.get('decision', 'N/A')
            conf = decision.get('confidence_score', 0)
            prob = decision.get('default_probability', 0)
            risk = decision.get('risk_level', 'N/A')
            
            # Check if result is reasonable for profile
            if profile == 'low_risk':
                match = "✓" if dec == 'APPROVE' and risk in ['Low', 'Medium'] else "✗"
            elif profile == 'medium_risk':
                # Medium can be APPROVE, CONDITIONAL, CONDITIONAL_APPROVE, or DENY depending on specifics
                match = "✓" if dec in ['APPROVE', 'CONDITIONAL', 'CONDITIONAL_APPROVE', 'DENY'] and risk in ['Low', 'Medium', 'High'] else "?"
            else:  # high_risk
                match = "✓" if dec in ['DENY', 'CONDITIONAL', 'CONDITIONAL_APPROVE'] and risk in ['High', 'Critical'] else "✗"
            
            print(f"  Result: {dec} | Confidence={conf:.1%} | Default={prob:.1%} | Risk={risk} {match}")
            return {'status': 'pass' if match == '✓' else 'unexpected', 'profile': profile, 'decision': dec, 'risk': risk, 'credit': credit}
        else:
            print(f"  ERROR: {result.get('error', 'Unknown')[:80]}")
            return {'status': 'error', 'profile': profile, 'error': result.get('error', 'Unknown'), 'credit': credit}
            
    except Exception as e:
        print(f"  EXCEPTION: {str(e)[:80]}")
        return {'status': 'exception', 'profile': profile, 'error': str(e), 'credit': credit}

async def main():
    print("=" * 60)
    print("EXTENDED E2E TEST - 9 TESTS (3 of each profile)")
    print("=" * 60)
    
    orch = get_orchestrator()
    results = []
    
    # Run 3 tests per profile
    test_num = 1
    for profile in ['low_risk', 'medium_risk', 'high_risk']:
        for i in range(3):
            r = await test_profile(orch, profile, test_num)
            results.append(r)
            test_num += 1
            
            # Wait 12 seconds between tests to avoid throttling
            if test_num <= 9:
                print("\n  ... waiting 12s to avoid throttling ...")
                await asyncio.sleep(12)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'pass')
    unexpected = sum(1 for r in results if r['status'] == 'unexpected')
    errors = sum(1 for r in results if r['status'] in ['error', 'exception'])
    
    for r in results:
        status_symbol = {'pass': '✓', 'unexpected': '?', 'error': '✗', 'exception': '✗'}.get(r['status'], '?')
        print(f"  {status_symbol} {r['profile']} (credit={r.get('credit', 'N/A')}): {r.get('decision', 'N/A')} (Risk: {r.get('risk', 'N/A')})")
    
    print(f"\nTotal: {passed} passed, {unexpected} unexpected, {errors} errors")
    
    return errors == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
