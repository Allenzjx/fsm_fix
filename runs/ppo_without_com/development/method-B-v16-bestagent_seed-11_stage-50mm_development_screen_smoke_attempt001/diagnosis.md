# Method-B v16 best-agent development screen smoke attempt001

`EXECUTION_PASS`, `RESTORE_PASS`, `DETERMINISTIC_POLICY_DUPLICATE`.

- Checkpoint file SHA-256:
  `47666f48aa45db334b9050c88be407f667453f3d2ea9bc9b9ecebbcb0e91e0ea`.
- All `100 x 122` telemetry values are finite. Policy maximum is
  `0.1524941`; phases 0/1 execute exact zero residual.
- The telemetry SHA-256
  `ffda9ab6ae885a5316c6f62ff0205210b4cf3ec66525b647e2b058b2b689f24d`
  is byte-identical to the explicit `final_agent.pt` smoke.
- A direct tensor audit proves that all 9 policy tensors (125,080 elements)
  and all observation-preprocessor tensors are exactly equal to
  `final_agent.pt`. Value and preprocessor tensors are also equal; only
  serialized non-controller optimizer state makes the checkpoint file hash
  differ.

Because deterministic evaluation uses the equal policy and equal observation
preprocessor under the same frozen runtime, a full run is mathematically the
same controller already evaluated at 8/20. It is recorded as an equivalent
duplicate, not silently discarded and not counted as a new independent
result.

Artifact SHA-256: result
`1f10531a6af22d344362535b7f6072d61ac82f9fc0d52de07647a34057b4cbbd`,
episodes
`3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`,
status
`303cf29b719398e33e2d40395fb4141a6167b1f6487dd11cb341c297313598db`,
telemetry
`ffda9ab6ae885a5316c6f62ff0205210b4cf3ec66525b647e2b058b2b689f24d`,
stdout
`70c6d0f7e3ef77cb7913fece899134d2c0e88fc1476af16e023e9fb28198b794`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: proceed to the final pre-registered distinct policy, checkpoint 57600.
