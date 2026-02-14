module.exports = {
  apps: [
    {
      name: "flask",
      script: "app.py",
      interpreter: "python",   // pastikan python ada di PATH
      env: {
        PYTHONUNBUFFERED: "1"  // biar log langsung muncul
      }
    },
    {
      name: "bridge",
      script: "bridge.js",
      interpreter: "node",
      env: {
        PYTHON_URL: "http://127.0.0.1:5000" // contoh environment variable
      }
    }
  ]
}