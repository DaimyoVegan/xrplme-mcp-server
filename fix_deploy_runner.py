with open("deploy_runner_vps.py") as f:
    content = f.read()

# Replace shutil.copytree lines with sudo cp -rT
old_block = '    shutil.copytree(src, dst, dirs_exist_ok=True)\n    subprocess.run(["chmod", "-R", "755", dst], capture_output=True)'
new_block = '    pw = open(os.path.expanduser("~/.pb_pw_675377")).read().strip()\n    subprocess.run(["sudo", "-kS"], input=pw + chr(10), capture_output=True)\n    subprocess.run(["sudo", "-n", "rm", "-f", dst + "/example_xrplme_agent.py"])\n    subprocess.run(["sudo", "-n", "cp", "-rT", src, dst], check=True)\n    subprocess.run(["sudo", "-n", "chmod", "-R", "755", dst], capture_output=True)'

content = content.replace(old_block, new_block)

with open("deploy_runner_vps.py", "w") as f:
    f.write(content)
print("Fixed deploy_runner.py")
