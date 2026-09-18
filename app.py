#!/usr/bin/env python3
"""Q-PATH AI — dependency-free full-stack demo server.

Run with: python3 app.py
Then visit: http://localhost:8000
"""
from __future__ import annotations

import json
import math
import cmath
import os
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "learning_data.json"
DATA.parent.mkdir(exist_ok=True)

DEFAULT_PROFILE = {
    "learner": "Ada Learner", "level": "Beginner", "streak": 4,
    "mastery": {"Qubit fundamentals": 90, "Quantum gates": 82, "Superposition": 75,
                 "Measurement": 64, "Entanglement": 51, "Phase": 43, "Algorithms": 32},
    "misconceptions": {"M06": 2}, "attempts": 0
}

TAXONOMY = {
    "M01": ("Superposition misconception", "A qubit in superposition is not secretly one fixed classical value; measurement samples from its probability distribution."),
    "M02": ("Entanglement misconception", "Entanglement describes correlations in a joint state. It does not transmit information instantly."),
    "M03": ("Measurement misconception", "Measurement samples a basis state and generally collapses the state in that basis."),
    "M04": ("Phase misconception", "Relative phase can affect later interference even when immediate measurement probabilities look unchanged."),
    "M05": ("Gate-order misconception", "Quantum gates usually do not commute, so their order changes the result."),
    "M06": ("Control-target misconception", "For a controlled-X, the control decides whether the operation happens; the target is the qubit that flips."),
    "M07": ("Interference misconception", "Amplitudes—not probabilities—combine before measurement, so paths can reinforce or cancel."),
    "M08": ("Probability misconception", "Probabilities are the squared magnitudes of amplitudes and must add to one."),
    "M09": ("State-vector misconception", "A state vector represents amplitudes for all computational basis states, not a list of observed outcomes."),
    "M10": ("Algorithm-step misconception", "Quantum algorithms require their steps in a precise sequence; verify the purpose of each gate."),
}

CHALLENGES = [
    {"id": "bell", "title": "Create a Bell state", "description": "Put q0 into superposition, then entangle q1 with it.", "expected": {"00": .5, "11": .5}, "hint": "Start with H on q0. Then use CX with q0 as control and q1 as target."},
    {"id": "ghz", "title": "Create a GHZ state", "description": "Entangle all three qubits into an equal |000⟩ / |111⟩ state.", "expected": {"000": .5, "111": .5}, "hint": "Apply H to q0, then use q0 as the control for CX gates targeting q1 and q2."},
    {"id": "plus", "title": "Build |+⟩", "description": "Create an equal superposition on q0.", "expected": {"0": .5, "1": .5}, "hint": "The Hadamard gate maps |0⟩ to |+⟩."},
    {"id": "flip", "title": "Flip a qubit", "description": "Transform q0 from |0⟩ to |1⟩.", "expected": {"1": 1}, "hint": "Which gate exchanges |0⟩ and |1⟩?"},
]

def load_profile():
    if DATA.exists():
        try: return json.loads(DATA.read_text())
        except (json.JSONDecodeError, OSError): pass
    return DEFAULT_PROFILE.copy()

def save_profile(profile):
    DATA.write_text(json.dumps(profile, indent=2))

def apply_single(state, gate, target, n):
    inv = 1 / math.sqrt(2)
    matrices = {
        "H": ((inv, inv), (inv, -inv)), "X": ((0, 1), (1, 0)),
        "Y": ((0, -1j), (1j, 0)), "Z": ((1, 0), (0, -1)),
        "S": ((1, 0), (0, 1j)), "T": ((1, 0), (0, cmath.exp(1j * math.pi / 4))),
    }
    m = matrices[gate]
    bit = 1 << (n - 1 - target)
    out = state[:]
    for i in range(1 << n):
        if not i & bit:
            j = i | bit
            out[i] = m[0][0] * state[i] + m[0][1] * state[j]
            out[j] = m[1][0] * state[i] + m[1][1] * state[j]
    return out

def simulate(circuit, qubits=2):
    qubits = max(1, min(int(qubits), 3))
    state = [0j] * (1 << qubits); state[0] = 1 + 0j
    for op in circuit:
        gate, target = op.get("gate"), int(op.get("target", 0))
        if target < 0 or target >= qubits: raise ValueError("Gate target is outside the circuit.")
        if gate in {"H", "X", "Y", "Z", "S", "T"}:
            state = apply_single(state, gate, target, qubits)
        elif gate == "CX":
            control = int(op.get("control", 0))
            if control == target or control < 0 or control >= qubits: raise ValueError("CX needs two different valid qubits.")
            cbit, tbit = 1 << (qubits-1-control), 1 << (qubits-1-target)
            out = state[:]
            for i in range(1 << qubits):
                if i & cbit and not i & tbit: out[i | tbit], out[i] = state[i], state[i | tbit]
            state = out
        else: raise ValueError(f"Unsupported gate: {gate}")
    probabilities = {format(i, f"0{qubits}b"): round(abs(a) ** 2, 6) for i, a in enumerate(state) if abs(a) ** 2 > 1e-8}
    amplitudes = {format(i, f"0{qubits}b"): {"re": round(a.real, 4), "im": round(a.imag, 4)} for i, a in enumerate(state) if abs(a) > 1e-8}
    return {"probabilities": probabilities, "amplitudes": amplitudes, "qubits": qubits}

def analyse(circuit, result, expected=None, challenge_id=None):
    issues = []
    cx = [g for g in circuit if g.get("gate") == "CX"]
    if challenge_id == "bell" and cx:
        last = cx[-1]
        if last.get("control") == 1 and last.get("target") == 0:
            issues.append(("M06", .87))
    if challenge_id == "bell" and not cx:
        issues.append(("M02", .72))
    if circuit and circuit[-1].get("gate") == "H" and any(g.get("gate") == "Z" for g in circuit):
        issues.append(("M05", .68))
    if expected:
        max_error = max(abs(result["probabilities"].get(k, 0) - v) for k, v in expected.items())
        extras = sum(v for k, v in result["probabilities"].items() if k not in expected)
        correct = max_error < .02 and extras < .02
    else: correct = False
    if not issues and not correct and challenge_id == "bell": issues.append(("M06", .61))
    return correct, issues

def tutor_response(profile, issues, correct, challenge):
    if correct:
        return {"tone": "success", "headline": "Excellent — your circuit matches the target.", "body": "You created the intended quantum state. I’ve increased your mastery for this concept; try the next challenge when you’re ready.", "misconceptions": []}
    if issues:
        cards = [{"id": code, "label": TAXONOMY[code][0], "confidence": confidence, "explanation": TAXONOMY[code][1]} for code, confidence in issues]
        return {"tone": "hint", "headline": "I found a likely conceptual mix-up.", "body": f"For this challenge, {challenge['hint']} Try changing one operation and run it again.", "misconceptions": cards}
    return {"tone": "hint", "headline": "Your state is valid, but it does not yet match the target.", "body": challenge["hint"], "misconceptions": []}

class App(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT / "static"), **kwargs)
    def send_json(self, payload, status=200):
        raw = json.dumps(payload).encode(); self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/profile": return self.send_json(load_profile())
        if path == "/api/challenges": return self.send_json(CHALLENGES)
        if path == "/api/analytics":
            p = load_profile(); weakest = sorted(p["mastery"].items(), key=lambda x: x[1])[:3]
            return self.send_json({"activeLearners": 24, "completedToday": 38, "averageMastery": round(sum(p["mastery"].values()) / len(p["mastery"])), "needsAttention": weakest, "taxonomy": TAXONOMY})
        return super().do_GET()
    def do_POST(self):
        if urlparse(self.path).path != "/api/simulate": return self.send_json({"error": "Not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(length) or b"{}")
            challenge = next((c for c in CHALLENGES if c["id"] == body.get("challengeId")), CHALLENGES[0])
            result = simulate(body.get("circuit", []), body.get("qubits", 2))
            expected = challenge["expected"]
            # Challenges with one qubit should compare against the low-order bit of the simulator result.
            if len(next(iter(expected))) == 1:
                # q0 is the most-significant displayed qubit, so a one-qubit target
                # must be padded on the right when comparing a multi-qubit circuit.
                expected = {k.ljust(result["qubits"], "0"): v for k, v in expected.items()}
            correct, issues = analyse(body.get("circuit", []), result, expected, challenge["id"])
            profile = load_profile(); profile["attempts"] += 1
            if correct:
                subject = "Entanglement" if challenge["id"] == "bell" else "Superposition"
                profile["mastery"][subject] = min(100, profile["mastery"].get(subject, 50) + 4)
            for code, _ in issues: profile["misconceptions"][code] = profile["misconceptions"].get(code, 0) + 1
            save_profile(profile)
            return self.send_json({"simulation": result, "correct": correct, "feedback": tutor_response(profile, issues, correct, challenge), "profile": profile})
        except (ValueError, KeyError, json.JSONDecodeError) as e: return self.send_json({"error": str(e)}, 400)

if __name__ == "__main__":
    host = os.environ.get("QPATH_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Q-PATH AI running at http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), App).serve_forever()
