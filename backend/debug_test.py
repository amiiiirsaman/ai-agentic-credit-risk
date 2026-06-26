"""Debug test with rate limiting to avoid Bedrock throttling"""
import asyncio
import traceback
from orchestrator import get_orchestrator
from synthetic_data import SyntheticDataGenerator

async def test_one(orch, risk_profile):
    app = SyntheticDataGenerator.generate_application(risk_profile)
    credit = app['credit']['credit_score']
    income = app['employment']['annual_income']
    
    try:
        result = await orch.process_application(app)
        if result.get('status') == 'completed':
            decision = result.get('decision', {})
            return {
                'status': 'ok',
                'credit': credit,
                'income': income,
                'decision': decision.get('decision'),
                'confidence': decision.get('confidence_score', 0),
                'default_prob': decision.get('default_probability', 0),
                'risk_level': decision.get('risk_level')
            }
        else:
            return {'status': 'error', 'error': result.get('error'), 'credit': credit}
    except Exception as e:
        return {'status': 'exception', 'error': str(e), 'credit': credit}

async def main():
    orch = get_orchestrator()
    
    for profile in ['low_risk', 'medium_risk', 'high_risk']:
        print(f"\n=== Testing {profile.upper()} ===")
        # Run 2 tests per profile
        for i in range(2):
            r = await test_one(orch, profile)
            if r['status'] == 'ok':
                print(f"  [{i+1}] Credit={r['credit']:3d} -> {r['decision']:10s} | Conf={r['confidence']:.1%} | DefProb={r['default_prob']:.1%} | Risk={r['risk_level']}")
            else:
                print(f"  [{i+1}] Credit={r['credit']:3d} -> FAILED: {r.get('error', 'unknown')[:50]}")
            
            # Long delay between tests (10 seconds) to avoid Bedrock throttling
            print("    Waiting 10s before next test...")
            await asyncio.sleep(10.0)

if __name__ == "__main__":
    asyncio.run(main())
