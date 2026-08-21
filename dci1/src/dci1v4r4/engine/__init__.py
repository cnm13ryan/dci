"""v4r3's execution context and its root of trust.

Signing, hashing, atomic writes and durable replication are protocol-neutral
and are carried from ``dci1v4.engine`` unchanged. What is v4r3's is *where*
things go and *what may never overlap what*, which is exactly what a study
boundary is.
"""
