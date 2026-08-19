## **Guidelines for a Good Discussion Section**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Discussion section interprets the paper's results honestly, clearly, and usefully.

**Core function.** The Discussion section explains what the evidence supports, what remains unresolved, and what readers should take away. It translates technical findings into implications, identifies limitations and assumptions, points to future work, and calibrates confidence so the conclusions match the strength of the evidence.

## Canonical Structure

1. **Limitations:** State what the evidence does not establish. Cover scope, tested models and datasets, methodological caveats, missing ablations, unavailable baselines, threats to validity, post-hoc analyses, possible cherry-picking, alternative explanations, and technical assumptions. Address the objections a careful reader would raise.
2. **Implications:** Explain what practitioners, theorists, or future researchers should take from the work. Match the recommendation strength to the evidence strength: preliminary findings suggest further investigation; strong evidence can justify broader adoption or revision of practice.
3. **Future Work:** Identify concrete next steps that would extend, strengthen, or stress-test the claims. Focus on specific experiments, analyses, or theoretical directions.
4. **Reflections and Tacit Knowledge:** Share useful lessons that fall outside the formal results — surprising findings, replication tips, common misconceptions, fragile details, or provisional intuitions. These can also live in an appendix or companion note.

## Optional Element

A brief framing paragraph at the start can re-orient readers to the main claims before interpreting them. Skip this when it would duplicate the Introduction.

## Quality Criteria

* **Make limitations specific.** State exactly where the evidence may fail: models, datasets, languages, scales, regimes, assumptions, missing controls, or untested settings.
* **Surface weaknesses proactively.** Name the objections a careful reader would raise, then address them.
* **Calibrate confidence.** Match the strength of implications to the strength of evidence using consistent language: preliminary, suggestive, compelling, definitive.
* **Stay within the bounds of the experiments.** Keep conclusions inside what the design and analysis establish.
* **Address alternative explanations.** Identify plausible competing interpretations and explain the preferred reading. Acknowledge when multiple explanations remain viable.
* **Make implications concrete.** Specify the practitioner action, theoretical update, design choice, or belief revision the results support.
* **Motivate future work.** For each direction, explain what it would test, strengthen, extend, or clarify.
* **Tie discussion to the paper's claims.** Reflect on the claims from the Abstract and Introduction.
* **Share useful tacit knowledge.** Include practical lessons, replication challenges, surprising difficulties, and misconceptions that would help future researchers.
* **Add new value beyond the Introduction.** Use the Discussion to clarify boundaries, implications, and open questions.
* **Use a Conclusion only when needed.** Add a separate Conclusion only when it provides a final synthesis the Introduction and Discussion lack.
