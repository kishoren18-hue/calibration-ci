"""Reliability diagram as a standalone SVG (standard library only)."""

from __future__ import annotations

from typing import Sequence


def _bins(y: Sequence[int], p: Sequence[float], n_bins: int):
    acc = [[0.0, 0.0, 0] for _ in range(n_bins)]
    for yi, pi in zip(y, p):
        b = min(int(pi * n_bins), n_bins - 1)
        acc[b][0] += pi
        acc[b][1] += yi
        acc[b][2] += 1
    return [(s[0] / s[2], s[1] / s[2], s[2]) for s in acc if s[2]]


def reliability_svg(runs: dict[str, tuple[Sequence[int], Sequence[float]]], n_bins: int = 10,
                    title: str = "Reliability diagram") -> str:
    """runs: {label: (correct, confidence)}. Returns SVG markup.

    Dot area is proportional to the number of items in the bin; the dashed
    diagonal is perfect calibration.
    """
    W, H, L, R, T, B = 520, 420, 56, 150, 36, 48
    pw, ph = W - L - R, H - T - B
    x = lambda v: L + v * pw  # noqa: E731
    y = lambda v: T + (1 - v) * ph  # noqa: E731
    colors = ["#5b6b7f", "#d9822b", "#2a9d8f", "#c0397a"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,sans-serif" '
             f'font-size="12">', f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
             f'<text x="{L}" y="22" font-size="14" font-weight="600" fill="#1c2230">{title}</text>']
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        parts.append(f'<line x1="{x(0)}" x2="{x(1)}" y1="{y(t)}" y2="{y(t)}" stroke="#e4e7ec"/>')
        parts.append(f'<text x="{L - 8}" y="{y(t) + 4}" text-anchor="end" fill="#5d6678">{t:.2f}</text>')
        parts.append(f'<text x="{x(t)}" y="{H - B + 18}" text-anchor="middle" fill="#5d6678">{t:.2f}</text>')
    parts.append(f'<line x1="{x(0)}" y1="{y(0)}" x2="{x(1)}" y2="{y(1)}" stroke="#9aa3b2" stroke-dasharray="4 4"/>')
    parts.append(f'<text x="{L + pw / 2}" y="{H - 10}" text-anchor="middle" fill="#5d6678">confidence</text>')
    parts.append(f'<text transform="translate(16 {T + ph / 2}) rotate(-90)" text-anchor="middle" '
                 f'fill="#5d6678">accuracy</text>')
    total = max(1, max(len(v[0]) for v in runs.values()))
    for i, (label, (yy, pp)) in enumerate(runs.items()):
        c = colors[i % len(colors)]
        pts = _bins(yy, pp, n_bins)
        if len(pts) > 1:
            path = " ".join(f"{x(a):.1f},{y(b):.1f}" for a, b, _ in pts)
            parts.append(f'<polyline points="{path}" fill="none" stroke="{c}" stroke-width="2"/>')
        for a, b, n in pts:
            r = 3 + 10 * (n / total) ** 0.5
            parts.append(f'<circle cx="{x(a):.1f}" cy="{y(b):.1f}" r="{r:.1f}" fill="{c}" fill-opacity="0.8">'
                         f'<title>{label}: conf {a:.2f}, acc {b:.2f}, n={n}</title></circle>')
        ly = T + 16 + 22 * i
        parts.append(f'<rect x="{W - R + 16}" y="{ly - 9}" width="12" height="12" rx="2" fill="{c}"/>')
        parts.append(f'<text x="{W - R + 34}" y="{ly + 1}" fill="#1c2230">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)
