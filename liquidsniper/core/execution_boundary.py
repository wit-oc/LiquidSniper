"""Task 16 non-bypass propose -> policy -> execute boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import os

from .bankroll import BankrollState
from .paper_artifacts import persist_run_artifact
from .policy_gate import PolicyGateValidationError, validate_trade_intent
from .mode_guard import guard_parallel_mode


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

    def __init__(self, *, starting_bankroll_usd: float | None = None) -> None:
        self._proposals: dict[str, dict[str, Any]] = {}
        self._next_id = 1
        configured = starting_bankroll_usd
        if configured is None:
            configured = float(os.getenv("LIQUIDSNIPER_PAPER_BANKROLL_USD", "10000"))
        self._bankroll = BankrollState(float(configured))

    def _paper_risk_usd(self, proposal: dict[str, Any]) -> float:
        direct = proposal.get("risk_usd")
        trade_intent = proposal.get("trade_intent") if isinstance(proposal.get("trade_intent"), dict) else {}
        if direct is None:
            direct = trade_intent.get("risk_usd")
        if direct is None:
            return 0.0
        try:
            risk = float(direct)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, risk)

    def _paper_pnl_usd(self, proposal: dict[str, Any], adapter_result: dict[str, Any]) -> float:
        raw = adapter_result.get("pnl_usd")
        if raw is None:
            raw = proposal.get("pnl_usd")
        if raw is None:
            return 0.0
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

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
        guard = guard_parallel_mode(mode=mode, payload=proposal)
        if not guard.allowed:
            rec = {
                "proposal": dict(proposal),
                "approved": False,
                "executed": False,
                "reason_codes": (guard.reason_code,),
            }
            self._proposals[proposal_id] = rec
            return {
                "proposal_id": proposal_id,
                "decision": "rejected",
                "reason_codes": rec["reason_codes"],
                "trace_id": proposal.get("trace_id"),
                "policy_version": proposal.get("policy_version"),
            }
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

        proposal = dict(rec["proposal"])
        is_paper = str(proposal.get("mode") or "paper") == "paper"
        reserved_risk = 0.0

        if is_paper:
            reserved_risk = self._paper_risk_usd(proposal)
            if reserved_risk > 0 and not self._bankroll.reserve_risk(reserved_risk):
                return {
                    "proposal_id": proposal_id,
                    "decision": "blocked",
                    "reason_codes": ("BANKROLL_EXHAUSTED",),
                    "trace_id": proposal.get("trace_id"),
                    "policy_version": proposal.get("policy_version"),
                    "bankroll": self._bankroll.snapshot().__dict__,
                }

        adapter_result = adapter(proposal)
        out = dict(gate)
        out["adapter_result"] = adapter_result

        if is_paper:
            if reserved_risk > 0:
                self._bankroll.release_reserved(reserved_risk)
            self._bankroll.realize_pnl(self._paper_pnl_usd(proposal, adapter_result))
            out["bankroll"] = self._bankroll.snapshot().__dict__

        if is_paper and out.get("decision") == "executed":
            _, artifact_path = persist_run_artifact(proposal, out)
            out["paper_run_artifact_path"] = str(artifact_path)

        return out
