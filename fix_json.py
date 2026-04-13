import json

with open('outputs/segmentation/global_insights.json') as f:
    d = json.load(f)

with open('outputs/segmentation/segment_results.json') as f:
    segs = json.load(f)

# Calculate overall churn rate from all segments
rates = [s['churn_rate'] for s in segs if s.get('churn_rate')]
d['overall_churn_rate'] = round(sum(rates) / len(rates), 4)

# Also fix n_degrading — count accelerating as degrading for display
d['n_degrading'] = d.get('n_accelerating', 0)
d['top_degrading_segments'] = d.get('accelerating_risk_segments', [])[:3]

with open('outputs/segmentation/global_insights.json', 'w') as f:
    json.dump(d, f, indent=2)

print(f"Overall churn rate: {d['overall_churn_rate']:.1%}")
print(f"n_degrading set to: {d['n_degrading']}")
