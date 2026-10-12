%% =========================================================================
% AUTOMATISCHE BREMSPHASEN-ERKENNUNG (ohne Plots)
% =========================================================================

clear; clc;

% ---- KONFIGURATION ----
basePath = 'C:\Users\nico2\Desktop\Mountainbike\extracted';
positions = {'Vorne', 'Neutral', 'Hinten'};

fs = 400;               % Sampling-Frequenz [Hz]
g = 9.81;                % Gravitation [m/s^2]
tailCutSec = 1.5;        % Letzte X Sekunden ignorieren (Handy-Abschalt-Peak!)
thresholdRatio = 0.2;    % Bremsphase = solange Signal > 20% des Peaks

% ---- ANALYSE FÜR ALLE POSITIONEN (alle Trials!) ----
results = table();
signals = struct('Vorne', {{}}, 'Neutral', {{}}, 'Hinten', {{}});  % sammelt Zeitreihen pro Position

for p = 1:length(positions)
    posName = positions{p};
    
    % Alle Ordner finden, die zur Position passen
    allItems = dir(basePath);
    folders = allItems([allItems.isdir]);
    folders(ismember({folders.name}, {'.', '..'})) = [];
    
    matches = {};
    for f = 1:length(folders)
        if contains(folders(f).name, posName, 'IgnoreCase', true)
            matches{end+1} = folders(f).name; %#ok<AGROW>
        end
    end
    fprintf('%s: %d Trials gefunden\n', posName, length(matches));
    
    % JEDEN Trial einzeln analysieren
    for m = 1:length(matches)
        trialFolder = matches{m};
        filePath = fullfile(basePath, trialFolder, 'Accelerometer.csv');
        [res, t_win, mag_win] = analyzeBraking(filePath, fs, g, tailCutSec, thresholdRatio);
        res.Position = string(posName);
        res.Trial = string(trialFolder);
        results = [results; res]; %#ok<AGROW>
        
        if ~isempty(t_win)
            signals.(posName){end+1} = struct('t', t_win, 'mag', mag_win);
        end
    end
end

results = results(:, ["Position", "Trial", "t_start", "t_end", "duration", "max_decel", "mean_decel"]);
disp(results)

% ---- FEHLGESCHLAGENE TRIALS ANZEIGEN ----
failed = results(isnan(results.max_decel), :);
if height(failed) > 0
    fprintf('\n%d Trial(s) fehlgeschlagen (NaN-Daten, bitte pruefen):\n', height(failed));
    disp(failed(:, ["Position","Trial"]))
end

% ---- ZUSAMMENFASSUNG PRO POSITION (Mittelwert ± Std ueber alle Trials) ----
valid = results(~isnan(results.max_decel), :);

posNames = unique(valid.Position);
summary = table();
for i = 1:length(posNames)
    sub = valid(valid.Position == posNames(i), :);
    row.Position       = posNames(i);
    row.N_Trials        = height(sub);
    row.MaxDecel_mean   = mean(sub.max_decel);
    row.MaxDecel_std    = std(sub.max_decel);
    row.Dauer_mean_s    = mean(sub.duration);
    row.Dauer_std_s     = std(sub.duration);
    summary = [summary; struct2table(row)]; %#ok<AGROW>
end

fprintf('\n=== ZUSAMMENFASSUNG (Mittelwert ueber alle gueltigen Trials) ===\n');
disp(summary)

% ---- PLOT ----
posOrder = categorical(summary.Position, {'Vorne','Neutral','Hinten'});

figure;
bar(posOrder, summary.MaxDecel_mean, 'FaceColor', [0.7 0.7 0.9]);
hold on;
errorbar(posOrder, summary.MaxDecel_mean, summary.MaxDecel_std, ...
    'k.', 'LineWidth', 1.5, 'CapSize', 12);

% Einzelne Trials als Punkte darüberlegen (leicht verstreut)
for i = 1:height(summary)
    sub = valid(valid.Position == summary.Position(i), :);
    xJitter = i + (rand(height(sub),1)-0.5)*0.15;
    scatter(xJitter, sub.max_decel, 25, 'r', 'filled', 'MarkerFaceAlpha', 0.5);
end

ylabel('Max. Deceleration (m/s^2)');
title('Bremsleistung pro Koerperposition (Mittelwert ± Std, Einzeltrials in rot)');
theme('light');

% ---- LINE PLOT: Bremskurven aller Trials (am Peak ausgerichtet) ----
figure;
posColors = [0.85 0.33 0.10; 0 0.45 0.74; 0.47 0.67 0.19];  % Vorne, Neutral, Hinten

for i = 1:length(positions)
    subplot(1, 3, i);
    hold on;
    trials = signals.(positions{i});
    for k = 1:length(trials)
        plot(trials{k}.t, trials{k}.mag, 'Color', posColors(i,:), 'LineWidth', 1);
    end
    yline(0, 'k:');
    xline(0, 'k:');
    title(sprintf('%s (n=%d)', positions{i}, length(trials)));
    xlabel('Zeit relativ zum Peak (s)');
    ylabel('Beschleunigung (m/s^2)');
    grid on;
end
sgtitle('Bremskurven aller Trials, zeitlich am Peak ausgerichtet');
theme('light');

% ---- LINE PLOT: Mittelwertkurve ± Std pro Position ----
commonT = -0.2:1/fs:0.3;   % gemeinsames Zeitraster (relativ zum Peak)

figure;
for i = 1:length(positions)
    subplot(1, 3, i);
    hold on;
    trials = signals.(positions{i});
    
    % Alle Trials auf gemeinsames Zeitraster interpolieren
    M = NaN(length(trials), length(commonT));
    for k = 1:length(trials)
        M(k,:) = interp1(trials{k}.t, trials{k}.mag, commonT, 'linear', NaN);
    end
    
    meanCurve = mean(M, 1, 'omitnan');
    stdCurve  = std(M, 0, 1, 'omitnan');
    
    % Nur Bereich plotten, wo genug Trials Daten haben
    validCount = sum(~isnan(M), 1);
    idx = validCount >= 2;
    
    tPlot = commonT(idx);
    mPlot = meanCurve(idx);
    sPlot = stdCurve(idx);
    
    % Std-Band (schattiert)
    fill([tPlot, fliplr(tPlot)], [mPlot+sPlot, fliplr(mPlot-sPlot)], ...
        posColors(i,:), 'FaceAlpha', 0.2, 'EdgeColor', 'none');
    % Mittelwertkurve
    plot(tPlot, mPlot, 'Color', posColors(i,:), 'LineWidth', 2);
    
    yline(0, 'k:');
    xline(0, 'k:');
    title(sprintf('%s (n=%d)', positions{i}, length(trials)));
    xlabel('Zeit relativ zum Peak (s)');
    ylabel('Beschleunigung (m/s^2)');
    grid on;
end
sgtitle('Mittlere Bremskurve ± Std pro Koerperposition');
theme('light');


%% =========================================================================
% FUNKTION: BREMSPHASE AUTOMATISCH ERKENNEN
% =========================================================================
function [res, t_win, mag_win] = analyzeBraking(filePath, fs, g, tailCutSec, thresholdRatio)
    
    % 1. Daten laden
    data = readtable(filePath, "VariableNamingRule", "preserve");
    ax = toNumeric(data(:,2));
    ay = toNumeric(data(:,3));
    az = toNumeric(data(:,4));
    n = height(data);
    t = (0:n-1)' / fs;
    
    % NaN-Zeilen entfernen (z.B. Parse-Fehler, leere Zellen)
    validRows = ~isnan(ax) & ~isnan(ay) & ~isnan(az);
    ax = ax(validRows);
    ay = ay(validRows);
    az = az(validRows);
    t  = t(validRows);
    n  = length(ax);
    
    % Sicherheitscheck: genug gültige Daten vorhanden?
    if n < 10
        warning('%s: Keine gültigen numerischen Daten gefunden (Spalten pruefen!). Ueberspringe.', filePath);
        res.t_start = NaN; res.t_end = NaN; res.duration = NaN;
        res.max_decel = NaN; res.mean_decel = NaN;
        res = struct2table(res);
        t_win = []; mag_win = [];
        return;
    end
    
    % 2. Vektorbetrag (Gravitation grob abgezogen)
    mag = sqrt(ax.^2 + ay.^2 + az.^2) - g;
    
    % 3. Glätten (Rauschen entfernen)
    [b, a] = butter(4, 20/(fs/2), 'low');
    mag_f = filtfilt(b, a, mag);
    
    % 4. ENDE ABSCHNEIDEN (Handy-Abschalt-Peak ignorieren!)
    cutIdx = min(n, max(1, n - round(tailCutSec * fs)));
    mag_valid = mag_f(1:cutIdx);
    t_valid = t(1:cutIdx);
    
    % 5. Echten Bremspeak finden (stärkste negative Beschleunigung)
    [peakVal, peakIdx] = min(mag_valid);
    
    % 6. Bremsphase = Bereich um Peak, wo Signal < Schwellwert
    threshold = thresholdRatio * peakVal;  % z.B. 20% des Peaks
    
    startIdx = peakIdx;
    while startIdx > 1 && mag_valid(startIdx) < threshold
        startIdx = startIdx - 1;
    end
    
    endIdx = peakIdx;
    while endIdx < length(mag_valid) && mag_valid(endIdx) < threshold
        endIdx = endIdx + 1;
    end
    
    % 7. Ergebnisse (Kennwerte)
    res.t_start    = t_valid(startIdx);
    res.t_end      = t_valid(endIdx);
    res.duration   = t_valid(endIdx) - t_valid(startIdx);
    res.max_decel  = abs(peakVal);
    res.mean_decel = abs(mean(mag_valid(startIdx:endIdx)));
    res = struct2table(res);
    
    % 8. Zeitreihe für Line-Plot (relativ zum Peak ausgerichtet, etwas Rand drumherum)
    padSamples = round(0.1 * fs);  % 0.1s Rand vor/nach der Bremsphase mitnehmen
    plotStart = max(1, startIdx - padSamples);
    plotEnd   = min(length(mag_valid), endIdx + padSamples);
    
    t_win   = t_valid(plotStart:plotEnd) - t_valid(peakIdx);  % t=0 ist der Peak
    mag_win = mag_valid(plotStart:plotEnd);
end


%% =========================================================================
% HILFSFUNKTION: SPALTE ROBUST IN NUMERISCHEN VEKTOR UMWANDELN
% =========================================================================
function v = toNumeric(col)
    v = table2array(col);
    if iscell(v) || isstring(v)
        % Falls als Text gelesen (z.B. Dezimal-Komma statt Punkt)
        v = str2double(strrep(string(v), ',', '.'));
    end
    v = double(v);
end