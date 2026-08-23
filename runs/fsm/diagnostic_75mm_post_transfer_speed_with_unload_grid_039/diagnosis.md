# Diagnostic 75 mm combined speed/load grid 039

## Immutable result

- The exact environment process (`PID 130396`) exited naturally.
- Scenario: `development-h075-0000`
- Candidates: 25 (five post-transfer speeds, five Latin replicates)
- Strict success: **3/25**
- Other outcomes: **22/25 global timeouts**
- Result SHA-256:
  `2dcfc4c469ab359e7a2db2a9251d850c034b9c228e69fc668478e87deb64581e`

Every candidate retained 0/0/0/0 analytic-IK fallback and zero clamp. Each
successful candidate reached only the configured 2 mm front-left/rear-right
shortening.

| Post-transfer speed | Success | Eligible samples | Mean diagnostic dwell |
| ---: | ---: | ---: | ---: |
| 0.0000 rad/s | 0/5 | 415 | 0.6600 s |
| 0.0375 rad/s | 0/5 | 475 | 0.6100 s |
| 0.0750 rad/s | **1/5** | 857 | **1.0067 s** |
| 0.1125 rad/s | **1/5** | 1,705 | 0.6233 s |
| 0.1500 rad/s | **1/5** | 2,108 | 0.6767 s |

The three strict successes terminated at 149.767/149.917/149.783 s for
0.075/0.1125/0.15 rad/s. Their terminal upward forces were respectively
8.531/5.212/5.599/8.962 N,
6.568/7.253/7.539/7.205 N, and
7.725/6.347/6.916/7.608 N. All had zero non-wheel contact.

## Decision

Select 0.075 rad/s for a 25-environment exact-candidate repeat because it has
the highest group mean dwell and four of five replicates reached at least
0.833 s, including one strict success. Keep the 2 mm / 0.75 mm/s load
controller, phase-7/8 front/rear speeds 0/+0.3 rad/s, phase-9/0.4 support
geometry, and all strict metrics unchanged. No formal configuration is
changed until this repeat establishes the candidate's actual success rate.
