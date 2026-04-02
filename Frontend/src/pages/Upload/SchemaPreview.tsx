export function SchemaPreview() {
  const schema = [
    { col: 'customer_id', type: 'object', sample: 'CUST_89210' },
    { col: 'plan_type', type: 'category', sample: 'Enterprise' },
    { col: 'monthly_spend', type: 'float64', sample: '1450.00' },
    { col: 'login_frequency', type: 'int64', sample: '42' },
    { col: 'support_tickets', type: 'int64', sample: '3' },
  ]
  
  return (
    <div className="bg-[#0F1629] border border-[#1E2A45] rounded-xl overflow-hidden shadow-xl">
      <div className="px-6 py-4 border-b border-[#1E2A45] bg-[#141E35] flex justify-between items-center">
        <h3 className="font-semibold text-white">Detected Schema</h3>
        <span className="text-xs text-slate-400 font-mono">24 columns detected</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-[#0A0D1A] text-slate-400 text-xs uppercase tracking-wider">
              <th className="px-6 py-4 font-semibold">Column Name</th>
              <th className="px-6 py-4 font-semibold">Detected Type</th>
              <th className="px-6 py-4 font-semibold">Sample Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E2A45]">
            {schema.map((row, i) => (
              <tr key={i} className="text-slate-300 text-sm hover:bg-[#1E2A45]/30 transition group">
                <td className="px-6 py-3 font-mono text-blue-400 group-hover:text-blue-300">{row.col}</td>
                <td className="px-6 py-3">
                  <span className="px-2 py-1 bg-[#1E2A45] border border-slate-700/50 rounded text-xs text-slate-300 font-mono shadow-sm">{row.type}</span>
                </td>
                <td className="px-6 py-3 text-slate-400 truncate max-w-xs">{row.sample}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
