# SOC Triage Agent – Operating Map (Audit)

## 1. Current Human Workflow

A SOC analyst receiving a structured SIEM alert first establishes whether the event is actionable. The analyst reviews the alert timestamp, source and destination entities, rule name, severity, detection logic, and the raw event fields. They normalize obvious inconsistencies such as time zones, host names, usernames, IP addresses, and duplicate events. The analyst then checks surrounding telemetry rather than treating the triggering record as sufficient evidence.

Typical enrichment includes reputation and ownership information for public IPs or domains, DNS history, WHOIS or registration context where useful, endpoint telemetry, identity-provider sign-in activity, firewall/proxy records, EDR process activity, and related SIEM events. The analyst searches for the same indicator across other hosts, users, and time windows to determine whether the alert is isolated or part of a broader campaign. If the alert concerns an account, they examine recent successful and failed logins, impossible-travel signals, MFA events, privilege changes, and unusual application access. If it concerns malware or command-and-control activity, they look for process ancestry, persistence, network connections, and other hosts communicating with the indicator.

The analyst forms a working hypothesis and assigns a disposition such as false positive, benign/expected activity, suspicious requiring monitoring, or confirmed malicious. They consider detection confidence, asset criticality, identity privilege, indicator reputation, corroborating telemetry, and business context. A high-confidence malicious event involving a critical asset or privileged identity is normally escalated quickly. Containment can include isolating an endpoint, disabling an account, blocking an indicator, or restricting access, but destructive or business-impacting actions generally require an authorized responder or incident commander unless an approved automated playbook explicitly permits them.

Common exceptions include incomplete telemetry, stale threat-intelligence data, shared infrastructure, VPN/proxy addresses, legitimate scanners, vulnerability-management activity, penetration tests, service accounts, scheduled jobs, cloud-provider infrastructure, and indicators that appear malicious in isolation but are normal for the organization. Duplicate alerts and alert storms also require correlation so that analysts do not investigate the same underlying incident repeatedly. Analysts escalate when evidence indicates active compromise, lateral movement, credential abuse, data exposure, persistence, or material business impact; they monitor when evidence is weak but the activity remains anomalous; they close as benign or false positive when reliable context explains the behavior.

## 2. Pain Points & Failure Modes

The largest source of delay is fragmented enrichment. Analysts repeatedly copy indicators between the SIEM, EDR, identity platform, DNS tools, threat-intelligence services, and internal asset inventories. Alert payloads also frequently contain missing asset ownership, incomplete user context, inconsistent timestamps, or low-quality indicators. During alert spikes, this manual work creates queues and increases the chance that a high-value alert is overlooked.

Common mistakes include trusting the SIEM severity without validating evidence, treating reputation as proof of maliciousness, failing to account for shared NAT/VPN infrastructure, overlooking related events on another host, and escalating without enough context. The highest-cost false positive is unnecessary containment of a production system or privileged account. The highest-cost false negative is closing a genuine intrusion because the initial indicator looked benign or because corroborating telemetry was not searched.

An AI triage system can also fail in dangerous ways: it can hallucinate enrichment, overstate confidence, confuse an indicator with an observed compromise, leak sensitive telemetry to an external provider, or recommend containment from insufficient evidence. These failures must be treated as security failures rather than ordinary model-quality defects.

## 3. Target State with AI

The agent should own deterministic enrichment and prioritization of a single structured SIEM alert. It should normalize the alert, extract supported observables, identify available context, correlate supplied telemetry, summarize evidence, classify the alert into an explicit disposition taxonomy, assign calibrated confidence, and provide a concise rationale with evidence references. It should clearly distinguish observed facts from inferred hypotheses and report missing information instead of inventing it.

The human remains responsible for containment, account disablement, blocking, remediation, incident declaration, and final closure of ambiguous or high-impact cases. Human approval is required before actions that can interrupt production services, disable identities, destroy evidence, or materially affect a customer.

A good triage decision has four properties: factual grounding in supplied evidence, reproducible reasoning, an explicit confidence level, and an appropriate escalation recommendation. Success should be measured by analyst agreement, false-negative rate, enrichment completeness, time-to-triage reduction, and the rate of unsupported recommendations. The system should improve analyst speed without silently expanding its authority.

## 4. Scope Boundaries (v1)

The first version handles one security alert or IOC at a time from structured SIEM JSON. It supports common observables such as IP addresses, domains, URLs, hashes, usernames, host identifiers, and alert metadata when present in the input. It may normalize fields, correlate related records supplied to the agent, summarize evidence, prioritize the alert, and recommend one of the defined triage dispositions.

It explicitly does **not** autonomously isolate endpoints, disable accounts, block indicators, delete files, modify firewall rules, contact affected customers, declare a security incident, or perform destructive remediation. It does not treat third-party reputation alone as proof of compromise. It does not invent missing telemetry or silently call unapproved external services. Multi-alert incident correlation, autonomous response, malware detonation, forensic acquisition, threat hunting across an entire environment, and case-management automation remain outside v1.

## 5. Simple Before → After Map

**Before:** SIEM alert → analyst manually normalizes fields → copies IOC into reputation/intelligence tools → checks EDR/identity/DNS/firewall context → searches SIEM for related activity → forms hypothesis → decides severity/disposition → documents rationale → escalates or closes.

**After:** Structured SIEM alert → AI validates and normalizes supported fields → enriches only through approved tools/data → correlates supplied context → separates facts from hypotheses → produces disposition, confidence, evidence and missing-context list → human reviews high-impact or ambiguous cases → authorized responder performs containment/remediation → decision and evidence are recorded for audit/evaluation.

The objective is not to replace the SOC analyst. It is to remove repetitive enrichment and prioritization work while preserving human authority over consequential security actions and creating an auditable trail for every recommendation.