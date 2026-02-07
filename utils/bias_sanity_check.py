import json


def _to_float(x, default=None):
    try:
        if x is None:
            return default
        s = str(x).strip()
        if not s or s.lower() == "nan":
            return default
        return float(s.replace("%", ""))
    except Exception:
        return default


def parse_oo_points(optic_odds):
    pts = []
    for book, entries in (optic_odds or {}).items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            try:
                prob_str = str(entry.get("probability", "0")).replace("%", "").strip()
                if not prob_str or prob_str.lower() == "nan":
                    continue
                prob = float(prob_str)

                raw = str(entry.get("spread", ""))
                rs = raw.lower()
                clean = rs.replace("o", "").replace("u", "")
                if not clean:
                    continue
                line = float(clean)

                idx = entry.get("outcome_index")
                outcome = None
                if "o" in rs or idx == 0:
                    outcome = "OVER"
                elif "u" in rs or idx == 1:
                    outcome = "UNDER"

                if outcome:
                    pts.append({"line": line, "outcome": outcome, "prob": prob, "book": book})
            except Exception:
                continue
    return pts


def debug_total_line(game, target_line=155.5, line_epsilon=0.01):
    market = (game.get("markets") or {}).get("total") or {}
    hos_data = market.get("hos") or []
    oo_points = parse_oo_points((market.get("optic_odds") or {}))

    print("matchup", game.get("game_matchup"))
    print("target_total_line", target_line)

    # HOS
    hos_matches = []
    for hos_line in hos_data:
        h_line = _to_float(hos_line.get("line"), default=None)
        if h_line is None:
            continue
        if abs(h_line - float(target_line)) < line_epsilon:
            for sel in hos_line.get("selections") or []:
                outcome = sel.get("outcome")
                if outcome not in ("OVER", "UNDER"):
                    continue
                prob = _to_float(sel.get("prob"), default=0.0) or 0.0
                bias = _to_float(sel.get("bias"), default=0.0) or 0.0
                # In this dataset prob/bias appear to be decimals (0-1)
                # Unbiased decimal = prob - bias
                hos_matches.append(
                    {
                        "line": h_line,
                        "outcome": outcome,
                        "prob": prob,
                        "bias": bias,
                        "unbiased": prob - bias,
                    }
                )

    if not hos_matches:
        print("HOS", "no selections at target line")
    else:
        for h in hos_matches:
            print(
                "HOS",
                "line",
                h["line"],
                "outcome",
                h["outcome"],
                "prob_dec",
                h["prob"],
                "prob_pct",
                h["prob"] * 100.0,
                "bias_dec",
                h["bias"],
                "unbiased_pct",
                h["unbiased"] * 100.0,
            )

    # Optic
    oo_matches = [
        oo
        for oo in oo_points
        if abs(float(oo.get("line", 0.0)) - float(target_line)) < line_epsilon
        and oo.get("outcome") in ("OVER", "UNDER")
    ]
    if not oo_matches:
        print("OPTIC", "no entries at target line")
    else:
        for oo in sorted(oo_matches, key=lambda x: (x.get("outcome"), x.get("book"))):
            print(
                "OPTIC",
                "line",
                oo["line"],
                "outcome",
                oo["outcome"],
                "prob_pct",
                oo["prob"],
                "book",
                oo["book"],
            )

        # Averages by outcome
        for outcome in ("OVER", "UNDER"):
            vals = [float(oo["prob"]) for oo in oo_matches if oo.get("outcome") == outcome]
            if not vals:
                continue
            mean_val = sum(vals) / len(vals)
            print(
                "OPTIC_AVG",
                "outcome",
                outcome,
                "mean_prob_pct",
                mean_val,
                "n",
                len(vals),
                "min",
                min(vals),
                "max",
                max(vals),
            )

    # Direct diffs (Optic % vs HOS unbiased %)
    if hos_matches and oo_matches:
        hos_by_outcome = {h["outcome"]: h for h in hos_matches}
        print("DIFFS", "optic_prob_pct_minus_hos_unbiased_pct")
        for oo in sorted(oo_matches, key=lambda x: (x.get("outcome"), x.get("book"))):
            h = hos_by_outcome.get(oo.get("outcome"))
            if not h:
                continue
            diff_pp = float(oo["prob"]) - (h["unbiased"] * 100.0)
            print(
                "DIFF",
                oo["outcome"],
                "book",
                oo["book"],
                "optic_pct",
                oo["prob"],
                "hos_unbiased_pct",
                h["unbiased"] * 100.0,
                "diff_pp",
                diff_pp,
            )


def compute_optimal_bias_pp(game):
    market = (game.get("markets") or {}).get("total") or {}
    oo_points = parse_oo_points(market.get("optic_odds") or {})
    hos_data = market.get("hos") or []

    targets = []
    for hos_line in hos_data:
        h_line = hos_line.get("line")
        if h_line is None:
            continue

        for sel in hos_line.get("selections") or []:
            outcome = sel.get("outcome")
            if outcome not in ("OVER", "UNDER"):
                continue

            prob = float(sel.get("prob") or 0.0)
            bias = float(sel.get("bias") or 0.0)

            # Unbiased baseline
            h_unbiased = (prob - bias) * 100.0

            for oo in oo_points:
                if abs(float(h_line) - oo["line"]) < 0.01 and oo["outcome"] == outcome:
                    diff = oo["prob"] - h_unbiased
                    targets.append(diff if outcome == "OVER" else -diff)

    if not targets:
        return None

    mean_pp = sum(targets) / len(targets)
    return mean_pp, len(targets)


def main():
    with open("consolidated_odds_all_books.json", "r") as f:
        data = json.load(f)

    game = next((g for g in data if g.get("game_matchup") == "Marquette vs St. John's"), None)
    print("found_game", bool(game))
    if not game:
        return

    res = compute_optimal_bias_pp(game)
    print("optimal_bias_pp_n", res)

    # Focused sanity check for the exact line discussed
    print("\n--- 155.5 sanity check ---")
    debug_total_line(game, target_line=155.5)

    market = game["markets"]["total"]
    hos = market.get("hos") or []
    if hos:
        print("HOS_total_line", hos[0].get("line"))
        for s in hos[0].get("selections") or []:
            if s.get("outcome") in ("OVER", "UNDER"):
                prob = float(s.get("prob") or 0.0)
                bias = float(s.get("bias") or 0.0)
                print(
                    "HOS_sel",
                    s.get("outcome"),
                    "prob",
                    prob,
                    "bias",
                    bias,
                    "unbiased_prob",
                    prob - bias,
                )

    if res:
        pp, n = res
        dec = pp / 100.0
        print("optimal_bias_decimal", dec)
        print("optimal_bias_percent", dec * 100.0)


if __name__ == "__main__":
    main()
