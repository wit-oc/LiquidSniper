"""Task 16 non-bypass propose -> policy -> execute boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import os
from pathlib import Path
import threading

from .bankroll import BankrollState
from .paper_artifacts import persist_run_artifact
from .policy_gate import PolicyGateValidationError, validate_trade_intent
from .mode_guard import guard_parallel_mode
from .risk_breaker import apply_pnl, evaluate_drawdown, load_state, persist_state, utc_day


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
        self._lock = threading.Lock()

    def _breaker_state_path(self) -> Path:
        root = os.getenv("LS_ARTIFACT_ROOT") or os.getenv("LIQUIDSNIPER_ARTIFACT_ROOT") or "artifacts"
        return Path(root) / "paper_mvp" / "state" / "global_drawdown_breaker_state.json"

    def _breaker_limits(self) -> tuple[float | None, float | None]:
        raw_abs = os.getenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD")
        raw_pct = os.getenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_PCT")
        abs_limit = float(raw_abs) if raw_abs not in {None, ""} else None
        pct_limit = float(raw_pct) if raw_pct not in {None, ""} else None
        return abs_limit, pct_limit

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
        with self._lock:
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

            breaker_state_path = self._breaker_state_path()
            abs_limit, pct_limit = self._breaker_limits()
            try:
                breaker_state = load_state(
                    breaker_state_path,
                    starting_equity_usd=self._bankroll.snapshot().starting_equity_usd,
                    day=utc_day(),
                )
            except ValueError:
                return {
                    "proposal_id": proposal_id,
                    "decision": "blocked",
                    "reason_codes": ("GLOBAL_DRAWDOWN_STATE_UNREADABLE",),
                    "trace_id": proposal.get("trace_id"),
                    "policy_version": proposal.get("policy_version"),
                }

            tripped, trip_reason = evaluate_drawdown(
                breaker_state,
                max_daily_drawdown_usd=abs_limit,
                max_daily_drawdown_pct=pct_limit,
            )
            if tripped:
                breaker_state.tripped = True
                breaker_state.trip_reason = trip_reason
                persist_state(breaker_state_path, breaker_state)
                return {
                    "proposal_id": proposal_id,
                    "decision": "blocked",
                    "reason_codes": (trip_reason,),
                    "trace_id": proposal.get("trace_id"),
                    "policy_version": proposal.get("policy_version"),
                }

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

            realized_pnl = self._paper_pnl_usd(proposal, adapter_result)
            unrealized_pnl = adapter_result.get("unrealized_pnl_usd") if isinstance(adapter_result, dict) else None

            if is_paper:
                if reserved_risk > 0:
                    self._bankroll.release_reserved(reserved_risk)
                self._bankroll.realize_pnl(realized_pnl)
                out["bankroll"] = self._bankroll.snapshot().__dict__

            apply_pnl(
                breaker_state,
                realized_delta_usd=realized_pnl,
                unrealized_pnl_usd=float(unrealized_pnl) if unrealized_pnl is not None else None,
            )
            tripped_post, trip_reason_post = evaluate_drawdown(
                breaker_state,
                max_daily_drawdown_usd=abs_limit,
                max_daily_drawdown_pct=pct_limit,
            )
            if tripped_post:
                breaker_state.tripped = True
                breaker_state.trip_reason = trip_reason_post
            persist_state(breaker_state_path, breaker_state)
            out["global_breaker"] = {
                "tripped": breaker_state.tripped,
                "trip_reason": breaker_state.trip_reason,
                "drawdown_usd": breaker_state.drawdown_usd,
                "trading_day": breaker_state.trading_day,
            }

            if is_paper and out.get("decision") == "executed":
                _, artifact_path = persist_run_artifact(proposal, out)
                out["paper_run_artifact_path"] = str(artifact_path)

            return out
