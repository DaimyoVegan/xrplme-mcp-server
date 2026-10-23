#!/usr/bin/env python3
"""Deploy status page + schema + storefront + restart services."""
import subprocess, sys, os

# Run status generator
r1 = subprocess.run([sys.executable, "/home/xrpladmin/update_status_page.py"],
    capture_output=True, text=True, cwd="/home/xrpladmin")
print("Status gen:", r1.stdout.strip())

# Run storefront generator
r2 = subprocess.run([sys.executable, "/home/xrpladmin/gen_storefront.py"],
    capture_output=True, text=True, cwd="/home/xrpladmin")
print("Storefront gen:", r2.stdout.strip())

# Deploy schema
os.makedirs("/var/www/xrplme.online/schema/v1", exist_ok=True)
subprocess.run(["cp", "-f", "/tmp/response-schema.json", "/var/www/xrplme.online/schema/v1/response-schema.json"], capture_output=True)

# Copy all generated files to web root
subprocess.run(["cp", "-f", "/tmp/storefront.html", "/var/www/xrplme.online/storefront.html"], capture_output=True)
subprocess.run(["cp", "-f", "/home/xrpladmin/public_html/status.html", "/var/www/xrplme.online/status.html"], capture_output=True)
subprocess.run(["cp", "-f", "/home/xrpladmin/public_html/status-data.json", "/var/www/xrplme.online/status-data.json"], capture_output=True)

# Copy fixed blog index and developers page
if os.path.exists("/tmp/blog_index_fixed.html"):
    subprocess.run(["cp", "-f", "/tmp/blog_index_fixed.html", "/var/www/xrplme.online/blog/index.html"], capture_output=True)
if os.path.exists("/tmp/developers_fixed.html"):
    subprocess.run(["cp", "-f", "/tmp/developers_fixed.html", "/var/www/xrplme.online/developers.html"], capture_output=True)

# Update blog front page
r3 = subprocess.run([sys.executable, "/home/xrpladmin/update_blog_frontpage.py"],
    capture_output=True, text=True, cwd="/home/xrpladmin")
print("Blog update:", r3.stdout.strip())

# Fix permissions
subprocess.run(["chmod", "644",
    "/var/www/xrplme.online/storefront.html",
    "/var/www/xrplme.online/status.html",
    "/var/www/xrplme.online/status-data.json",
    "/var/www/xrplme.online/blog/index.html",
    "/var/www/xrplme.online/developers.html",
    "/var/www/xrplme.online/schema/v1/response-schema.json"], capture_output=True)
if r3.stdout:
    subprocess.run(["chmod", "644", "/var/www/xrplme.online/index.html"], capture_output=True)

# Restart MCP server to pick up updated instructions
subprocess.run(["systemctl", "restart", "mcp-xrplme.service"], capture_output=True)
import shutil
src = "/tmp/xrplme-examples"
dst = "/var/www/xrplme.online/examples"
if os.path.exists(src):
    pw = open(os.path.expanduser("~/.pb_pw_675377")).read().strip()
    subprocess.run(["sudo", "-kS"], input=(pw + chr(10)).encode(), capture_output=True)
    subprocess.run(["sudo", "-n", "rm", "-f", dst + "/example_xrplme_agent.py"])
    subprocess.run(["sudo", "-n", "cp", "-rT", src, dst], check=True)
    subprocess.run(["sudo", "-n", "chmod", "-R", "755", dst], capture_output=True)
print("Examples deployed")
print("MCP server restarted")

subprocess.run(["systemctl", "restart", "mcp-xrplme.service"], capture_output=True)
import shutil
src = "/tmp/xrplme-examples"
dst = "/var/www/xrplme.online/examples"
if os.path.exists(src):
    pw = open(os.path.expanduser("~/.pb_pw_675377")).read().strip()
    subprocess.run(["sudo", "-kS"], input=(pw + chr(10)).encode(), capture_output=True)
    subprocess.run(["sudo", "-n", "rm", "-f", dst + "/example_xrplme_agent.py"])
    subprocess.run(["sudo", "-n", "cp", "-rT", src, dst], check=True)
    subprocess.run(["sudo", "-n", "chmod", "-R", "755", dst], capture_output=True)
print("Examples deployed")
print("MCP server restarted")
print("All deployed OK")
