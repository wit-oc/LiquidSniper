"""Task 16 non-bypass propose -> policy -> execute boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .paper_artifacts import persist_run_artifact
from .policy_gate import PolicyGateValidationError, validate_trade_intent


_REQUIRED_AUDIT_FIELDS = ("trace_id", "policy_version", "rulebook_ref")


@dataclass(frozen=True)
class PolicyDecision:
    accepted: bool
    reason_codes: tuple[str, ...] = ()
    trace_id: str = ""
    policy_version: str = ""


class ExecutionBoundary:
    """Enforces a strict propose -> policy -> execute handshake.

    Strategy output must be submitted as a proposal and paired with a policy
    decision before execution is allowed.
    """

    def __init__(self) -> None:
        self._proposals: dict[str, dict[str, Any]] = {}
        self._next_id = 1

    def propose_trade(self, proposal: dict[str, Any], policy: PolicyDecision | None) -> dict[str, Any]:
        missing = [k for k in _REQUIRED_AUDIT_FIELDS if not str(proposal.get(k) or "").strip()]
        if missing:
            return {
                "decision": "rejected",
                "reason_codes": tuple(f"MISSING_{m.upper()}" for m in missing),
                "trace_id": proposal.get("trace_id"),
                "policy_version": proposal.get("policy_version"),
            }

        proposal_id = f"prop_{self._next_id:06d}"
        self._next_id += 1

        mode = str(proposal.get("mode") or "paper")
        if mode == "paper":
            trade_intent_payload = proposal.get("trade_intent")
            if not isinstance(trade_intent_payload, dict):
                rec = {
                    "proposal": dict(proposal),
                    "approved": False,
                    "executed": False,
                    "reason_codes": ("TRADE_INTENT_REQUIRED",),
                }
                self._proposals[proposal_id] = rec
                return {
                    "proposal_id": proposal_id,
                    "decision": "rejected",
                    "reason_codes": rec["reason_codes"],
                    "trace_id": proposal.get("trace_id"),
                    "policy_version": proposal.get("policy_version"),
                }
            try:
                normalized_trade_intent = validate_trade_intent(trade_intent_payload).normalized
            except PolicyGateValidationError as exc:
                rec = {
                    "proposal": dict(proposal),
                    "approved": False,
                    "executed": False,
                    "reason_codes": (f"TRADE_INTENT_{exc.reason_code}",),
                }
                self._proposals[proposal_id] = rec
                return {
                    "proposal_id": proposal_id,
                    "decision": "rejected",
                    "reason_codes": rec["reason_codes"],
                    "trace_id": proposal.get("trace_id"),
                    "policy_version": proposal.get("policy_version"),
                }

            proposal = dict(proposal)
            proposal["trade_intent"] = normalized_trade_intent

        if policy is None:
            rec = {
                "proposal": dict(proposal),
                "approved": False,
                "executed": False,
                "reason_codes": ("POLICY_DECISION_REQUIRED",),
            }
            self._proposals[proposal_id] = rec
            return {
                "proposal_id": proposal_id,
                "decision": "rejected",
                "reason_codes": rec["reason_codes"],
                "trace_id": proposal["trace_id"],
                "policy_version": proposal["policy_version"],
            }

        if policy.trace_id != proposal["trace_id"] or policy.policy_version != proposal["policy_version"]:
            rec = {
                "proposal": dict(proposal),
                "approved": False,
                "executed": False,
                "reason_codes": ("POLICY_DECISION_MISMATCH",),
            }
            self._proposals[proposal_id] = rec
            return {
                "proposal_id": proposal_id,
                "decision": "rejected",
                "reason_codes": rec["reason_codes"],
                "trace_id": proposal["trace_id"],
                "policy_version": proposal["policy_version"],
            }

        approved = bool(policy.accepted)
        reason_codes = policy.reason_codes if policy.reason_codes else (() if approved else ("POLICY_REJECTED",))
        rec = {
            "proposal": dict(proposal),
            "approved": approved,
            "executed": False,
            "reason_codes": tuple(reason_codes),
        }
        self._proposals[proposal_id] = rec
        return {
            "proposal_id": proposal_id,
            "decision": "accepted" if approved else "rejected",
            "reason_codes": rec["reason_codes"],
            "trace_id": proposal["trace_id"],
            "policy_version": proposal["policy_version"],
            "rulebook_ref": proposal["rulebook_ref"],
        }

    def execute_approved(self, proposal_id: str) -> dict[str, Any]:
        rec = self._proposals.get(proposal_id)
        if rec is None:
            return {
                "decision": "blocked",
                "reason_codes": ("PROPOSAL_NOT_FOUND",),
            }

        proposal = rec["proposal"]
        mode = str(proposal.get("mode") or "paper")
        if mode != "paper":
            return {
                "proposal_id": proposal_id,
                "decision": "blocked",
                "reason_codes": ("MODE_NOT_ALLOWED",),
                "trace_id": proposal["trace_id"],
                "policy_version": proposal["policy_version"],
            }

        if not rec["approved"]:
            return {
                "proposal_id": proposal_id,
                "decision": "blocked",
                "reason_codes": ("PROPOSAL_NOT_APPROVED",),
                "trace_id": proposal["trace_id"],
                "policy_version": proposal["policy_version"],
            }

        if rec["executed"]:
            return {
                "proposal_id": proposal_id,
                "decision": "noop",
                "reason_codes": ("ALREADY_EXECUTED",),
                "trace_id": proposal["trace_id"],
                "policy_version": proposal["policy_version"],
            }

        rec["executed"] = True
        return {
            "proposal_id": proposal_id,
            "decision": "executed",
            "reason_codes": (),
            "trace_id": proposal["trace_id"],
            "policy_version": proposal["policy_version"],
            "rulebook_ref": proposal["rulebook_ref"],
            "execution_mode": proposal.get("mode") or "paper",
        }

    def execute_with_adapter(
        self,
        proposal_id: str,
        adapter: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute only after gate pass; never call adapter on blocked/rejected proposals."""
        gate = self.execute_approved(proposal_id)
        if gate.get("decision") != "executed":
            return gate

        rec = self._proposals.get(proposal_id)
        if rec is None:
            return {
                "decision": "blocked",
                "reason_codes": ("PROPOSAL_NOT_FOUND",),
            }

        adapter_result = adapter(dict(rec["proposal"]))
        out = dict(gate)
        out["adapter_result"] = adapter_result

        if str(rec["proposal"].get("mode") or "paper") == "paper" and out.get("decision") == "executed":
            _, artifact_path = persist_run_artifact(rec["proposal"], out)
            out["paper_run_artifact_path"] = str(artifact_path)

        return out
