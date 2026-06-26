"""
Test script to generate and analyze 30 loan applications
to verify the scoring engine produces varied, reasonable results
"""
import asyncio
import json
import sys
from datetime import datetime
from collections import Counter
from synthetic_data import SyntheticDataGenerator
from orchestrator import get_orchestrator

async def run_application(orchestrator, app_data, app_num):
    """Run a single application through the orchestrator"""
    try:
        # Add application_id to the data
        app_data_with_id = {**app_data, "application_id": f"TEST-{app_num:03d}"}
        result = await orchestrator.process_application(app_data_with_id)
        return result
    except Exception as e:
        print(f"Error processing application {app_num}: {e}")
        return None

async def main():
    print("=" * 80)
    print("CREDIT RISK SCORING ENGINE TEST - 30 APPLICATIONS")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize
    generator = SyntheticDataGenerator()
    orchestrator = get_orchestrator()
    
    # Generate 30 applications with distribution: 10 low, 10 medium, 10 high risk
    applications = []
    risk_profiles = ['low_risk'] * 10 + ['medium_risk'] * 10 + ['high_risk'] * 10
    
    print("Generating 30 test applications...")
    for i, risk_profile in enumerate(risk_profiles):
        app = generator.generate_application(risk_profile=risk_profile)
        applications.append({
            'app_num': i + 1,
            'risk_profile': risk_profile,
            'data': app,
            'credit_score': app['credit']['credit_score'],
            'income': app['employment']['annual_income'],
            'dti': app['financial']['monthly_debt'] / (app['employment']['annual_income'] / 12) if app['employment']['annual_income'] > 0 else 1,
        })
    
    print(f"Generated {len(applications)} applications")
    print()
    
    # Process applications (just first 5 for quick test, then analyze)
    results = []
    
    # Process sequentially to avoid overwhelming the system
    print("Processing applications through the orchestrator...")
    print("(Processing first 6 applications as sample - 2 of each risk profile)")
    
    sample_apps = applications[:2] + applications[10:12] + applications[20:22]  # 2 low, 2 medium, 2 high
    
    for app_info in sample_apps:
        print(f"\n[App {app_info['app_num']:02d}] {app_info['risk_profile'].upper()} risk | Credit: {app_info['credit_score']} | Income: ${app_info['income']:,.0f} | DTI: {app_info['dti']:.1%}")
        
        result = await run_application(orchestrator, app_info['data'], app_info['app_num'])
        
        if result and result.get('status') == 'completed':
            decision = result.get('decision', {})
            agent_results = result.get('agent_results', {})
            
            # Extract key metrics
            confidence = decision.get('confidence_score') or decision.get('confidence')
            default_prob = decision.get('default_probability')
            risk_level = decision.get('risk_level')
            percentile = decision.get('risk_percentile')
            final_decision = decision.get('decision')
            
            results.append({
                'app_num': app_info['app_num'],
                'input_risk_profile': app_info['risk_profile'],
                'credit_score': app_info['credit_score'],
                'income': app_info['income'],
                'dti': app_info['dti'],
                'decision': final_decision,
                'confidence': confidence,
                'default_prob': default_prob,
                'risk_level': risk_level,
                'percentile': percentile,
                # Agent confidences
                'agent_confidences': {
                    name: data.get('confidence', data.get('confidence_score', 'N/A'))
                    for name, data in agent_results.items()
                }
            })
            
            print(f"    → Decision: {final_decision} | Confidence: {confidence:.1%} | Default Prob: {default_prob:.1%} | Risk: {risk_level} | Percentile: {percentile}")
            
            # Show agent confidence variation
            agent_confs = [v for v in results[-1]['agent_confidences'].values() if isinstance(v, (int, float))]
            if agent_confs:
                print(f"    → Agent Confidences: min={min(agent_confs):.1%}, max={max(agent_confs):.1%}, range={max(agent_confs)-min(agent_confs):.1%}")
        else:
            print(f"    → FAILED to process")
    
    print()
    print("=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    if not results:
        print("No results to analyze!")
        return
    
    # Analyze results
    decisions = Counter(r['decision'] for r in results)
    risk_levels = Counter(r['risk_level'] for r in results)
    
    print(f"\nDecision Distribution:")
    for dec, count in decisions.items():
        print(f"  {dec}: {count} ({count/len(results)*100:.0f}%)")
    
    print(f"\nRisk Level Distribution:")
    for risk, count in risk_levels.items():
        print(f"  {risk}: {count} ({count/len(results)*100:.0f}%)")
    
    confidences = [r['confidence'] for r in results if r['confidence'] is not None]
    default_probs = [r['default_prob'] for r in results if r['default_prob'] is not None]
    percentiles = [r['percentile'] for r in results if r['percentile'] is not None]
    
    print(f"\nConfidence Scores:")
    print(f"  Range: {min(confidences):.1%} - {max(confidences):.1%}")
    print(f"  Unique values: {len(set(round(c, 2) for c in confidences))}")
    
    print(f"\nDefault Probabilities:")
    print(f"  Range: {min(default_probs):.1%} - {max(default_probs):.1%}")
    print(f"  Unique values: {len(set(round(d, 2) for d in default_probs))}")
    
    print(f"\nPercentiles:")
    print(f"  Range: {min(percentiles)} - {max(percentiles)}")
    print(f"  Unique values: {len(set(percentiles))}")
    
    print("\n" + "=" * 80)
    print("CORRELATION CHECK: Input Risk Profile vs Output Risk Level")
    print("=" * 80)
    
    for r in results:
        match = "✓" if (
            (r['input_risk_profile'] == 'low' and r['risk_level'] in ['Low', 'Medium']) or
            (r['input_risk_profile'] == 'medium' and r['risk_level'] in ['Low', 'Medium', 'High']) or
            (r['input_risk_profile'] == 'high' and r['risk_level'] in ['Medium', 'High', 'Critical'])
        ) else "✗"
        print(f"  App {r['app_num']:02d}: Input={r['input_risk_profile']:6s} → Output={r['risk_level']:8s} {match}")
    
    print("\n" + "=" * 80)
    print("DETAILED RESULTS TABLE")
    print("=" * 80)
    print(f"{'App':>4} | {'Profile':>7} | {'Credit':>6} | {'Income':>10} | {'Decision':>12} | {'Conf':>6} | {'DefProb':>7} | {'Risk':>8} | {'%ile':>4}")
    print("-" * 95)
    for r in results:
        print(f"{r['app_num']:4d} | {r['input_risk_profile']:>7} | {r['credit_score']:>6} | ${r['income']:>9,.0f} | {r['decision']:>12} | {r['confidence']*100:>5.1f}% | {r['default_prob']*100:>6.1f}% | {r['risk_level']:>8} | {r['percentile']:>4}")
    
    print("\n" + "=" * 80)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
