# Runtime-v18.1 training-entrypoint import correction

Registered after v18 smoke attempt001 failed and before attempt002.

Attempt001 initialized the Isaac application but failed before environment
construction because `train_residual_ppo.py` referenced `math.exp` without
importing `math`. It produced no simulation, rollout, update, or performance
result.

The only source change is `import math`. One AST regression test was added
to ensure the training entrypoint imports `math` whenever it contains
attribute loads rooted at that module. The v18 configuration, confidence
threshold, projection, all simulation and learning parameters, and all
pre-registered decision gates are unchanged.

- corrected `train_residual_ppo.py` SHA-256:
  `cab8f29d87c7745f352884bff2ef3d6ac6b4f451b6d6ed445288f099e0bc0c19`
- updated `test_training_entrypoint.py` SHA-256:
  `e37aab3915c155185666fd5b14d7b2f1a297886b91d542c89af3552df92a383a`
- unchanged common-config raw SHA-256:
  `3c6b744266f48155348f9fe8df36ce254221ee9b873abee5b6b3980194e2fcc5`
- unchanged canonical common-config SHA-256:
  `ba0b27c4fc565d9ba42167c214fec8002049d90deb03cb5099e16ccc788d475b`

Python compilation and all 138 tests passed before attempt002.
