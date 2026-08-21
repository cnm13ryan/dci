"""The pairwise-matrix screen: every registered §8.1 cell, at screen scale.

Check C12 records the A-versus-reference correlation as **BLOCKED** and names
what would settle it: "a v4 calibration or confirmatory stage carrying two
composed cells with the same outcome constraint on the same blocks". The FORM x
STEM screen report says the same thing from the other side -- "This screen
carries no composed reference cells and does not supply it."

Neither does any other artifact in the repository. The B+R pilot has three
composed cells and no reference-on-reference cell; v3's composed arms all carry
A as the outcome; the two design screens are solo-only. So four quantities that
decide the scientific question have never been measured in this constraint
vocabulary at all:

    Delta_R = D(B<-A) - mean_j D(B<-R_j)                      (registered primary)
    Xi      = Delta_R - [D(Rbar<-A) - D(Rbar<-Rbar')]         (registered secondary)
    D(R_j<-A), D(R_j<-B)                                      (registered secondary)
    the empirical companion-difficulty -> D(B<-companion) relation  (decision V5)

This screen runs the whole registered §8.1 matrix -- five constraints, five
solo cells, ten unordered pairs in both orders -- so all four become estimable
before freeze, on topics disjoint from the ones that selected the references.

**It is a screen, not the confirmatory experiment.** It runs on 48 blocks, not
384, so it cannot meet the registered §17.3 precision preconditions and cannot
license an L3 statement. It exists to show whether the design identifies what
it claims to identify, and to supply the two planning quantities the allocation
decision has been waiting on.
"""
STUDY_ID = "dci1-matrix-screen-v4"
CLASSIFICATION = "NON-CONFIRMATORY DESIGN SCREEN"

__all__ = ["STUDY_ID", "CLASSIFICATION"]
