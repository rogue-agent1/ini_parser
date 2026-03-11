#!/usr/bin/env python3
"""INI file parser and writer — without configparser.

Supports sections, key=value, comments (#;), multiline values,
interpolation (%(key)s), and preserves order.

Usage:
    python ini_parser.py config.ini
    python ini_parser.py --test
"""

import re
import sys


class IniFile:
    """INI file parser/writer."""

    def __init__(self):
        self.sections = {}  # name -> OrderedDict-like dict
        self._order = []    # section order

    def parse(self, text: str) -> 'IniFile':
        current = "__default__"
        self.sections[current] = {}
        self._order.append(current)
        multiline_key = None
        
        for line in text.splitlines():
            stripped = line.strip()
            
            # Empty or comment
            if not stripped or stripped[0] in '#;':
                multiline_key = None
                continue

            # Section header
            m = re.match(r'^\[([^\]]+)\]', stripped)
            if m:
                current = m.group(1).strip()
                if current not in self.sections:
                    self.sections[current] = {}
                    self._order.append(current)
                multiline_key = None
                continue

            # Multiline continuation (starts with whitespace)
            if multiline_key and line[0] in ' \t':
                self.sections[current][multiline_key] += '\n' + stripped
                continue

            # Key = value
            m = re.match(r'^([^=:]+)[=:](.*)$', stripped)
            if m:
                key = m.group(1).strip()
                value = m.group(2).strip()
                self.sections[current][key] = value
                multiline_key = key
            else:
                multiline_key = None

        return self

    def get(self, section: str, key: str, fallback=None, interpolate=True) -> str:
        """Get value with optional interpolation."""
        if section not in self.sections:
            return fallback
        value = self.sections[section].get(key, fallback)
        if value is None or not interpolate:
            return value
        # Interpolate %(key)s references
        def replacer(m):
            ref_key = m.group(1)
            return self.sections[section].get(ref_key, m.group(0))
        return re.sub(r'%\((\w+)\)s', replacer, str(value))

    def set(self, section: str, key: str, value: str):
        if section not in self.sections:
            self.sections[section] = {}
            self._order.append(section)
        self.sections[section][key] = value

    def remove(self, section: str, key: str = None) -> bool:
        if section not in self.sections:
            return False
        if key is None:
            del self.sections[section]
            self._order.remove(section)
        elif key in self.sections[section]:
            del self.sections[section][key]
        else:
            return False
        return True

    def to_string(self) -> str:
        lines = []
        for section in self._order:
            if section == "__default__" and not self.sections.get(section):
                continue
            if section != "__default__":
                lines.append(f"[{section}]")
            for key, value in self.sections.get(section, {}).items():
                if '\n' in value:
                    first, *rest = value.split('\n')
                    lines.append(f"{key} = {first}")
                    for r in rest:
                        lines.append(f"    {r}")
                else:
                    lines.append(f"{key} = {value}")
            lines.append("")
        return '\n'.join(lines)

    def section_names(self) -> list:
        return [s for s in self._order if s != "__default__"]

    def items(self, section: str) -> list:
        return list(self.sections.get(section, {}).items())


def test():
    print("=== INI Parser Tests ===\n")

    ini_text = """
# Database configuration
[database]
host = localhost
port = 5432
name = mydb
connection = %(host)s:%(port)s/%(name)s

[server]
host = 0.0.0.0
port = 8080
debug = true

; Logging
[logging]
level = INFO
format = %(asctime)s - %(message)s
"""

    ini = IniFile().parse(ini_text)

    # Sections
    assert ini.section_names() == ["database", "server", "logging"]
    print(f"✓ Sections: {ini.section_names()}")

    # Basic get
    assert ini.get("database", "host") == "localhost"
    assert ini.get("server", "port") == "8080"
    print("✓ Basic get")

    # Interpolation
    conn = ini.get("database", "connection")
    assert conn == "localhost:5432/mydb", f"Got: {conn}"
    print(f"✓ Interpolation: connection = {conn}")

    # Non-interpolated
    raw = ini.get("logging", "format", interpolate=False)
    assert "%(asctime)s" in raw
    print("✓ Raw (no interpolation)")

    # Fallback
    assert ini.get("database", "missing", fallback="default") == "default"
    print("✓ Fallback")

    # Set
    ini.set("database", "pool_size", "10")
    assert ini.get("database", "pool_size") == "10"
    print("✓ Set")

    # New section
    ini.set("cache", "ttl", "300")
    assert "cache" in ini.section_names()
    print("✓ New section via set")

    # Remove
    ini.remove("database", "pool_size")
    assert ini.get("database", "pool_size") is None
    print("✓ Remove key")

    # Roundtrip
    output = ini.to_string()
    ini2 = IniFile().parse(output)
    assert ini2.get("database", "host") == "localhost"
    assert ini2.get("server", "debug") == "true"
    print("✓ Roundtrip (write → parse)")

    # Colon separator
    colon_ini = IniFile().parse("[s]\nkey: value\n")
    assert colon_ini.get("s", "key") == "value"
    print("✓ Colon separator")

    print("\nAll tests passed! ✓")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--test":
        test()
    else:
        with open(args[0]) as f:
            ini = IniFile().parse(f.read())
        for section in ini.section_names():
            print(f"[{section}]")
            for k, v in ini.items(section):
                print(f"  {k} = {v}")
