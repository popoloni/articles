# Mathematical Model — AI Loop Economics

## 1. Context accumulation

For `N` turns, static context `S`, average new history `T`, and average output `o_bar`:

**Full replay**

```
I_full(N) = N*S + N*(N-1)/2*T
O(N)      = N*o_bar
```

**Compaction or fresh external state**

```
I_bounded(N) = N*(S + R)
```

where `R` is retained compacted context or reconstructed external state.

**Model cost**

```
C_model(N) = p_input*I(N) + p_output*O(N)
```

Prices are expressed per token in the equation and converted from provider prices per million tokens in the code.

## 2. Complete candidate ledger

```
C_candidate =
    C_model
  + C_tools
  + C_environment
  + C_verification
  + C_review
  + C_coordination
  + C_rework
  + C_risk
```

`C_risk` is expected loss rather than maximum possible loss.

## 3. Cost per accepted outcome

For independent acceptance probability `P_a`:

```
C_accepted = C_candidate / P_a
```

For a homogeneous observed cohort:

```
C_accepted_hat = total cohort candidate cost / independently accepted outcomes
```

The cohort estimator should be reported with sample size, acceptance rate, mean, median, p90, review time, and escaped defects.

## 4. Evidence-changing retry and escalation policy

For stage `k`:

- `a_k`: automatic incremental attempt and gate cost
- `p_k`: conditional success probability after all previous stages failed
- `s_k`: additional review and residual-risk cost if the stage succeeds
- `C_H`: human completion cost after machine stages are exhausted

```
E[C_K] =
  sum_k survival(k-1) * (a_k + p_k*s_k)
  + survival(K) * C_H

survival(k) = product_j<=k (1 - p_j)
```

A new stage is attractive only when its expected stage cost plus residual human cost is below immediate escalation. Correlated retries must receive a low conditional success probability.

## 5. Local total cost and break-even

**Monthly fixed local cost**

```
C_local_fixed = (hardware_price - residual_value)/economic_life_months
                + maintenance_monthly
```

**Local infrastructure cost per accepted outcome at monthly volume `V`**

```
C_local_infra_accepted(V) =
    (C_local_fixed + V*r_local) / (V*P_a_local)
```

For a cloud model with variable candidate model cost `r_cloud` and acceptance `P_a_cloud`, the acceptance-adjusted infrastructure break-even is obtained from:

```
(C_local_fixed + V*r_local)/(V*P_a_local)
    = r_cloud/P_a_cloud
```

which gives:

```
V_BE = C_local_fixed /
       (P_a_local*(r_cloud/P_a_cloud) - r_local)
```

This is not a complete route break-even until review, rework, risk, and operations are included.

## 6. Organizational throughput

For stage capacities expressed in the same accepted-change unit:

```
Y ≈ min(C_spec, C_generation, C_verification,
        C_integration, C_release, C_operations)
```

The equation identifies the constraint but does not model queue variance. Practical systems require headroom at the constrained stage.

## 7. Verification leverage

```
L_v = (rework reduction + expected failure-cost reduction)
      / full verifier cost
```

`L_v > 1` indicates positive direct economic leverage before counting auditability, learning, and trust.

## 8. Uncertainty model

The Python implementation uses:

- Beta posteriors for stage acceptance probabilities from illustrative pilot counts;
- lognormal uncertainty around attempt, review, residual-risk, and human-escalation costs;
- 100,000 Monte Carlo draws with a fixed seed.

The result is a distribution rather than a falsely precise point estimate.

## 9. Scenario results

The regulated-maintenance scenario produces:

```
Human only                         $720.00
One local attempt, then human      $184.70
Two local attempts, then human     $123.84
Local-local-Opus cascade            $62.53
Cascade plus blind fourth retry     $65.25
```

The blind retry is rejected because its high incremental cost and low changed success probability raise expected cost.
