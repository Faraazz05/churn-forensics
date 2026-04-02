% =============================================================
% Customer Health Forensics System — Phase 4
% Octave: PSI Mathematical Validation
% =============================================================
% Independent mathematical implementation of PSI.
% Cross-validates Python PSI engine output.
%
% Called by octave_runner.py:
%   octave --no-gui --quiet psi_validation.m <ref_csv> <cur_csv> <psi_csv> <output_json>
%
% Reads:
%   ref_csv  — reference period feature data
%   cur_csv  — current period feature data
%   psi_csv  — Python-computed PSI results to cross-check
%
% Outputs:
%   output_json — per-feature PSI comparison + agreement flags
% =============================================================

% ── Parse arguments ────────────────────────────────────────────
args = argv();
if length(args) >= 1; ref_csv  = args{1}; else; ref_csv  = 'ref_data.csv'; end
if length(args) >= 2; cur_csv  = args{2}; else; cur_csv  = 'cur_data.csv'; end
if length(args) >= 3; psi_csv  = args{3}; else; psi_csv  = 'psi_results.csv'; end
if length(args) >= 4; out_json = args{4}; else; out_json = 'octave_psi_output.json'; end

fprintf('[Octave] PSI Validation\n');
fprintf('[Octave] Ref:  %s\n', ref_csv);
fprintf('[Octave] Cur:  %s\n', cur_csv);

% ── PSI computation function ───────────────────────────────────
function psi_val = compute_psi(ref_vals, cur_vals, n_bins)
  if nargin < 3; n_bins = 10; end
  EPS = 1e-6;

  % Build breakpoints on reference distribution
  pcts        = linspace(0, 100, n_bins + 1);
  breakpoints = prctile(ref_vals, pcts);
  breakpoints = unique(breakpoints);

  if length(breakpoints) < 2
    psi_val = NaN;
    return;
  end

  % Bin counts
  ref_counts = histc(ref_vals, breakpoints)(1:end-1);
  cur_counts = histc(cur_vals, breakpoints)(1:end-1);

  % Proportions
  ref_pct = ref_counts / (sum(ref_counts) + EPS);
  cur_pct = cur_counts / (sum(cur_counts) + EPS);

  % Avoid log(0)
  ref_pct(ref_pct == 0) = EPS;
  cur_pct(cur_pct == 0) = EPS;

  % PSI formula
  psi_val = sum((cur_pct - ref_pct) .* log(cur_pct ./ ref_pct));
end

% ── PSI status function ────────────────────────────────────────
function status = psi_status(psi_val)
  if psi_val < 0.10
    status = 'stable';
  elseif psi_val < 0.20
    status = 'monitor';
  else
    status = 'significant_drift';
  end
end

% ── Load CSVs ──────────────────────────────────────────────────
ref_data  = csvread(ref_csv,  1, 0);
cur_data  = csvread(cur_csv,  1, 0);

% Load Python PSI results for cross-check
py_features = {};
py_psi_vals = [];
if exist(psi_csv, 'file')
  fid = fopen(psi_csv, 'r');
  header = fgetl(fid);   % skip header
  col_idx = 1;           % assumes feature=col1, psi=col2
  row = 1;
  while ~feof(fid)
    line = fgetl(fid);
    if ischar(line)
      parts = strsplit(line, ',');
      if length(parts) >= 2
        py_features{end+1} = strtrim(parts{1});
        py_psi_vals(end+1) = str2double(strtrim(parts{2}));
      end
    end
    row++;
  end
  fclose(fid);
  fprintf('[Octave] Loaded %d Python PSI values from %s\n', length(py_psi_vals), psi_csv);
end

% ── Validate per-column PSI ────────────────────────────────────
n_cols   = min(size(ref_data, 2), size(cur_data, 2));
results  = {};
n_agree  = 0;
n_total  = 0;

fprintf('[Octave] Validating %d numeric columns\n', n_cols);

for col = 1:n_cols
  ref_vals = ref_data(:, col);
  cur_vals = cur_data(:, col);

  % Remove NaN
  ref_vals = ref_vals(~isnan(ref_vals));
  cur_vals = cur_vals(~isnan(cur_vals));

  if length(ref_vals) < 30 || length(cur_vals) < 30
    continue;
  end

  oct_psi   = compute_psi(ref_vals, cur_vals, 10);
  oct_status = psi_status(oct_psi);

  entry.column     = col;
  entry.octave_psi = round(oct_psi, 6);
  entry.status     = oct_status;
  entry.agreement  = false;
  entry.python_psi = NaN;
  entry.delta      = NaN;

  % Cross-check against Python PSI if available
  if col <= length(py_psi_vals)
    py_val = py_psi_vals(col);
    delta  = abs(oct_psi - py_val);
    entry.python_psi = round(py_val, 6);
    entry.delta      = round(delta, 6);
    entry.agreement  = delta < 0.01;

    if entry.agreement
      n_agree++;
    end
    n_total++;

    fprintf('[Octave] Col %2d: Oct_PSI=%.4f  Py_PSI=%.4f  delta=%.4f  %s\n',
            col, oct_psi, py_val, delta,
            ifelse(entry.agreement, 'AGREE', 'DIFF'));
  else
    fprintf('[Octave] Col %2d: Oct_PSI=%.4f  status=%s\n',
            col, oct_psi, oct_status);
  end

  results{end+1} = entry;
end

% ── Distribution shift mathematical validation ─────────────────
fprintf('[Octave] Running distribution shift validation...\n');

% For the first 5 features: compute KL divergence as additional cross-check
kl_results = {};
N_BINS_KL  = 20;

for col = 1:min(5, n_cols)
  ref_vals = ref_data(:, col);
  cur_vals = cur_data(:, col);
  ref_vals = ref_vals(~isnan(ref_vals));
  cur_vals = cur_vals(~isnan(cur_vals));

  if length(ref_vals) < 50 || length(cur_vals) < 50
    continue;
  end

  all_vals    = [ref_vals; cur_vals];
  edges       = linspace(min(all_vals), max(all_vals), N_BINS_KL + 1);
  ref_hist    = histc(ref_vals, edges)(1:end-1);
  cur_hist    = histc(cur_vals, edges)(1:end-1);

  EPS = 1e-6;
  ref_p = ref_hist / (sum(ref_hist) + EPS);
  cur_p = cur_hist / (sum(cur_hist) + EPS);
  ref_p(ref_p == 0) = EPS;
  cur_p(cur_p == 0) = EPS;

  kl_div = sum(cur_p .* log(cur_p ./ ref_p));

  kl_entry.column     = col;
  kl_entry.kl_divergence = round(kl_div, 6);
  kl_entry.significant   = kl_div > 0.05;
  kl_results{end+1} = kl_entry;

  fprintf('[Octave] Col %d KL-divergence: %.4f  %s\n',
          col, kl_div, ifelse(kl_div > 0.05, '(significant)', '(stable)'));
end

% ── Build JSON output ──────────────────────────────────────────
fid = fopen(out_json, 'w');
fprintf(fid, '{\n');
fprintf(fid, '  "tool": "Octave",\n');
fprintf(fid, '  "n_columns_validated": %d,\n', length(results));
fprintf(fid, '  "n_psi_agreements": %d,\n', n_agree);
fprintf(fid, '  "n_psi_crosschecked": %d,\n', n_total);
fprintf(fid, '  "agreement_rate": %.4f,\n',
        ifelse(n_total > 0, n_agree / n_total, 0));
fprintf(fid, '  "validation_passed": %s,\n',
        ifelse(n_total == 0 || (n_agree / n_total) >= 0.90, 'true', 'false'));

fprintf(fid, '  "psi_results": [\n');
for i = 1:length(results)
  r = results{i};
  fprintf(fid, '    {\n');
  fprintf(fid, '      "column": %d,\n', r.column);
  fprintf(fid, '      "octave_psi": %.6f,\n', r.octave_psi);
  fprintf(fid, '      "status": "%s",\n', r.status);
  if ~isnan(r.python_psi)
    fprintf(fid, '      "python_psi": %.6f,\n', r.python_psi);
    fprintf(fid, '      "delta": %.6f,\n', r.delta);
    fprintf(fid, '      "agreement": %s\n', ifelse(r.agreement, 'true', 'false'));
  else
    fprintf(fid, '      "python_psi": null,\n');
    fprintf(fid, '      "delta": null,\n');
    fprintf(fid, '      "agreement": null\n');
  end
  if i < length(results)
    fprintf(fid, '    },\n');
  else
    fprintf(fid, '    }\n');
  end
end
fprintf(fid, '  ],\n');

fprintf(fid, '  "kl_divergence_results": [\n');
for i = 1:length(kl_results)
  k = kl_results{i};
  fprintf(fid, '    {"column": %d, "kl_divergence": %.6f, "significant": %s}',
          k.column, k.kl_divergence, ifelse(k.significant, 'true', 'false'));
  if i < length(kl_results)
    fprintf(fid, ',\n');
  else
    fprintf(fid, '\n');
  end
end
fprintf(fid, '  ]\n');
fprintf(fid, '}\n');
fclose(fid);

fprintf('[Octave] Output written to: %s\n', out_json);
fprintf('[Octave] Agreement rate: %d/%d (%.1f%%)\n',
        n_agree, n_total, ifelse(n_total > 0, n_agree/n_total*100, 0));
fprintf('[Octave] psi_validation.m complete.\n');
