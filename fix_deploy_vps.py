#!/usr/bin/env python3
with open("/home/xrpladmin/deploy_runner.py") as f:
    content = f.read()

# Fix the path issue - proper string quoting
content = content.replace(
    'os.path.expanduser("~/.pb_pw_675377")',
    '"/home/xrpladmin/.pb_pw_675377"'
)

# Fix sudo -n to sudo -kS with password and use -S instead of -n
content = content.replace(
    'subprocess.run(["sudo", "-n", "rm", "-f", dst + "/example_xrplme_agent.py"])',
    'subprocess.run(["sudo", "-kS", "rm", "-f", dst + "/example_xrplme_agent.py"], input=(pw + chr(10)).encode(), capture_output=True)'
)
content = content.replace(
    'subprocess.run(["sudo", "-n", "cp", "-rT", src, dst], check=True)',
    'subprocess.run(["sudo", "-kS", "cp", "-rT", src, dst], input=(pw + chr(10)).encode(), capture_output=True, check=True)'
)
content = content.replace(
    'subprocess.run(["sudo", "-n", "chmod", "-R", "755", dst], capture_output=True)',
    'subprocess.run(["sudo", "-kS", "chmod", "-R", "755", dst], input=(pw + chr(10)).encode(), capture_output=True)'
)

# Also fix the MCP server restart to use -kS instead of -n
content = content.replace(
    'subprocess.run(["sudo", "-n", "systemctl", "restart", "mcp-xrplme.service"],',
    'subprocess.run(["sudo", "-kS", "systemctl", "restart", "mcp-xrplme.service"],'
)
content = content.replace(
    'subprocess.run(["sudo", "-n", "systemctl", "restart", "xrplme-card-payment.service"],',
    'subprocess.run(["sudo", "-kS", "systemctl", "restart", "xrplme-card-payment.service"],'
)

with open("/home/xrpladmin/deploy_runner.py", "w") as f:
    f.write(content)
print("Fixed deploy_runner.py")
