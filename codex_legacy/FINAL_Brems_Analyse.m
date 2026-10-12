%% =========================================================================
% BIOMECHANISCHE BREMSANALYSE - MOUNTAINBIKE
% Körperhaltungseinfluss auf Bremsleistung
% =========================================================================
% Datenquelle: phyphox (Smartphone IMU)
% Positionen: Vorne, Neutral, Hinten
% Messbedingungen: 25 km/h Vollbremsung
% =========================================================================
%
% Wichtige Korrektur:
% Der Vektorbetrag |a| ist immer >= 0. Ein Hochpass daraus oszilliert um 0,
% deshalb war "a < -0.5" fast die ganze Aufnahme lang wahr — nicht die
% Bremsphase. Gravitation wird jetzt achsenweise entfernt; die
% CoM-Deceleration ist die (negative) lineare Beschleunigung |a_lin|.
% =========================================================================

clear; clc; close all;
if exist('theme', 'file'), theme('light'); end

%% KONFIGURATION
% =========================================================================

basePath = 'C:\Users\nico2\Desktop\Mountainbike\extracted';

g = 9.81;              % Gravitation [m/s²]
fc_high = 0.5;         % Hochpass: Gravitation / Drift [Hz]
fc_low = 8;            % Tiefpass: Körperschwerpunkt, nicht Rahmenrütteln [Hz]
order_high = 2;
order_low = 4;
tailCutSec = 1.5;      % Handy-Abschalt-Artefakt am Ende ignorieren
thresholdRatio = 0.20; % Bremsfenster: |a_lin| > 20% des Peaks
absThreshold = 2.0;    % Mindest-Schwellwert [m/s²]

positions = {'Vorne', 'Neutral', 'Hinten'};
colors = {[0.8510 0.3255 0.0980], [0 0.4471 0.7412], [0.4667 0.6745 0.1882]};
n_pos = length(positions);

%% DATEN LADEN (ALLE TRIALS PRO POSITION)
% =========================================================================

fprintf('\n%s\n', repmat('=', 1, 70));
fprintf('BIOMECHANISCHE BREMSANALYSE - DATENBEARBEITUNG\n');
fprintf('%s\n\n', repmat('=', 1, 70));

allItems = dir(basePath);
folders = allItems([allItems.isdir]);
folders(ismember({folders.name}, {'.', '..'})) = [];

sensorData = struct();
results_table = table();

for p = 1:n_pos
    posName = positions{p};
    matches = {};
    for f = 1:length(folders)
        if contains(folders(f).name, posName, 'IgnoreCase', true)
            matches{end+1} = folders(f).name; %#ok<AGROW>
        end
    end
    fprintf('%s: %d Trials gefunden\n', posName, length(matches));

    sensorData.(posName).trials = {};
    maxDecels = [];
    meanDecels = [];
    durations = [];
    maxJerks = [];

    for m = 1:length(matches)
        trialFolder = matches{m};
        fileAcc = fullfile(basePath, trialFolder, 'Accelerometer.csv');
        if ~isfile(fileAcc)
            warning('Accelerometer.csv nicht gefunden in %s', trialFolder);
            continue;
        end

        trial = analyzeBrakingTrial(fileAcc, fc_high, fc_low, ...
            order_high, order_low, tailCutSec, thresholdRatio, absThreshold);

        trial.name = trialFolder;
        sensorData.(posName).trials{end+1} = trial; %#ok<AGROW>

        maxDecels(end+1,1) = trial.max_decel; %#ok<AGROW>
        meanDecels(end+1,1) = trial.mean_decel; %#ok<AGROW>
        durations(end+1,1) = trial.brake_duration; %#ok<AGROW>
        maxJerks(end+1,1) = trial.max_jerk; %#ok<AGROW>

        results_table = [results_table; table( ...
            string(posName), string(trialFolder), ...
            trial.max_decel, trial.mean_decel, trial.brake_duration, trial.max_jerk, ...
            'VariableNames', {'Position', 'Trial', 'Max_Decel', 'Mean_Decel', ...
                              'Duration', 'Max_Jerk'})]; %#ok<AGROW>
    end

    sensorData.(posName).stats.max_decel_mean = mean(maxDecels, 'omitnan');
    sensorData.(posName).stats.max_decel_std  = std(maxDecels, 0, 'omitnan');
    sensorData.(posName).stats.mean_decel_mean = mean(meanDecels, 'omitnan');
    sensorData.(posName).stats.duration_mean = mean(durations, 'omitnan');
    sensorData.(posName).stats.max_jerk_mean = mean(maxJerks, 'omitnan');
    sensorData.(posName).stats.n_trials = numel(maxDecels);
    sensorData.(posName).maxDecels = maxDecels;
    sensorData.(posName).meanDecels = meanDecels;
    sensorData.(posName).maxJerks = maxJerks;

    fprintf('  max |a_lin| = %.2f ± %.2f m/s²  (n=%d)\n', ...
        sensorData.(posName).stats.max_decel_mean, ...
        sensorData.(posName).stats.max_decel_std, ...
        sensorData.(posName).stats.n_trials);
    fprintf('  Ø  |a_lin| im Fenster = %.2f m/s², Dauer = %.3f s\n\n', ...
        sensorData.(posName).stats.mean_decel_mean, ...
        sensorData.(posName).stats.duration_mean);
end

%% STATISTIK-TABELLE
% =========================================================================

fprintf('%s\n', repmat('=', 1, 70));
fprintf('ERGEBNISSE - VERGLEICH DER KÖRPERPOSITIONEN\n');
fprintf('%s\n\n', repmat('=', 1, 70));

fprintf('%-12s | %14s | %12s | %12s | %8s\n', ...
    'Position', 'Max Decel', 'Ø Decel', 'Dauer', 'n');
fprintf('%s\n', repmat('-', 1, 70));

max_decels = zeros(n_pos, 1);
for p = 1:n_pos
    posName = positions{p};
    s = sensorData.(posName).stats;
    max_decels(p) = s.max_decel_mean;
    fprintf('%-12s | %6.2f ± %-5.2f | %11.2f | %11.3f | %8d\n', ...
        posName, s.max_decel_mean, s.max_decel_std, ...
        s.mean_decel_mean, s.duration_mean, s.n_trials);
end
fprintf('%s\n\n', repmat('=', 1, 70));

%% VISUALISIERUNG 1: ROHSIGNALE (ein repräsentativer Trial pro Position)
% =========================================================================

figure('Name', 'Rohsignale', 'Position', [50 50 1200 700]);
set(gcf, 'Color', 'white');

for p = 1:n_pos
    posName = positions{p};
    trials = sensorData.(posName).trials;
    if isempty(trials), continue; end
    tr = trials{1};

    subplot(n_pos, 1, p);
    hold on;
    plot(tr.t, tr.ax, 'LineWidth', 1.2, 'Color', [0.8 0.2 0.2], 'DisplayName', 'X');
    plot(tr.t, tr.ay, 'LineWidth', 1.2, 'Color', [0.2 0.8 0.2], 'DisplayName', 'Y');
    plot(tr.t, tr.az, 'LineWidth', 1.5, 'Color', [0.2 0.2 0.8], 'DisplayName', 'Z');
    xline(tr.t_brake_start, '--k', 'HandleVisibility', 'off');
    xline(tr.t_brake_end, '--k', 'HandleVisibility', 'off');
    grid on; grid minor;
    ylabel(posName, 'FontSize', 11, 'FontWeight', 'bold');
    legend('Location', 'best', 'FontSize', 10);
    if p == n_pos
        xlabel('Zeit (s)', 'FontSize', 11);
    end
end

sgtitle('Rohsignale (1. Trial): Beschleunigung X, Y, Z — gestrichelt = Bremsfenster', ...
    'FontSize', 13, 'FontWeight', 'bold');
if exist('theme', 'file'), theme('light'); end
saveas(gcf, fullfile('C:\Users\nico2\Desktop', 'Fig01_Rohsignale.png'));

%% VISUALISIERUNG 2: CoM-DECELERATION (Peak-aligned, negativ = bremsen)
% =========================================================================

figure('Name', 'Gefilterte Signale', 'Position', [50 50 1200 600]);
set(gcf, 'Color', 'white');
hold on;

for p = 1:n_pos
    posName = positions{p};
    trials = sensorData.(posName).trials;
    col = colors{p};
    for k = 1:numel(trials)
        h = plot(trials{k}.t_rel, -trials{k}.a_lin_win, ...
            'LineWidth', 1.2, 'Color', col, 'HandleVisibility', 'off');
        if isprop(h, 'Color') && numel(h.Color) >= 3
            h.Color = [col 0.25];
        end
    end
    % Mittelkurve auf gemeinsamem Raster
    commonT = -0.4:0.002:0.4;
    M = nan(numel(trials), numel(commonT));
    for k = 1:numel(trials)
        M(k,:) = interp1(trials{k}.t_rel, -trials{k}.a_lin_win, commonT, 'linear', nan);
    end
    meanCurve = mean(M, 1, 'omitnan');
    plot(commonT, meanCurve, 'LineWidth', 2.8, 'Color', col, 'DisplayName', posName);
end

yline(0, '-', 'Color', [0.5 0.5 0.5], 'LineWidth', 1, 'HandleVisibility', 'off');
xlabel('Zeit relativ zum Peak (s)', 'FontSize', 12);
ylabel('CoM-Beschleunigung (m/s²)', 'FontSize', 12);
title('Negative CoM-Beschleunigung beim Bremsen (Einzeltrials blass, Mittelwert kräftig)', ...
    'FontSize', 13, 'FontWeight', 'bold');
grid on; grid minor;
legend('Location', 'best', 'FontSize', 11);
if exist('theme', 'file'), theme('light'); end
saveas(gcf, fullfile('C:\Users\nico2\Desktop', 'Fig02_Gefiltert.png'));

%% VISUALISIERUNG 3: BAR-CHART VERGLEICH
% =========================================================================

figure('Name', 'Statistik', 'Position', [50 50 1000 600]);
set(gcf, 'Color', 'white');

means = zeros(n_pos,1);
stdevs = zeros(n_pos,1);
for p = 1:n_pos
    means(p) = sensorData.(positions{p}).stats.max_decel_mean;
    stdevs(p) = sensorData.(positions{p}).stats.max_decel_std;
end

bar(1:n_pos, means, 0.55, 'FaceColor', [0.8510 0.3255 0.0980], ...
    'EdgeColor', 'black', 'LineWidth', 1.5, 'DisplayName', 'Mittelwert max. |a_{lin}|');
hold on;
errorbar(1:n_pos, means, stdevs, 'k.', 'LineWidth', 1.5, 'CapSize', 14, ...
    'HandleVisibility', 'off');

for p = 1:n_pos
    vals = sensorData.(positions{p}).maxDecels;
    xj = p + (rand(size(vals)) - 0.5) * 0.18;
    scatter(xj, vals, 28, 'filled', 'MarkerFaceColor', [0.2 0.2 0.2], ...
        'MarkerFaceAlpha', 0.45, 'DisplayName', 'Einzeltrials');
end

for p = 1:n_pos
    text(p, means(p) + stdevs(p) + 1.2, sprintf('%.2f', means(p)), ...
        'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold');
end

set(gca, 'XTick', 1:n_pos, 'XTickLabel', positions);
ylabel('Max. CoM-Deceleration (m/s²)', 'FontSize', 12);
title('Bremsleistung: Vergleich der Körperpositionen (Mittelwert ± Std)', ...
    'FontSize', 13, 'FontWeight', 'bold');
grid on; grid minor;
legend('FontSize', 11);
if exist('theme', 'file'), theme('light'); end
saveas(gcf, fullfile('C:\Users\nico2\Desktop', 'Fig03_Vergleich.png'));

%% VISUALISIERUNG 4: JERK-ANALYSE
% =========================================================================

figure('Name', 'Jerk-Analyse', 'Position', [50 50 1200 600]);
set(gcf, 'Color', 'white');

subplot(1, 2, 1);
hold on;
for p = 1:n_pos
    posName = positions{p};
    trials = sensorData.(posName).trials;
    col = colors{p};
    for k = 1:numel(trials)
        h = plot(trials{k}.t_rel, trials{k}.jerk_win, 'LineWidth', 1.0, 'Color', col);
        h.Color = [col 0.3];
    end
end
grid on; grid minor;
xlabel('Zeit relativ zum Peak (s)', 'FontSize', 11);
ylabel('Jerk (m/s³)', 'FontSize', 11);
title('Ruck um den Bremspeak', 'FontSize', 12, 'FontWeight', 'bold');

subplot(1, 2, 2);
jerkMeans = zeros(n_pos,1);
for p = 1:n_pos
    jerkMeans(p) = sensorData.(positions{p}).stats.max_jerk_mean;
end
bar(1:n_pos, jerkMeans, 'FaceColor', [0.4667 0.6745 0.1882], ...
    'EdgeColor', 'black', 'LineWidth', 1.5);
set(gca, 'XTick', 1:n_pos, 'XTickLabel', positions);
ylabel('Mittlerer max. Jerk (m/s³)', 'FontSize', 11);
title('Ruck pro Position', 'FontSize', 12, 'FontWeight', 'bold');
grid on;
for p = 1:n_pos
    text(p, jerkMeans(p) + 2, sprintf('%.1f', jerkMeans(p)), ...
        'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold');
end

sgtitle('Jerk-Analyse (Ruck)', 'FontSize', 13, 'FontWeight', 'bold');
if exist('theme', 'file'), theme('light'); end
saveas(gcf, fullfile('C:\Users\nico2\Desktop', 'Fig04_Jerk.png'));

%% RANKING
% =========================================================================

fprintf('\nRANKING (größte CoM-Deceleration = stärkste Bremsung):\n');
[~, ranking_idx] = sort(max_decels, 'descend');
medals = {'1.', '2.', '3.'};
for i = 1:length(ranking_idx)
    idx = ranking_idx(i);
    fprintf('  %s %s: %.2f m/s²\n', medals{i}, positions{idx}, max_decels(idx));
end
fprintf('\n');

%% EXPORT
% =========================================================================

outCsv = fullfile('C:\Users\nico2\Desktop', 'brems_results.csv');
writetable(results_table, outCsv);
fprintf('Ergebnisse gespeichert: %s\n', outCsv);


%% =========================================================================
function trial = analyzeBrakingTrial(filePath, fc_high, fc_low, ...
        order_high, order_low, tailCutSec, thresholdRatio, absThreshold)

    raw = readtable(filePath, 'VariableNamingRule', 'preserve');
    t_raw = toNumeric(raw(:, 1));
    ax_raw = toNumeric(raw(:, 2));
    ay_raw = toNumeric(raw(:, 3));
    az_raw = toNumeric(raw(:, 4));

    valid = ~isnan(t_raw) & ~isnan(ax_raw) & ~isnan(ay_raw) & ~isnan(az_raw) & (t_raw > 0);
    t_raw = t_raw(valid);
    ax_raw = ax_raw(valid);
    ay_raw = ay_raw(valid);
    az_raw = az_raw(valid);

    dt = median(diff(t_raw));
    fs = 1 / dt;
    t = (t_raw(1):dt:t_raw(end))';
    ax = interp1(t_raw, ax_raw, t, 'linear');
    ay = interp1(t_raw, ay_raw, t, 'linear');
    az = interp1(t_raw, az_raw, t, 'linear');

    Wn_high = fc_high / (fs/2);
    Wn_low  = fc_low  / (fs/2);
    [b_hp, a_hp] = butter(order_high, Wn_high, 'high');
    [b_lp, a_lp] = butter(order_low,  Wn_low,  'low');

    % Gravitation achsenweise entfernen, dann Betrag der Linearacceleration
    ax_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ax));
    ay_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, ay));
    az_lin = filtfilt(b_lp, a_lp, filtfilt(b_hp, a_hp, az));
    a_lin  = sqrt(ax_lin.^2 + ay_lin.^2 + az_lin.^2);

    jerk = gradient(a_lin, dt);

    cutIdx = min(length(t), max(1, length(t) - round(tailCutSec * fs)));
    a_valid = a_lin(1:cutIdx);
    [peakVal, peakIdx] = max(a_valid);
    threshold = max(absThreshold, thresholdRatio * peakVal);

    startIdx = peakIdx;
    while startIdx > 1 && a_valid(startIdx) > threshold
        startIdx = startIdx - 1;
    end
    endIdx = peakIdx;
    while endIdx < length(a_valid) && a_valid(endIdx) > threshold
        endIdx = endIdx + 1;
    end

    pad = round(0.4 * fs);
    plotStart = max(1, peakIdx - pad);
    plotEnd   = min(cutIdx, peakIdx + pad);

    trial.t = t;
    trial.ax = ax;
    trial.ay = ay;
    trial.az = az;
    trial.a_lin = a_lin;
    trial.fs = fs;
    trial.t_brake_start = t(startIdx);
    trial.t_brake_end = t(endIdx);
    trial.brake_duration = t(endIdx) - t(startIdx);
    trial.max_decel = peakVal;
    trial.mean_decel = mean(a_valid(startIdx:endIdx));
    trial.max_jerk = max(abs(jerk(startIdx:endIdx)));
    trial.t_rel = t(plotStart:plotEnd) - t(peakIdx);
    trial.a_lin_win = a_lin(plotStart:plotEnd);
    trial.jerk_win = jerk(plotStart:plotEnd);
end


function v = toNumeric(col)
    v = table2array(col);
    if iscell(v) || isstring(v)
        v = str2double(strrep(string(v), ',', '.'));
    end
    v = double(v);
end
