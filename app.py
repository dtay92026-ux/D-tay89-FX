from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DtayFxEngine | Trading Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #f3f4f6; }
        .glass-card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-emerald { box-shadow: 0 0 25px rgba(16, 185, 129, 0.2); }
        .glow-blue { box-shadow: 0 0 25px rgba(59, 130, 246, 0.2); }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <!-- Navbar -->
    <header class="glass-card border-b border-gray-800 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <div class="w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>
            <h1 class="text-xl font-bold tracking-wider text-white">DTAY<span class="text-emerald-400">FX</span> ENGINE</h1>
        </div>
        <div class="flex items-center space-x-4">
            <span class="text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">Telegram Active</span>
            <span class="text-xs text-gray-400 font-mono">MT5: Ready</span>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <!-- Control Panel Banner -->
        <div class="glass-card rounded-2xl p-6 glow-blue flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-white">Automated Trading Control Panel</h2>
                <p class="text-sm text-gray-400 mt-1">Real-time monitoring for XAUUSD & Telegram notification dispatchers.</p>
            </div>
            <div class="flex gap-3">
                <button onclick="triggerBotAction('start')" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition shadow-lg shadow-emerald-900/40 cursor-pointer">Start Engine</button>
                <button onclick="triggerBotAction('stop')" class="px-5 py-2.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-semibold text-sm transition cursor-pointer">Stop Engine</button>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="glass-card rounded-2xl p-5 border-l-4 border-emerald-500">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Asset / Symbol</p>
                <p class="text-2xl font-bold text-white mt-2 font-mono">XAUUSD</p>
                <p class="text-xs text-emerald-400 mt-1">M15 Timeframe</p>
            </div>
            <div class="glass-card rounded-2xl p-5 border-l-4 border-blue-500">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Lot Size</p>
                <p class="text-2xl font-bold text-white mt-2 font-mono">0.01</p>
                <p class="text-xs text-blue-400 mt-1">Risk Managed</p>
            </div>
            <div class="glass-card rounded-2xl p-5 border-l-4 border-purple-500">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Strategy</p>
                <p class="text-xl font-bold text-white mt-2 font-mono">EMA 9/21</p>
                <p class="text-xs text-purple-400 mt-1">Crossover Filter</p>
            </div>
            <div class="glass-card rounded-2xl p-5 border-l-4 border-amber-500">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Telegram Status</p>
                <p class="text-xl font-bold text-white mt-2 font-mono">Connected</p>
                <p class="text-xs text-amber-400 mt-1">Instant Alerts ON</p>
            </div>
        </div>

        <!-- Live Terminal Log -->
        <div class="glass-card rounded-2xl p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-white">Live Execution Logs</h3>
                <span class="text-xs text-gray-400 font-mono" id="status-badge">Status: Idle</span>
            </div>
            <div class="bg-gray-950 rounded-xl p-4 font-mono text-xs text-emerald-400 h-64 overflow-y-auto border border-gray-800" id="log-box">
                [System] DtayFxEngine web interface loaded.<br>
                [System] Ready to dispatch MT5 logs and Telegram events.
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="text-center py-6 text-xs text-gray-500 border-t border-gray-900">
        DtayFxEngine &bull; Powered by MetaTrader 5 & Telegram Bot API
    </footer>

    <script>
        function triggerBotAction(action) {
            const logBox = document.getElementById('log-box');
            const timeStr = new Date().toLocaleTimeString();
            if(action === 'start') {
                logBox.innerHTML += `<br>[${timeStr}] 🚀 Engine started manually from Web UI.`;
                document.getElementById('status-badge').innerText = "Status: Running";
            } else {
                logBox.innerHTML += `<br>[${timeStr}] 🛑 Engine stopped manually from Web UI.`;
                document.getElementById('status-badge').innerText = "Status: Stopped";
            }
            logBox.scrollTop = logBox.scrollHeight;
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/status")
def status():
  return jsonify({"status": "running", "symbol": "XAUUSD", "telegram": "active"})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
