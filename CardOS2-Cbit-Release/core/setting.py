# cos/setting.py

class Settings:
    def __init__(self, path="settings.cfg"):
        self.path = path
        self.data = {}

    # =========================
    # LOAD
    # =========================
    def load(self):
        self.data = {}
        try:
            with open(self.path, "r") as f:
                for line in f:
                    line = line.strip()
                    # skip empty lines & comments
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = self._parse(value.strip())
                        self.data[key] = value
        except OSError:
            print("ERROR: settings file not found")

    # =========================
    # PARSE VALUE
    # =========================
    def _parse(self, value):
        # Handle lists (comma-separated)
        if "," in value:
            return [self._parse_single(v.strip()) for v in value.split(",")]
        else:
            return self._parse_single(value)

    def _parse_single(self, value):
        v = value.lower()
        # Boolean
        if v == "true":
            return True
        if v == "false":
            return False
        # Integer
        try:
            return int(value)
        except:
            pass
        # Float
        try:
            return float(value)
        except:
            pass
        # String fallback
        return value

    # =========================
    # GET VALUE
    # =========================
    def get(self, key, default=None):
        return self.data.get(key, default)

    # =========================
    # SET VALUE
    # =========================
    def set(self, key, value):
        self.data[key] = value

    # =========================
    # SAVE TO FILE
    # =========================
    def save(self):
        try:
            with open(self.path, "w") as f:
                for key in sorted(self.data.keys()):
                    val = self.data[key]
                    if isinstance(val, list):
                        val = ",".join(str(v) for v in val)
                    f.write(f"{key}={val}\n")
        except OSError:
            print("ERROR: failed to save settings")

    # =========================
    # GET SECTION
    # =========================
    def get_section(self, prefix):
        result = {}
        prefix = prefix + "."
        for key, value in self.data.items():
            if key.startswith(prefix):
                sub_key = key[len(prefix):]
                result[sub_key] = value
        return result

    # =========================
    # HAS KEY
    # =========================
    def has(self, key):
        return key in self.data

    # =========================
    # REMOVE KEY
    # =========================
    def remove(self, key):
        if key in self.data:
            del self.data[key]

    # =========================
    # DEBUG PRINT
    # =========================
    def print_all(self):
        for key in sorted(self.data.keys()):
            print(f"{key} = {self.data[key]}")