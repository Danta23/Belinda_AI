module.exports = {
  apps: [
    {
      name: "flask",
      script: "app.py",
      interpreter: "python"
    },
    {
      name: "bridge",
      script: "bridge.js",
      interpreter: "node"
    }
  ]
}