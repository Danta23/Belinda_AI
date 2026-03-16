
import os
import json
from dotenv import load_dotenv, set_key

class SettingsManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.env_path = os.path.join(root_dir, ".env")
        self.defaults = {
            "GROQ_API_KEY": "",
            "FLASK_PORT": "8000",
            "AI_NAME": "Belinda AI",
            "AI_PERSONALITY": "Intelligent assistant",
            "AI_MAX_TOKENS": "1024",
            "APP_THEME": "dark",
            "APP_LANGUAGE": "English",
            "APP_FONT_SIZE": "14",
            "APP_FONT_FAMILY": "Segoe UI",
            "APP_TITLE_SIZE": "24",
            "EXECUTION_MODE": "local"
        }
        
        if not os.path.exists(self.env_path):
            # Ensure the directory exists first
            os.makedirs(self.root_dir, exist_ok=True)
            
            template = os.path.join(root_dir, ".env.example")
            if os.path.exists(template):
                with open(template, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                with open(self.env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                try:
                    with open(self.env_path, 'w', encoding='utf-8') as f:
                        content = "\n".join([f"{k}={v}" for k, v in self.defaults.items()])
                        f.write(content)
                except: pass
        
        load_dotenv(self.env_path)

    def get(self, key, default=None):
        if default is None:
            default = self.defaults.get(key, "")
        value = os.getenv(key)
        if value is None:
            return default
        return value

    def set(self, key, value):
        set_key(self.env_path, key, str(value))
        os.environ[key] = str(value)

    def get_all(self):
        settings = {}
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        try:
                            k, v = line.split('=', 1)
                            settings[k.strip()] = v.strip()
                        except: pass
        return settings
