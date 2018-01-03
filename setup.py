import os
import subprocess
import Savoir
import linecache
import json

# Check if directory structure and files are correct
print("Checking required files...")
if not os.path.isdir("multichain"):
	print("Multichain directory does not exist! Make sure you have Multichain downloaded.")
elif not (os.path.exists(os.path.join("multichain", "src", "multichain-cli")) and os.path.exists(os.path.join("multichain", "src", "multichaind")) and os.path.exists(os.path.join("multichain", "src", "multichain-util"))):
	print("Multichain files are incomplete! Make sure your version has been correctly compiled.")
else:
	print("File check complete!")
		
chainname = input("Enter a name for the new gradebook:\n")

# Set path for chains
path = os.path.join(os.getcwd(), "chains")
if not os.path.exists(path):
	os.makedirs(path)

# Call Multichain executables to create chain with given name
subprocess.call([os.path.join("multichain", "src", "multichain-util"), "create", chainname, "-datadir=" + path])
subprocess.call([os.path.join("multichain", "src", "multichaind"), chainname, "-daemon", "-datadir=" + path])

# Set relevant credentials from chain configuration file
rpcuserline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 1)
rpcuser = rpcuserline.strip().split("=")[1]
print(rpcuser)
rpcpasswdline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 2)
rpcpasswd = rpcpasswdline.strip().split("=")[1]
print(rpcpasswd)
rpchost = "localhost"

# Issue API command to check RPC port
output = bytes.decode(subprocess.check_output([os.path.join("multichain", "src", "multichain-cli"),  "-datadir=" + path, chainname, "getblockchainparams"]))
rpcport = str(json.loads(output).get("default-rpc-port"))

# Set up API for making calls
api = Savoir.Savoir(rpcuser, rpcpasswd, rpchost, rpcport, chainname)

# Save API parameters in file for access later
saveFile = open(os.path.join(path, chainname, "apiparams"), "w")
saveFile.write(rpcuser + "\n" + rpcpasswd + "\n" + rpchost + "\n" + rpcport + "\n" + chainname)

# Set up blockchain structure
api.create("stream", "pubKeys", True)
api.create("stream", "items", True)
api.create("stream", "access", True)
api.create("stream", "courses", True)
api.create("stream", "blacklist", True)
api.subscribe("pubKeys")
api.subscribe("items")
api.subscribe("access")
api.subscribe("courses")
api.subscribe("blacklist")
print(api.liststreams())