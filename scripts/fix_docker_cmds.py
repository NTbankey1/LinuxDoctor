#!/usr/bin/env python3
"""Fix Docker evidence commands that are blocked by SafetyChecker."""
import yaml

with open("data/kb/docker.yaml", "r") as f:
    content = f.read()

old_state = """      - hypothesis_id: "container_crash_loop"
        command: 'c=$(docker ps -a --format "{{.Names}}" 2>/dev/null | head -1); if [ -n "$c" ]; then docker inspect "$c" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); s=d[0][\\"State\\"]; print(f\\"status={s[\\"Status\\"]} exit={s[\\"ExitCode\\"]} oom={s[\\"OOMKilled\\"]}\\")"; else echo "NO_CONTAINERS"; fi'
        parser_regex: "exit=(?P<exit_code>\\d+)\\s+oom=(?P<oom_killed>True|False)"
        fact_key: "container_state"
      - hypothesis_id: "container_crash_loop"
        command: 'c=$(docker ps -a --format "{{.Names}}" 2>/dev/null | head -1); if [ -n "$c" ]; then docker logs "$c" --tail 20 2>&1; else echo "NO_CONTAINERS"; fi'
        parser_regex: "(?P<container_log>.*(?:Error|error|FATAL|panic|Exception|Traceback).*)"
        fact_key: "container_logs" """

new_state = """      - hypothesis_id: "container_crash_loop"
        command: "docker inspect $(docker ps -a -q 2>/dev/null | head -1) 2>/dev/null | python3 -c \\\"import sys,json; d=json.load(sys.stdin); s=d[0]['State']; print(f'exit={s[\\\"ExitCode\\\"]} oom={s[\\\"OOMKilled\\\"]}')\\\" || echo 'NO_CONTAINERS'"
        parser_regex: "exit=(?P<exit_code>\\d+)\\s+oom=(?P<oom_killed>True|False)"
        fact_key: "container_state"
      - hypothesis_id: "container_crash_loop"
        command: "docker logs $(docker ps -a -q 2>/dev/null | head -1) --tail 20 2>&1 || echo 'NO_CONTAINERS'"
        parser_regex: "(?P<container_log>.*(?:Error|error|FATAL|panic|Exception|Traceback).*)"
        fact_key: "container_logs" """

count = content.count(old_state)
if count > 0:
    content = content.replace(old_state, new_state)
    print(f"Fix applied ({count} occurrence(s))")
else:
    print("Pattern not found - checking alternatives...")
    # Check if there are still c=$(docker commands
    if "c=$(docker" in content:
        print("  Found c=$(docker patterns still in file")
        for i, line in enumerate(content.split("\n")):
            if "c=$(docker" in line:
                print(f"  Line {i+1}: {line[:120]}")
    else:
        print("  No c=$(docker patterns found - already fixed!")

with open("data/kb/docker.yaml", "w") as f:
    f.write(content)

print("\nValidating YAML...")
try:
    data = yaml.safe_load(open("data/kb/docker.yaml"))
    rules = data.get("rules", [])
    print(f"  Valid! {len(rules)} rules loaded")
    
    # Check all evidence commands start with allowed commands
    blocked = 0
    for rule in rules:
        for step in rule.get("evidence_gathering", []):
            cmd = step.get("command", "")
            first_word = cmd.split()[0] if cmd else ""
            if first_word == "c" or first_word == "c=$(docker" or (first_word.endswith("=(")):
                print(f"  BLOCKED: Rule {rule['rule_id']} starts with variable: {cmd[:70]}...")
                blocked += 1
    if blocked == 0:
        print("  Zero blocked commands! All evidence gathering starts with allowed cmds.")
except yaml.YAMLError as e:
    print(f"  YAML ERROR: {e}")
