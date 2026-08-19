"""SOC Triage Agent with OpenAI & Anthropic support + Mock Mode."""
import json
import os
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError

try:
    from openai import OpenAI, AuthenticationError as OpenAIAuthError
except ImportError:
    OpenAI = None
    OpenAIAuthError = Exception

try:
    from anthropic import Anthropic
    from anthropic import AuthenticationError as AnthropicAuthError
    from anthropic import NotFoundError as AnthropicNotFoundError
except ImportError:
    Anthropic = None
    AnthropicAuthError = Exception
    AnthropicNotFoundError = Exception

from schemas import RawSecurityLog, ThreatTriageReport, SeverityLevel, ThreatCategory, ActionType, MitigationStep

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class SOCTriageAgent:
    """Production SOC Triage Agent supporting OpenAI & Anthropic with stateful schema recovery."""

    ANTHROPIC_FALLBACK_MODELS = [
        "claude-sonnet-4-6",
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-5-20250929",
    ]

    def __init__(
        self,
        provider: Literal["openai", "anthropic"] = "openai",
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.provider = provider.lower()
        self.max_retries = max_retries
        self.mock_mode = os.getenv("MOCK_LLM", "false").lower() == "true"

        if self.mock_mode:
            logger.warning("🧪 MOCK MODE ENABLED — No live API calls will be made.")
            self.model = model or "mock-llm"
            return

        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.model = model or "gpt-4o-mini"
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key or api_key.lower().startswith("your_") or "placeholder" in api_key.lower():
                raise ValueError(
                    "OPENAI_API_KEY is missing or contains a placeholder.\n"
                    f"  → Set a real key in {env_path} or export OPENAI_API_KEY=sk-..."
                )
            self.openai_client = OpenAI(api_key=api_key)

        elif self.provider == "anthropic":
            if Anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.model = model or "claude-sonnet-4-6"
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
            if not api_key or len(api_key) < 20:
                raise ValueError(
                    "ANTHROPIC_API_KEY is missing or looks invalid.\n"
                    f"  → Set a real key in {env_path} or export ANTHROPIC_API_KEY=sk-ant-..."
                )
            self.anthropic_client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'.")

    def _mock_triage(self, log: RawSecurityLog) -> ThreatTriageReport:
        """Return a realistic synthetic report for offline testing."""
        event = log.event_type.upper()
        if "DUMP" in event or "EXFIL" in event or "OUTBOUND" in event:
            severity = SeverityLevel.CRITICAL
            category = ThreatCategory.DATA_EXFILTRATION
            action = ActionType.AUTO_CONTAIN
            confidence = 0.96
            summary = (
                f"Detected large outbound data transfer via {log.event_type} "
                f"from {log.source_ip}. Immediate containment required."
            )
        elif "SSH" in event or "AUTH" in event or "LOGIN" in event:
            severity = SeverityLevel.HIGH
            category = ThreatCategory.AUTHENTICATION
            action = ActionType.ESCALATE_TO_SOC
            confidence = 0.88
            summary = (
                f"Repeated unauthorized access attempts ({log.event_type}) "
                f"detected from {log.source_ip}."
            )
        elif "MALWARE" in event or "RANSOM" in event:
            severity = SeverityLevel.CRITICAL
            category = ThreatCategory.MALWARE
            action = ActionType.AUTO_CONTAIN
            confidence = 0.94
            summary = f"Malicious activity ({log.event_type}) detected on {log.source_ip}."
        else:
            severity = SeverityLevel.MEDIUM
            category = ThreatCategory.RECONNAISSANCE
            action = ActionType.MONITOR
            confidence = 0.72
            summary = f"Anomalous activity ({log.event_type}) observed from {log.source_ip}."

        return ThreatTriageReport(
            log_id=log.log_id,
            severity=severity,
            category=category,
            confidence_score=confidence,
            summary=summary,
            mitigation_plan=[
                MitigationStep(
                    step_number=1,
                    action=f"Isolate host {log.source_ip} from production network segment",
                    requires_human_approval=True,
                ),
                MitigationStep(
                    step_number=2,
                    action="Revoke active sessions and rotate compromised credentials",
                    requires_human_approval=True,
                ),
            ],
            recommended_action=action,
            reasoning_trace=(
                f"1. Parsed event type '{log.event_type}' against threat taxonomy.\n"
                f"2. Assessed source IP {log.source_ip} against internal asset registry.\n"
                f"3. Confidence {confidence} derived from indicator correlation."
            ),
        )

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert Security Operations Center (SOC) Level 3 Analyst Agent.\n"
            "Your task is to analyze incoming raw SIEM logs and output a strict JSON triage report.\n\n"
            "═══════════════════════════════════════════════════════════════════════\n"
            "  CLASSIFICATION RUBRIC — APPLY THESE RULES EXACTLY\n"
            "═══════════════════════════════════════════════════════════════════════\n\n"
            "SEVERITY LEVELS:\n"
            "  • CRITICAL — Active data exfiltration, ransomware deployment, confirmed\n"
            "    compromise of privileged accounts, or large-volume unauthorized transfer\n"
            "    to external destinations. Time-sensitive; immediate response required.\n"
            "  • HIGH     — Repeated brute-force attacks, unauthorized lateral movement,\n"
            "    or malware indicators. Requires prompt analyst investigation.\n"
            "  • MEDIUM   — Reconnaissance (port scans, enumeration), suspicious but\n"
            "    non-destructive activity. May be security tooling or low-risk probing.\n"
            "  • LOW      — Policy violations, minor anomalies, or benign misconfigurations.\n\n"
            "THREAT CATEGORIES:\n"
            "  • DATA_EXFILTRATION — Unauthorized outbound transfer of sensitive data,\n"
            "    database dumps, or bulk file extraction to external IPs.\n"
            "  • AUTHENTICATION    — Failed login storms, credential stuffing,\n"
            "    unauthorized SSH/RDP attempts, or privilege escalation.\n"
            "  • MALWARE           — Ransomware encryption, trojan execution,\n"
            "    suspicious process behavior, or known IOC matches.\n"
            "  • LATERAL_MOVEMENT  — SMB/WinRM/RDP hops between internal hosts,\n"
            "    pass-the-hash, or unexpected service account usage on new machines.\n"
            "  • RECONNAISSANCE    — Port scans, DNS enumeration, directory traversal,\n"
            "    or OSINT-style probing from internal or external sources.\n"
            "  • UNKNOWN           — Insufficient data to classify; use sparingly.\n\n"
            "RECOMMENDED ACTIONS:\n"
            "  • AUTO_CONTAIN        — Use ONLY when there is ACTIVE, ONGOING harm\n"
            "    (data exfiltration in progress, ransomware spreading, live C2 beacon).\n"
            "    Requires high confidence (>0.90) and clear malicious indicators.\n"
            "  • ESCALATE_TO_SOC     — Use for HIGH-severity events that need human\n"
            "    analyst judgment before containment (brute force, suspected compromise).\n"
            "  • MONITOR             — Use for MEDIUM/LOW reconnaissance or anomalies\n"
            "    that may be benign security tooling or low-risk probing.\n"
            "  • IGNORE_FALSE_POSITIVE — Use ONLY when the event is clearly benign\n"
            "    (e.g., scheduled backup, authorized penetration test, known good IP).\n\n"
            "═══════════════════════════════════════════════════════════════════════\n\n"
            "CRITICAL REQUIREMENT:\n"
            "You MUST respond ONLY with valid JSON conforming strictly to the provided\n"
            "Pydantic JSON Schema. Do NOT include markdown wrapping, preamble, or commentary."
        )

    def _call_model(self, messages: list, system_prompt: str) -> str:
        if self.mock_mode:
            return "{\"mock\": true}"
        if self.provider == "openai":
            return self._call_openai(messages, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(messages, system_prompt)
        raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_openai(self, messages: list, system_prompt: str) -> str:
        try:
            formatted_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return response.choices[0].message.content or "{}"
        except OpenAIAuthError as e:
            raise RuntimeError(
                f"OpenAI Authentication failed (401). Your API key is invalid or expired.\n"
                f"  → Check {PROJECT_ROOT / '.env'} has a real key starting with 'sk-'"
            ) from e
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _call_anthropic(self, messages: list, system_prompt: str) -> str:
        anthropic_messages = [m for m in messages if m.get("role") != "system"]
        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=anthropic_messages,
                temperature=0.1,
            )
            return response.content[0].text or "{}"
        except AnthropicAuthError as e:
            raise RuntimeError(
                "Anthropic Authentication failed (401). Your API key is invalid or expired."
            ) from e
        except AnthropicNotFoundError as e:
            retired_notice = ""
            if "claude-3" in self.model:
                retired_notice = (
                    "\n  ⚠️  Claude 3.x models were retired in 2025–2026. "
                    "You MUST use Claude 4.x model IDs."
                )
            raise RuntimeError(
                f"Anthropic model '{self.model}' returned 404 (Not Found).{retired_notice}\n"
                f"  → Your API key may not have access to this model.\n"
                f"  → Try current active models: {', '.join(self.ANTHROPIC_FALLBACK_MODELS)}\n"
                f"  → Or run with --mock to test offline."
            ) from e
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def triage_log(self, log: RawSecurityLog) -> ThreatTriageReport:
        """Processes a raw SIEM log and returns a guaranteed ThreatTriageReport with retry loops."""
        if self.mock_mode:
            return self._mock_triage(log)

        logger.info(
            f"[{self.provider.upper()} | {self.model}] Triaging Log ID: {log.log_id} | Event: {log.event_type}"
        )

        schema_json = json.dumps(ThreatTriageReport.model_json_schema(), indent=2)
        user_prompt = (
            f"Target JSON Schema:\n{schema_json}\n\n"
            f"Incoming Raw Security Log:\n{log.model_dump_json(indent=2)}\n\n"
            "Analyze the threat, assess confidence, outline mitigation steps, and recommend an action."
        )
        messages = [{"role": "user", "content": user_prompt}]
        system_prompt = self._build_system_prompt()

        for attempt in range(1, self.max_retries + 1):
            logger.debug(f"[Attempt {attempt}/{self.max_retries}] {self.provider} | {self.model}")
            raw_response_text = self._call_model(messages, system_prompt)

            clean_text = raw_response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            try:
                parsed_json = json.loads(clean_text)
            except json.JSONDecodeError as e:
                logger.error(f"[Attempt {attempt}] Invalid JSON: {e}")
                messages.append({"role": "assistant", "content": raw_response_text})
                messages.append({
                    "role": "user",
                    "content": f"Your output failed JSON parsing: {e}. Output ONLY valid raw JSON.",
                })
                continue

            try:
                triage_report = ThreatTriageReport.model_validate(parsed_json)
                logger.success(
                    f"[{self.provider.upper()}] Triage OK | {log.log_id} | "
                    f"Severity: {triage_report.severity.value} | Action: {triage_report.recommended_action.value}"
                )
                return triage_report
            except ValidationError as ve:
                logger.warning(f"[Attempt {attempt}] Schema validation failed.")
                messages.append({"role": "assistant", "content": raw_response_text})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Schema validation errors:\n{json.dumps(ve.errors(), indent=2)}\n\n"
                        "Correct fields strictly and return raw JSON only."
                    ),
                })

        raise RuntimeError(
            f"Failed to extract valid ThreatTriageReport for {log.log_id} after {self.max_retries} attempts."
        )

    @staticmethod
    def list_anthropic_models():
        """Print currently active Anthropic model IDs for reference."""
        print("\n📋 Active Anthropic Model IDs (as of 2026):")
        print("-" * 50)
        for m in SOCTriageAgent.ANTHROPIC_FALLBACK_MODELS:
            print(f"  • {m}")
        print("-" * 50)
        print("Usage: python main.py --provider anthropic --model claude-sonnet-4-6")


if __name__ == "__main__":
    from datetime import datetime
    mock_log = RawSecurityLog(
        log_id="LOG-LOCAL-001",
        timestamp=datetime.now(),
        source_ip="10.0.4.15",
        destination_ip="192.168.1.1",
        user_id="admin_test",
        event_type="UNAUTHORIZED_SSH_ATTEMPT",
        payload_summary="15 failed SSH login attempts in 30 seconds from internal subnet.",
    )
    agent = SOCTriageAgent(provider="anthropic")
    print(f"Agent ready: {agent.provider} | {agent.model}")