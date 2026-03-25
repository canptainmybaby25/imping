package com.imping.qengine;

import android.os.Bundle;
import android.view.View;
import android.widget.*;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.os.Build;

import com.chaquo.python.android.AndroidPythonEnvironment;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {

    private TextView statusText, statsText, logText;
    private TableLayout procTable;
    private Button scanBtn, mimicBtn, monitorBtn;
    private ScrollView logScroll;
    private LinearLayout procContainer;

    private boolean monitoring = false;
    private Thread monitorThread = null;
    private PyObject pyClassifier = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Init Python
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        setContentView(R.layout.activity_main);

        initViews();
        initPythonEngine();
        updateStatus("⚛️ IMPGING Ready\n" + getSystemInfo());
        updateStats(0, 0, 0, 0, 1.0f);
        appendLog("IMPGING Q-Engine initialized");
    }

    private void initViews() {
        statusText  = findViewById(R.id.statusText);
        statsText   = findViewById(R.id.statsText);
        logText     = findViewById(R.id.logText);
        procTable   = findViewById(R.id.procTable);
        logScroll   = findViewById(R.id.logScroll);
        scanBtn     = findViewById(R.id.scanBtn);
        mimicBtn    = findViewById(R.id.mimicBtn);
        monitorBtn  = findViewById(R.id.monitorBtn);
        procContainer = findViewById(R.id.procContainer);

        scanBtn.setOnClickListener(v -> doScan());
        mimicBtn.setOnClickListener(v -> toggleMimic());
        monitorBtn.setOnClickListener(v -> toggleMonitor());

        // Load app icon
        try {
            ApplicationInfo ai = getPackageManager()
                .getApplicationInfo(getPackageName(), 0);
            setTitle("⚛️ IMPGING Q-Engine");
        } catch (PackageManager.NameNotFoundException e) {}
    }

    private void initPythonEngine() {
        try {
            Python py = Python.getInstance();
            PyObject sys = py.getModule("sys");
            sys.callAttr("path", "append", getFilesDir().getAbsolutePath() + "/python");

            // Load the Q-Engine bootstrap
            pyClassifier = py.getModule("qengine_bridge")
                .callAttr("get_classifier");
            appendLog("✅ Q-Engine loaded via Chaquopy");
        } catch (Exception e) {
            appendLog("⚠️  Q-Engine init: " + e.getMessage());
            // Fallback: load scripts directly
            try {
                pyClassifier = py.getModule("impging_standalone")
                    .callAttr("QClassifier");
                appendLog("✅ Standalone Q-Engine loaded");
            } catch (Exception e2) {
                appendLog("❌ Q-Engine unavailable: " + e2.getMessage());
            }
        }
    }

    private void doScan() {
        scanBtn.setEnabled(false);
        statusText.setText("🔍 Scanning...");
        appendLog("Scan started");

        new Thread(() -> {
            try {
                StringBuilder results = new StringBuilder();
                AndroidProcessScanner scanner = new AndroidProcessScanner(this);

                List<ProcessInfo> procs = scanner.scanProcesses();
                List<ScannedResult> classified = classifier.classifyAll(procs);

                int casino = 0, gaming = 0, malware = 0, suspicious = 0;

                runOnUiThread(() -> {
                    procContainer.removeAllViews();
                    for (ScannedResult r : classified) {
                        addProcessRow(r);
                        switch (r.category) {
                            case "CASINO": casino++; break;
                            case "GAMING": gaming++; break;
                            case "MALWARE": malware++; break;
                            case "SUSPICIOUS": suspicious++; break;
                        }
                    }
                    updateStats(casino, gaming, malware, suspicious, 1.0f);
                    statusText.setText("✅ Scan complete — " + procs.size() + " processes");
                    appendLog("Scan complete: " + procs.size() + " procs | 🃏" + casino + " 🎮" + gaming + " ⚠️" + (malware + suspicious));
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    statusText.setText("❌ Scan failed: " + e.getMessage());
                    appendLog("Scan error: " + e.getMessage());
                });
            } finally {
                runOnUiThread(() -> scanBtn.setEnabled(true));
            }
        }).start();
    }

    private void toggleMimic() {
        if (mimicBtn.getText().toString().contains("Start")) {
            mimicBtn.setText("⏹ Stop Mimic");
            appendLog("Mimic Engine: ACTIVE (stealth)");
            // Start as background service
            Intent svc = new Intent(this, IMPGINGService.class);
            svc.setAction("START_MIMIC");
            startService(svc);
        } else {
            mimicBtn.setText("👁️ Start Mimic");
            appendLog("Mimic Engine: STOPPED");
            Intent svc = new Intent(this, IMPGINGService.class);
            svc.setAction("STOP");
            startService(svc);
        }
    }

    private void toggleMonitor() {
        monitoring = !monitoring;
        if (monitoring) {
            monitorBtn.setText("⏹ Stop Monitor");
            appendLog("Monitor: STARTED (5s interval)");
            monitorThread = new Thread(() -> {
                while (monitoring) {
                    doScan();
                    try { Thread.sleep(5000); } catch (InterruptedException e) { break; }
                }
            });
            monitorThread.start();
        } else {
            monitorBtn.setText("📡 Start Monitor");
            appendLog("Monitor: STOPPED");
            if (monitorThread != null) monitorThread.interrupt();
        }
    }

    private void addProcessRow(ScannedResult r) {
        TableRow row = new TableRow(this);
        row.setPadding(4, 4, 4, 4);

        String flag = r.category.equals("CASINO") || r.category.equals("MALWARE") ? "🔴"
                    : r.category.equals("SUSPICIOUS") ? "🟡" : "🟢";

        String[] cols = {
            String.valueOf(r.pid),
            r.name.length() > 18 ? r.name.substring(0, 15) + "…" : r.name,
            flag + " " + r.category,
            String.format("%.3f", r.confidence),
            String.format("%.4f", r.entropy)
        };

        int[] colors = { Color.parseColor("#2a2a2a"), Color.parseColor("#1a1a1a") };
        int rowColor = colors[procContainer.getChildCount() % 2];

        for (String col : cols) {
            TextView tv = new TextView(this);
            tv.setText(col);
            tv.setTextColor(Color.WHITE);
            tv.setTextSize(11);
            tv.setPadding(8, 4, 8, 4);
            tv.setBackgroundColor(rowColor);
            row.addView(tv);
        }

        procContainer.addView(row);
    }

    private void updateStats(int casino, int gaming, int malware, int suspicious, float energy) {
        String s = "  🃏 CASINO: " + casino + "   🎮 GAMING: " + gaming
                  + "   ⚠️ ALERT: " + (malware + suspicious)
                  + "   ⚡ ENERGY: " + String.format("%.2f", energy);
        statsText.setText(s);
    }

    private void updateStatus(String msg) {
        statusText.setText(msg);
    }

    private void appendLog(String msg) {
        String ts = java.text.SimpleDateFormat("HH:mm:ss").format(new java.util.Date());
        String current = logText.getText().toString();
        String newEntry = "[" + ts + "] " + msg + "\n";
        logText.setText(newEntry + current);
        logScroll.post(() -> logScroll.fullScroll(View.FOCUS_UP));
    }

    private String getSystemInfo() {
        int cores = Runtime.getRuntime().availableProcessors();
        long memTotal = Runtime.getRuntime().totalMemory() / 1024 / 1024;
        return "CPU: " + cores + " cores | RAM: " + memTotal + "MB | API " + Build.VERSION.SDK_INT;
    }

    // ── Process Info inner class ──────────────────────────────
    static class ProcessInfo {
        int pid;
        String name;
        String packageName;
        String sourceDir;
        boolean isSystem;

        ProcessInfo(int pid, String name, String pkg, String dir, boolean sys) {
            this.pid = pid; this.name = name; this.packageName = pkg;
            this.sourceDir = dir; this.isSystem = sys;
        }
    }

    static class ScannedResult {
        int pid;
        String name;
        String category;
        float confidence;
        float entropy;

        ScannedResult(int pid, String name, String cat, float conf, float ent) {
            this.pid = pid; this.name = name; this.category = cat;
            this.confidence = conf; this.entropy = ent;
        }
    }

    // ── Process Scanner ──────────────────────────────────────
    private class AndroidProcessScanner {
        private final Activity ctx;
        private final List<String> CASINO_KW = java.util.Arrays.asList(
            "1xbet","22bet","7bit","andarbahar","baccarat","bet365","betfair",
            "betway","betwinner","bk8","blackjack","bovada","casino","championsbet",
            "cricbet","dream11","draftkings","dafabet","exchange","fanduel",
            "fc25","fifa","football","foxbet","galsports","ganar","guts","jackpot",
            "ladbrokes","leo","leovegas","liga","live casino","lottery","luckia",
            "marathonbet","megapari","melbet","mgm","michigancasino","milan","mobilecasino",
            "mrbet","netbet","nfl","odds","onlinebet","palms","parlay","partypoker",
            "poker","pokerstars","polynomial","power","premierbet","props","ps3838",
            "racebook","rar","realbet","rivalry","rolletto","rouletteroom","royal",
            "sbotop","scratch","septulah","sexys","sidney","slot","snake","soccer",
            "sportbet","sportsbet","sportsbook","stanleybet","stake","stake","sbotop",
            "suntos","superbet","supersports","tennisi","tennis","texas","tipsport",
            "tomhorsey","tonybet","topbet","unibet","vegas","victory","vikings","win",
            "winmasters","winpot","winspeeder","witkey","worldbet","youwin","zodiac"
        );
        private final List<String> MALWARE_KW = java.util.Arrays.asList(
            "betblock","betfilter","bet ограничитель","casinoactivator",
            "casinoblocker","casinoclose","coldturkey","gamban","gamblock",
            "gamebreaker","gamestopper","netnanny","selfexclude","spam","stealer",
            "keylog","rat ","trojan","virustotal","yara","remnux","fiddler","mitmproxy",
            "frida","xposed","substrate","hook","injector","cheat","crack","keygen",
            "rootkit","backdoor","keylogger","siphon","freevpn","hideit","cloack"
        );

        AndroidProcessScanner(Activity c) { this.ctx = c; }

        List<ProcessInfo> scanProcesses() {
            List<ProcessInfo> results = new ArrayList<>();
            try {
                PackageManager pm = ctx.getPackageManager();
                List<ApplicationInfo> apps = pm.getInstalledApplications(
                    PackageManager.GET_META_DATA);
                android.app.ActivityManager am = (android.app.ActivityManager)
                    ctx.getSystemService(ACTIVITY_SERVICE);
                android.app.ActivityManager.MemoryInfo memInfo =
                    new android.app.ActivityManager.MemoryInfo();
                am.getMemoryInfo(memInfo);

                for (ApplicationInfo app : apps) {
                    String name = app.loadLabel(pm).toString();
                    if (name == null || name.isEmpty()) name = app.packageName;
                    boolean isSystem = (app.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                    results.add(new ProcessInfo(
                        app.uid, name, app.packageName, app.sourceDir, isSystem));
                }
            } catch (Exception e) {
                appendLog("Scanner error: " + e.getMessage());
            }
            return results;
        }

        ScannedResult classify(ProcessInfo p) {
            String lname = p.name.toLowerCase();
            String lpkg  = p.packageName.toLowerCase();
            String full  = lname + " " + lpkg;

            float casinoConf = 0f, gamingConf = 0f, malwareConf = 0f;

            for (String kw : CASINO_KW) {
                if (full.contains(kw)) { casinoConf += 0.4f; break; }
            }
            for (String kw : MALWARE_KW) {
                if (full.contains(kw)) { malwareConf += 0.5f; break; }
            }
            if (p.name.contains("Game") || p.name.contains("Play") ||
                p.sourceDir.contains("game") || p.sourceDir.contains("casino")) {
                gamingConf += 0.3f;
            }

            float entropy = shannonEntropy(p.name);
            if (entropy > 3.5) { malwareConf += 0.2f; }
            if (p.isSystem) { malwareConf *= 0.5f; }

            casinoConf = Math.min(casinoConf, 1.0f);
            gamingConf = Math.min(gamingConf, 1.0f);
            malwareConf = Math.min(malwareConf, 1.0f);

            String cat;
            float conf;
            if (casinoConf >= 0.4f) { cat = "CASINO"; conf = casinoConf; }
            else if (malwareConf >= 0.4f) { cat = "MALWARE"; conf = malwareConf; }
            else if (gamingConf >= 0.3f) { cat = "GAMING"; conf = gamingConf; }
            else { cat = "UNKNOWN"; conf = 0.0f; }

            return new ScannedResult(p.pid, p.name, cat, conf, entropy);
        }

        List<ScannedResult> classifyAll(List<ProcessInfo> procs) {
            List<ScannedResult> results = new ArrayList<>();
            for (ProcessInfo p : procs) {
                results.add(classify(p));
            }
            java.util.Collections.sort(results,
                (a, b) -> Float.compare(b.confidence, a.confidence));
            return results;
        }

        private float shannonEntropy(String s) {
            if (s == null || s.isEmpty()) return 0f;
            int[] freq = new int[256];
            for (char c : s.toCharArray()) freq[(int)c]++;
            float ent = 0f;
            for (int f : freq) {
                if (f == 0) continue;
                float p = (float) f / s.length();
                ent -= p * (Math.log(p) / Math.log(2));
            }
            return ent;
        }
    }
}
