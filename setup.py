import os
import sys
import subprocess
import Savoir
import linecache
import json
import time

# Check if directory structure and files are correct
print("Checking required files...")
if not os.path.isdir("multichain"):
	print("Multichain directory does not exist! Make sure you have Multichain downloaded.")
elif not (os.path.exists(os.path.join("multichain", "multichain-cli.exe")) and os.path.exists(os.path.join("multichain", "multichaind.exe")) and os.path.exists(os.path.join("multichain", "multichain-util.exe"))):
	print("Multichain files are incomplete! Make sure your version has been correctly compiled.")
else:
	print("File check complete!")
		
# Set path for chains
path = os.path.join(os.getcwd(), "chains")
if not os.path.exists(path):
	os.makedirs(path)
exit = True

# Initialize process variable
process = None

# Start menu and continue until the exit option is selected
while exit:

	# Print menu options
	option = input("\n--Unichain alpha 1--\nPlease select an option by entering a number below:\n1. Create new gradebook\n2. Reconnect to existing gradebook\n3. Connect to existing gradebook for the first time\n4. Grant student access\n5. Grant teacher access\n6. Exit\n")
	
	# Option 1: Create new gradebook
	if option == "1" or option == "1.":
		
		chainname = input("Enter a name for the new gradebook:\n")

		# Call Multichain executables to create chain with given name
		subprocess.call([os.path.join("multichain", "multichain-util.exe"), "create", chainname, "-datadir=" + path], stdout=subprocess.DEVNULL)
		process = subprocess.Popen([os.path.join("multichain", "multichaind.exe"), chainname, "-datadir=" + path], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		
		# Process each line of node output
		for line in iter(process.stdout.readline, b''):
			#sys.stdout.write(line.decode(sys.stdout.encoding))
			
			# If the string "multichaind" is present in node output, indicating that the IP address and port immediately follow
			if "multichaind" in line.decode(sys.stdout.encoding):
			
				# Split IP address and port from chain name and print result
				print("Gradebook created! When others connect for the first time, tell them to use this IP address and port: " + line.decode(sys.stdout.encoding).split(" ")[line.decode(sys.stdout.encoding).split(" ").index("multichaind") + 1].split("@")[1])
			
			# If the string "started" is present in node output, indicating that the node successfully started
			if "started" in line.decode(sys.stdout.encoding):
				break
			
			# Loop until one of those two words is found in node output
			else:
				pass
			
		# Wait a few seconds to allow node to start
		time.sleep(5)
		
		# Set relevant credentials from chain configuration file
		rpcuserline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 1)
		rpcuser = rpcuserline.strip().split("=")[1]
		rpcpasswdline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 2)
		rpcpasswd = rpcpasswdline.strip().split("=")[1]
		rpchost = "localhost"
				
		# Issue API command to check RPC port
		output = bytes.decode(subprocess.check_output([os.path.join("multichain", "multichain-cli.exe"),  "-datadir=" + path, chainname, "getblockchainparams"]))
		rpcport = str(json.loads(output).get("default-rpc-port"))

		# Set up API for making calls
		api = Savoir.Savoir(rpcuser, rpcpasswd, rpchost, rpcport, chainname)

		# Save API parameters in file for access later
		saveFile = open(os.path.join(path, chainname, "apiparams"), "w")
		saveFile.write(rpcuser + "\n" + rpcpasswd + "\n" + rpchost + "\n" + rpcport + "\n" + chainname)
		saveFile.close()
		
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
		
		print("Now grant access to others or choose option 2 to get started!\n")
	
	# Option 2: Reconnect to existing gradebook	
	elif option == "2" or option == "2.":
	
		# Start Multichain node for given chain name
		chainname = input("Enter the name of the gradebook you're trying to connect to.\n")
		process = subprocess.Popen([os.path.join("multichain", "multichaind.exe"), chainname, "-datadir=" + path])
		time.sleep(10)
		
		# Start web interface
		subprocess.call(["python",  os.path.join(os.getcwd(), "webui.py")])
	
	# Option 3: Connect to existing gradebook for the first time			
	elif option == "3" or option == "3.": 
	
		# Ask for chain name and IP address of seed node
		chainname = input("Enter the name of the gradebook you're trying to connect to.\n")
		ipport = input("Enter the IP address and port of the gradebook assigned at creation. Example: 127.0.0.1:5766\n")
		connected = False
		
		# Run Multichain node in background and record output
		process = subprocess.Popen([os.path.join("multichain", "multichaind.exe"), chainname + "@" + ipport, "-datadir=" + path], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		
		# Process each line of node output
		for line in iter(process.stdout.readline, b''):
				#sys.stdout.write(line.decode(sys.stdout.encoding))
				
				# If the string "error:" is present in any line of the node output
				if "Error:" in line.decode(sys.stdout.encoding):
					print("An error occurred. Ensure that the IP address, port, and gradebook name are correct, and try again.")
					break
					
				# If the string "grant" is present in any line of the node output, indicating a lack of permissions
				elif "grant" in line.decode(sys.stdout.encoding):
				
					# Print the assigned address to give to the chain owner for granting access
					print("You currently do not have permission to access this gradebook.\nPlease ask the owner to run this program and grant access to the following address:\n" + line.decode(sys.stdout.encoding).split(" ")[line.decode(sys.stdout.encoding).split(" ").index("grant") + 1])
					break
					
				# If the string "started" is present in any line of the node output, indicating the node was successfully started
				elif "started" in line.decode(sys.stdout.encoding):
					print("Connected!")
					connected = True
					break
					
				# Loop until one of those three words is found in program output
				else:
					pass
		
		# Wait a few seconds to allow node to start
		time.sleep(5)
		
		# If node was successfully started
		if connected == True:
		
			# Set relevant credentials from chain configuration file
			rpcuserline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 1)
			rpcuser = rpcuserline.strip().split("=")[1]
			rpcpasswdline = linecache.getline(os.path.join(path, chainname, "multichain.conf"), 2)
			rpcpasswd = rpcpasswdline.strip().split("=")[1]
			rpchost = "localhost"
			
			# Issue API command to check RPC port
			output = bytes.decode(subprocess.check_output([os.path.join("multichain", "multichain-cli.exe"),  "-datadir=" + path, chainname, "getblockchainparams"]))
			rpcport = str(json.loads(output).get("default-rpc-port"))

			# Set up API for making calls
			api = Savoir.Savoir(rpcuser, rpcpasswd, rpchost, rpcport, chainname)

			# Save API parameters in file for access later
			saveFile = open(os.path.join(path, chainname, "apiparams"), "w")
			saveFile.write(rpcuser + "\n" + rpcpasswd + "\n" + rpchost + "\n" + rpcport + "\n" + chainname)
			saveFile.close()

			# Start web interface
			subprocess.call(["python",  os.path.join(os.getcwd(), "webui.py")])
			

	# Option 4: Grant student access			
	elif option == "4" or option == "4.":
	
		# Ask for name of student and address given to them after an attempted connection
		chainname = input("Please enter the name of the gradebook.\n")
		address = input("Please enter the address of the student you are granting access.\n")
		
		# Attempt to grant address student permissions, but catch an error
		try:
			
			# Call Multichain process to grant the address access
			subprocess.check_output([os.path.join("multichain", "multichain-cli.exe"), chainname, "-datadir=" + path, "grant", address, "connect,send,receive"])
			print("Access successfully granted!")
			print("Now tell the user who tried to connect to do so again, since now they have permissions!")
			
		# Catch a possible error (usually incorrect address or not being the gradebook owner)
		except subprocess.CalledProcessError as e:
							
			print("That address is likely incorrect. Try entering it again.")
	
	# Option 5: Grant teacher access		
	elif option == "5" or option == "5.":
	
		# Ask for name of teacher and address given to them after an attempted connection
		chainname = input("Please enter the name of the gradebook.\n")
		address = input("Please enter the address of the teacher you are granting access.\n")
		
		# Attempt to grant address teacher permissions, but catch an error
		try:
		
			# Call Multichain process to grant the address access
			subprocess.check_output([os.path.join("multichain", "multichain-cli.exe"), chainname, "-datadir=" + path, "grant", address, "connect,send,receive,issue"])
			print("Access successfully granted!")
			print("Now tell the user who tried to connect to do so again, since now they have permissions!")
			
		# Catch a possible error (usually incorrect address or not being the gradebook owner)
		except subprocess.CalledProcessError as e:
		
			print("That address is likely incorrect. Try entering it again.")
			
	# Option 6: Exit
	elif option == "6" or option == "6.":
		
		# Set exit flag so while loop ends
		exit = False
		
		# If there is a running Multichain node, kill it before exiting
		if process != None:
			process.kill()
