"""
rl_recommender.py
=================
Customer Health Forensics — Phase 5
Reinforcement Learning recommendation optimizer.

Learns which retention actions work best for different customer profiles
by tracking past actions and their outcomes.

Design:
  - State:   customer risk category + primary driver category
  - Actions: retention interventions (re-engagement / support / pricing / etc.)
  - Reward:  reduction in churn probability after action
  - Algorithm: ε-greedy Q-learning with experience replay

Storage:
  - Q-table: JSON (simple, inspectable, no GPU needed)
  - Experience buffer: deque of (state, action, reward, next_state)

This is intentionally simple — Q-learning on a discrete state/action
space is the right choice here. Deep RL would be overkill and non-explainable.
"""

import json
import random
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ── Actions ────────────────────────────────────────────────────
ACTIONS = {
    "re_engagement_email":     "Send personalised re-engagement email with feature highlight",
    "csm_outreach":            "Assign CSM check-in call within 48 hours",
    "discount_offer":          "Offer 15–20% loyalty discount or free month",
    "annual_plan_upgrade":     "Offer annual plan upgrade with cost-saving framing",
    "feature_education":       "Send targeted feature education sequence (3-email drip)",
    "support_escalation":      "Escalate to senior support, root-cause ticket analysis",
    "billing_intervention":    "Proactive billing contact — offer payment plan",
    "executive_outreach":      "Personal reach-out from account executive or founder",
    "onboarding_program":      "Assign onboarding specialist, 30/60/90 day milestones",
    "roi_report":              "Send personalised ROI and value realisation report",
    "product_walkthrough":     "Schedule live product walkthrough session",
    "winback_campaign":        "Full win-back campaign — discount + dedicated support",
}

ACTION_IDS = list(ACTIONS.keys())

# ── States ─────────────────────────────────────────────────────
# State = (risk_tier, primary_driver_category)
RISK_TIERS      = ["Critical", "High", "Medium", "Safe"]
DRIVER_CATS     = ["engagement", "payment", "support", "satisfaction",
                   "contract", "product_adoption", "overall_health",
                   "onboarding", "unknown"]

# ── RL config ──────────────────────────────────────────────────
EPSILON_START    = 1.0
EPSILON_END      = 0.10
EPSILON_DECAY    = 0.995
LEARNING_RATE    = 0.15
DISCOUNT_FACTOR  = 0.90
REPLAY_BUFFER_SIZE = 2000
BATCH_SIZE       = 32
MIN_EXPERIENCES  = 50   # minimum before learning from replay


@dataclass
class Experience:
    state:       tuple
    action:      str
    reward:      float
    next_state:  tuple
    done:        bool = True


class RLRecommender:
    """
    Q-learning recommender for retention actions.

    Usage:
        rl = RLRecommender()
        action = rl.recommend(risk_tier="Critical", driver_cat="engagement")
        # ... execute action, observe outcome ...
        rl.record_outcome(state, action, new_churn_prob, old_churn_prob)
        rl.save(path)
    """

    def __init__(self, load_path: Path = None):
        self.q_table  = defaultdict(lambda: defaultdict(float))
        self.epsilon  = EPSILON_START
        self.n_steps  = 0
        self.replay   = deque(maxlen=REPLAY_BUFFER_SIZE)
        self.history  = []   # (timestamp, state, action, reward)

        if load_path and Path(load_path).exists():
            self.load(load_path)

    def _state(self, risk_tier: str, driver_cat: str) -> tuple:
        """Normalise state representation."""
        tier = risk_tier   if risk_tier   in RISK_TIERS  else "Medium"
        cat  = driver_cat  if driver_cat  in DRIVER_CATS else "unknown"
        return (tier, cat)

    def recommend(
        self,
        risk_tier:  str,
        driver_cat: str,
        top_k:      int = 3,
        explore:    bool = False,
    ) -> list[dict]:
        """
        Return top-K recommended actions for a customer state.

        Args:
            risk_tier:  "Critical" / "High" / "Medium" / "Safe"
            driver_cat: Primary driver category from rule engine
            top_k:      Number of actions to return
            explore:    Force exploration (ignore Q-values)

        Returns:
            List of action dicts sorted by expected value.
        """
        state = self._state(risk_tier, driver_cat)

        # ε-greedy: explore vs exploit
        if explore or (random.random() < self.epsilon and self.n_steps < 1000):
            # Random exploration
            selected = random.sample(ACTION_IDS, min(top_k, len(ACTION_IDS)))
        else:
            # Exploit: sort by Q-value
            q_vals   = {a: self.q_table[state][a] for a in ACTION_IDS}
            # Add small prior based on domain knowledge for cold start
            q_vals   = self._apply_priors(q_vals, risk_tier, driver_cat)
            selected = sorted(q_vals, key=q_vals.get, reverse=True)[:top_k]

        return [
            {
                "action_id":    a,
                "description":  ACTIONS[a],
                "q_value":      round(self.q_table[state][a], 4),
                "state":        {"risk_tier": risk_tier, "driver_cat": driver_cat},
                "rank":         i + 1,
            }
            for i, a in enumerate(selected)
        ]

    def _apply_priors(self, q_vals: dict, risk_tier: str, driver_cat: str) -> dict:
        """
        Inject domain-knowledge priors for cold-start (no learned Q-values yet).
        These priors are overridden as the RL agent accumulates experience.
        """
        q = dict(q_vals)

        # Engagement decline → re-engagement + education
        if driver_cat == "engagement":
            q["re_engagement_email"]  += 2.0
            q["feature_education"]    += 1.5
            q["product_walkthrough"]  += 1.2

        # Payment stress → billing intervention
        elif driver_cat == "payment":
            q["billing_intervention"] += 2.5
            q["discount_offer"]       += 1.5
            q["annual_plan_upgrade"]  += 1.0

        # Support friction → escalation
        elif driver_cat == "support":
            q["support_escalation"]   += 2.0
            q["product_walkthrough"]  += 1.5
            q["csm_outreach"]         += 1.0

        # Low NPS / satisfaction → executive outreach
        elif driver_cat == "satisfaction":
            q["executive_outreach"]   += 2.5
            q["csm_outreach"]         += 2.0
            q["roi_report"]           += 1.0

        # New customer / onboarding
        elif driver_cat == "onboarding":
            q["onboarding_program"]   += 3.0
            q["csm_outreach"]         += 1.5

        # Critical tier always elevates high-touch actions
        if risk_tier == "Critical":
            q["executive_outreach"]   += 1.0
            q["csm_outreach"]         += 1.0
            q["winback_campaign"]     += 0.5

        return q

    def record_outcome(
        self,
        risk_tier:      str,
        driver_cat:     str,
        action:         str,
        old_churn_prob: float,
        new_churn_prob: float,
        next_risk_tier: str = None,
        next_driver_cat: str = None,
    ) -> float:
        """
        Record the outcome of a recommendation and update Q-table.

        Reward function:
          - Positive reward for churn probability reduction
          - Negative reward for worsening
          - Bonus for Critical → High improvement

        Returns:
            Reward value.
        """
        state      = self._state(risk_tier, driver_cat)
        next_state = self._state(
            next_risk_tier  or risk_tier,
            next_driver_cat or driver_cat,
        )

        # Reward: scaled probability reduction
        delta  = old_churn_prob - new_churn_prob
        reward = delta * 10.0   # scale to make Q-values meaningful

        # Bonus for tier improvement
        tier_order = {"Critical": 3, "High": 2, "Medium": 1, "Safe": 0}
        if (tier_order.get(next_risk_tier or risk_tier, 0) <
                tier_order.get(risk_tier, 0)):
            reward += 2.0    # moved to safer tier

        # Add to experience buffer
        exp = Experience(state, action, reward, next_state)
        self.replay.append(exp)
        self.history.append({
            "state":          str(state),
            "action":         action,
            "reward":         round(reward, 4),
            "old_prob":       round(old_churn_prob, 4),
            "new_prob":       round(new_churn_prob, 4),
        })

        # Direct Q update
        self._update_q(state, action, reward, next_state)

        # Experience replay (learn from past)
        if len(self.replay) >= MIN_EXPERIENCES:
            self._experience_replay()

        # Decay epsilon
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)
        self.n_steps += 1

        return reward

    def _update_q(self, state, action, reward, next_state):
        """Standard Q-learning update."""
        current_q  = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values()) \
                     if self.q_table[next_state] else 0.0
        target     = reward + DISCOUNT_FACTOR * max_next_q
        self.q_table[state][action] = current_q + LEARNING_RATE * (target - current_q)

    def _experience_replay(self):
        """Sample random batch from replay buffer and update Q-table."""
        batch = random.sample(self.replay, min(BATCH_SIZE, len(self.replay)))
        for exp in batch:
            self._update_q(exp.state, exp.action, exp.reward, exp.next_state)

    def get_policy_summary(self) -> dict:
        """Return the current learned policy as a human-readable dict."""
        policy = {}
        for state in self.q_table:
            if not self.q_table[state]:
                continue
            best_action = max(self.q_table[state], key=self.q_table[state].get)
            policy[str(state)] = {
                "best_action":  best_action,
                "description":  ACTIONS.get(best_action, ""),
                "q_value":      round(self.q_table[state][best_action], 4),
                "n_actions_explored": len(self.q_table[state]),
            }
        return policy

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "q_table":  {str(k): dict(v) for k, v in self.q_table.items()},
            "epsilon":  self.epsilon,
            "n_steps":  self.n_steps,
            "history":  self.history[-500:],   # keep last 500
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[RL] Policy saved → {path} ({self.n_steps} steps learned)")

    def load(self, path: Path) -> None:
        path = Path(path)
        with open(path) as f:
            data = json.load(f)
        for state_str, actions in data.get("q_table", {}).items():
            state = tuple(eval(state_str))
            for action, q_val in actions.items():
                self.q_table[state][action] = q_val
        self.epsilon = data.get("epsilon", EPSILON_START)
        self.n_steps = data.get("n_steps",  0)
        self.history = data.get("history",  [])
        print(f"[RL] Policy loaded from {path} ({self.n_steps} steps)")

    def __repr__(self):
        return (f"RLRecommender(steps={self.n_steps}, "
                f"epsilon={self.epsilon:.3f}, "
                f"states_explored={len(self.q_table)})")
