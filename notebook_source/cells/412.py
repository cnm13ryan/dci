target_all = confirmatory_scores.query(
    "constraint_id == @CFG.target_id and is_measured")
print("EXPLORATORY. Descriptive only.\n")
display(target_all.groupby(["added_constraint", "order"])
        .agg(fail_rate=("fail", "mean"), mean_words=("response_words", "mean"),
             n=("fail", "size")).round(3))

_probe = pd.DataFrame({
    "reference": SELECTED_REFERENCES,
    "difficulty": [float(SIGNATURE.at[c, SIG_DIFFICULTY]) for c in SELECTED_REFERENCES],
    "wording_instability_max": [float(SIGNATURE_FULL.at[c, SIG_S_MAX])
                                for c in SELECTED_REFERENCES],
    "mahalanobis": [float(MATCH_DISTANCE[c]) for c in SELECTED_REFERENCES],
}).set_index("reference")
for o in CFG.orders:
    _probe[f"tau_{o}"] = [float(PRIMARY.loc[f"tau|{c}|{o}", "estimate"])
                          for c in SELECTED_REFERENCES]
display(_probe.round(3))
print("\nWith six references a correlation here has almost no power. It is "
      "recorded to motivate the next preregistration, not to support a claim.")

_lengths = (calibration_scores.query("order == 'isolated' and is_measured")
            .groupby("constraint_id")["response_words"].mean())
print(f"\nMediator watch: mean isolated response length, focal "
      f"{_lengths.get(CFG.focal_id, float('nan')):.1f} words versus panel mean "
      f"{_lengths.reindex(SELECTED_REFERENCES).mean():.1f}. This imbalance was "
      "accepted by the causal-variable audit and is reported, not corrected.")
