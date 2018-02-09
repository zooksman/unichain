import subprocess

subprocess.call(["easy_install",  "Savoir"])
subprocess.call(["pip3", "install", "cryptography"])
subprocess.call(["easy_install", "jinja2"])
subprocess.call(["pip3", "install", "git+https://github.com/webpy/webpy#egg=web.py"])
