import re
import json
from typing import Dict, Any, Optional, List
from google.adk.agents import Agent

# -----------------------
# Knowledge Base (3 fields/asset)
# -----------------------
KB: Dict[str, Dict[str, Dict[str, Any]]] = {
    "server": {
        "system_name": {
            "label": "System Name / Hostname",
            "description": "Unique identifier for the server used in network, CMDB, and documentation.",
            "value_type": "string",
            "allowed_values": None,
            "examples": ["FACT-CTRL-SRV-01", "PLT-A-SCADA-SRV", "DB-PRD-01"],
            "validation": {
                "pattern": r"^[A-Za-z0-9\-]{3,32}$",
                "max_length": 32,
                "notes": "Letters, digits, hyphens only; 3–32 chars."
            },
            "how_to_find": [
                "Windows: run `hostname` in Command Prompt.",
                "Linux: `hostnamectl status` or `cat /etc/hostname`.",
                "Check server labels or CMDB."
            ],
            "ui_hint": "text",
        },
        "type": {
            "label": "Type (Physical / Virtual)",
            "description": "Whether the server is a physical box or a virtual machine.",
            "value_type": "enum",
            "allowed_values": ["Physical", "Virtual"],
            "examples": ["Physical", "Virtual"],
            "validation": {"pattern": None, "max_length": None, "notes": "Choose one."},
            "how_to_find": [
                "Physical if racked hardware; Virtual if on VMware/Hyper-V/Azure/AWS.",
                "Check hypervisor inventory or CMDB."
            ],
            "ui_hint": "radio",
        },
        "operating_system": {
            "label": "Operating System",
            "description": "Primary OS running on the server.",
            "value_type": "enum",
            "allowed_values": ["Windows Server", "Ubuntu", "RHEL", "CentOS", "VMware ESXi", "Other"],
            "examples": ["Windows Server 2019", "Ubuntu 22.04 LTS", "VMware ESXi 8.0"],
            "validation": {"pattern": None, "max_length": 40, "notes": "If 'Other', specify distro/version."},
            "how_to_find": [
                "Windows: Win+R → `winver` or Settings → System → About.",
                "Linux: `cat /etc/os-release`.",
                "ESXi: vSphere host summary."
            ],
            "ui_hint": "select",
        },
    },
    "pc_hmi": {
        "system_name": {
            "label": "System Name / Hostname",
            "description": "Unique name for the HMI workstation in PLC/SCADA networks.",
            "value_type": "string",
            "allowed_values": None,
            "examples": ["HMI-LINE1-01", "PACK-HMI-02", "SCADA-HMI-01"],
            "validation": {
                "pattern": r"^[A-Za-z0-9\-]{3,32}$",
                "max_length": 32,
                "notes": "Letters, digits, hyphens only; 3–32 chars."
            },
            "how_to_find": [
                "Windows: run `hostname`.",
                "Check desktop sticker/asset tag or HMI vendor config."
            ],
            "ui_hint": "text",
        },
        "type": {
            "label": "HMI Type",
            "description": "Form factor of the HMI device.",
            "value_type": "enum",
            "allowed_values": ["Industrial PC", "Panel PC", "Standard Desktop"],
            "examples": ["Industrial PC", "Panel PC"],
            "validation": {"pattern": None, "max_length": None, "notes": "Choose the closest option."},
            "how_to_find": [
                "Inspect device chassis or vendor model documentation.",
                "Ask controls/maintenance team."
            ],
            "ui_hint": "select",
        },
        "operating_system": {
            "label": "Operating System",
            "description": "OS used by the HMI, often specified by SCADA vendor.",
            "value_type": "enum",
            "allowed_values": ["Windows 10", "Windows 11", "Windows Server", "Ubuntu", "RHEL", "Other"],
            "examples": ["Windows 10 LTSC", "Windows 11 Pro"],
            "validation": {"pattern": None, "max_length": 40, "notes": "If 'Other', specify distro/version."},
            "how_to_find": [
                "Windows: Settings → System → About.",
                "Linux: `cat /etc/os-release`."
            ],
            "ui_hint": "select",
        },
    },
}

# -----------------------
# Tool 1: Field Info
# -----------------------
def get_asset_field_info(asset_type: str, asset_field: str) -> dict:
    """Return rich guidance for a specific asset field."""
    a = asset_type.lower().replace(" ", "_")
    f = asset_field.lower().replace(" ", "_")
    if a not in KB:
        return {"status": "error", "error_message": f"Unknown asset_type '{asset_type}'. Supported: {list(KB.keys())}"}
    if f not in KB[a]:
        return {"status": "error", "error_message": f"Unknown field '{asset_field}' for asset_type '{asset_type}'. Supported: {list(KB[a].keys())}"}
    return {"status": "success", "field": KB[a][f], "asset_type": a, "asset_field": f}

# -----------------------
# Tool 2: Deterministic Rule Check (regex/enums)
# -----------------------
def rule_check_value(asset_type: str, asset_field: str, value: str) -> dict:
    """Apply deterministic checks (enum membership, regex, length). Returns pass/fail with reasons."""
    info = get_asset_field_info(asset_type, asset_field)
    if info.get("status") != "success":
        return info

    meta = info["field"]
    vt = meta.get("value_type")
    allowed = meta.get("allowed_values")
    val_rules = meta.get("validation", {})
    pattern = val_rules.get("pattern")
    max_len = val_rules.get("max_length")

    reasons: List[str] = []
    passed = True

    # Enum check
    normalized_value = value.strip()
    if vt == "enum" and allowed:
        # Case-insensitive membership with normalization
        allowed_lower = [x.lower() for x in allowed]
        if normalized_value.lower() not in allowed_lower:
            passed = False
            reasons.append(f"Value not in allowed set {allowed}.")
        else:
            # Normalize to canonical casing from allowed list
            normalized_value = allowed[allowed_lower.index(normalized_value.lower())]

    # Pattern check
    if pattern:
        if not re.fullmatch(pattern, value or ""):
            passed = False
            reasons.append(f"Does not match required pattern: {pattern}")

    # Max length
    if max_len is not None and len(value) > max_len:
        passed = False
        reasons.append(f"Exceeds max length {max_len} characters.")

    return {
        "status": "success",
        "result": {
            "passed": passed,
            "reasons": reasons,
            "normalized_value": normalized_value,
            "value_type": vt,
        }
    }

# -----------------------
# Sub-Agent: LLM Validator
# -----------------------
validator_agent = Agent(
    name="asset_field_validator_llm",
    model="gemini-2.0-flash",
    description="LLM sub-agent that validates a user's value for a specific asset field using domain rules + judgment.",
    instruction=(
        "You validate user-provided values for a given asset_type and asset_field.\n"
        "Inputs you will receive:\n"
        " - asset_type, asset_field, user_value\n"
        " - field metadata (label, description, allowed_values, regex pattern, examples)\n"
        " - results from deterministic rule_check (passed/reasons/normalized_value)\n\n"
        "Your job:\n"
        "1) Consider the rules AND apply domain reasoning. Even if rules pass, flag obviously implausible values "
        "(e.g., system_name '!!!', OS='Windows Server 3020'). If rules fail but the value is close, suggest a correction.\n"
        "2) Output STRICT JSON with keys: "
        '{"decision":"accept"|"revise"|"reject","confidence":0.0-1.0,'
        '"normalized_value":str|null,"reasons":[str,...],"suggestions":[str,...]}.\n'
        " - 'accept' = value is valid; include normalized_value if applicable.\n"
        " - 'revise' = minor fix needed; give clear suggestions.\n"
        " - 'reject' = wrong field or clearly invalid; suggest correct value patterns or examples.\n"
        "Keep responses concise. Output only JSON—no extra prose."
    ),
    tools=[get_asset_field_info, rule_check_value],  # Validator may call tools if needed
)

# -----------------------
# Tool 3: Bridge tool that calls the LLM validator sub-agent
# -----------------------
def llm_validate_asset_field(asset_type: str, asset_field: str, value: str) -> dict:
    """Calls the validator LLM agent with structured context; returns parsed JSON decision."""
    # Gather metadata + rule checks
    info = get_asset_field_info(asset_type, asset_field)
    if info.get("status") != "success":
        return info
    rules = rule_check_value(asset_type, asset_field, value)
    if rules.get("status") != "success":
        return rules

    payload = {
        "asset_type": asset_type,
        "asset_field": asset_field,
        "user_value": value,
        "field_meta": info["field"],
        "rule_check": rules["result"]
    }

    # Instantiate a runner
    from google.adk.runner import Runner
    runner = Runner(agent=validator_agent)

    # Run the agent with a prompt
    response = runner.run("What is the capital of France?")

    # Ask sub-agent
    prompt = (
        "Validate the following asset field value. Remember to output STRICT JSON only.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    raw = runner.run(prompt)
    #raw = validator_agent.invoke(prompt)

    # Try to parse JSON from sub-agent
    try:
        decision = json.loads(str(raw).strip())
        return {"status": "success", "validation": decision}
    except Exception:
        # If parsing fails, return raw text for visibility
        return {"status": "error", "error_message": "Validator returned non-JSON response.", "raw": str(raw)}

# -----------------------
# Root Agent: Asset Field Guide (orchestrator)
# -----------------------
root_agent = Agent(
    name="asset_field_guide_agent",
    model="gemini-2.0-flash",
    description="Guide agent that helps identify asset fields and collect correct values.",
    instruction=(
        "You are an Asset Field Guide.Users the need your help are non technical. \n"
        "ALWAYS extract or request both inputs BEFORE responding helpfully: asset_type and asset_field.\n"
        "Supported asset_types: server, pc_hmi. Fields per asset: system_name, type, operating_system.\n\n"
        "Flow:\n"
        "1) If asset_type is missing, ask the user to specify one of: server, pc_hmi.\n"
        "2) If asset_field is missing, list the valid fields for the chosen asset and ask the user to pick one.\n"
        "3) Once both are known, call get_asset_field_info(asset_type, asset_field) and provide:\n"
        "   - Field label & purpose (1–2 lines), expected value_type, allowed_values (if any), 2–3 examples,\n"
        "   - How to find it (steps), and validation tips—briefly. Use the How to find it (steps) to help guide the user to find the value for the field \n"
        "4) If the user ALSO provided a candidate value, call llm_validate_asset_field(asset_type, asset_field, value)\n"
        "   and summarize the decision: ACCEPT (with normalized value), or what to revise/retry with a single\n"
        "   clear suggestion list. Then ask for confirmation or the corrected value.\n"
        "Keep messages crisp and action oriented. Avoid long paragraphs."
    ),
    tools=[get_asset_field_info, llm_validate_asset_field],
)

# -----------------------
# Usage examples (commented)
# -----------------------
# 1) Guidance (no value yet):
# print(root_agent.run("asset_type=server, asset_field=system_name. Help me fill it."))
#
# 2) Validate a provided value:
# print(root_agent.run("asset_type=server, asset_field=type, value=Virtual"))
#
# 3) Ask for missing inputs:
# print(root_agent.run("I want to enter the OS for my server."))
