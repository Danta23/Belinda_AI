module.exports = {
  apps: [
    {
      name: "flask",
      script: "app.py",
      interpreter: "python",
      env: {
        PYTHONUNBUFFERED: "1"
      },
      autorestart: true,        // otomatis restart kalau crash
      restart_delay: 5000,      // tunggu 5 detik sebelum restart
      max_restarts: 10          // batasi maksimal restart berturut-turut
    },
    {
      name: "bridge",
      script: "bridge.js",
      interpreter: "node",
      env: {
        PYTHON_URL: "http://127.0.0.1:8000"
      },
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10
    }
  ]
}