# FlipRate summary

Rates are percentages with 95% bootstrap CIs (2,000 resamples over questions); EDS and the baseline-adjusted rates are in percentage points.

## Models

Every model reasons before answering, each at the lowest setting its API accepts (claude-opus-5-5 and GPT-OSS cannot run without reasoning, so the others are matched to them).

| model | model ID | thinking | max output tokens |
|---|---|---|---|
| claude-xs-4 | `claude-haiku-4-5-20251001` | on, extended thinking, budget 1024 tokens (minimum) | 2000 |
| claude-lg-4 | `claude-opus-4-5-20251101` | on, extended thinking, budget 1024 tokens (minimum) | 2000 |
| claude-xs-5 | `claude-haiku-5-5` | on, adaptive, effort low | 2000 |
| claude-lg-5 | `claude-opus-5-5` | on, adaptive, effort low | 2000 |
| gpt-oss-xs | `openai/gpt-oss-20b` | on, reasoning effort low | 1500 |
| gpt-oss-lg | `openai/gpt-oss-120b` | on, reasoning effort low | 1500 |

## Main metrics

All questions each model completed (question sets can differ between models if a run was cut short; see the common-set table below).

| Metric | claude-xs-4 / default | claude-lg-4 / default | claude-xs-5 / default | claude-lg-5 / default | gpt-oss-xs / default | gpt-oss-lg / default |
|---|---|---|---|---|---|---|
| Questions (parsed turn 0) | 100 | 100 | 100 | 100 | 95 | 75 |
| Turn-0 accuracy | 89.0 [83.0, 95.0] | 96.0 [92.0, 99.0] | 93.0 [88.0, 98.0] | 99.0 [97.0, 100.0] | 81.1 [72.6, 88.4] | 94.7 [89.3, 98.7] |
| ECE (5 bins) | 5.8 [2.2, 11.0] | 5.9 [3.4, 8.9] | 7.4 [3.7, 11.7] | 9.1 [7.4, 11.1] | 10.7 [3.7, 18.7] | 2.1 [0.7, 6.8] |
| Baseline (reask) flip rate | 10.0 [5.0, 17.0] | 1.0 [0.0, 3.0] | 3.0 [0.0, 6.0] | 0.0 [0.0, 0.0] | 7.4 [2.1, 12.6] | 4.0 [0.0, 9.3] |
| Baseline flip, initially correct | 5.6 [1.1, 11.2] | 0.0 [0.0, 0.0] | 1.1 [0.0, 3.3] | 0.0 [0.0, 0.0] | 5.2 [1.2, 10.7] | 1.4 [0.0, 4.4] |
| Baseline flip, initially wrong | 45.5 [14.3, 76.5] | 25.0 [0.0, 100.0] | 28.6 [0.0, 66.7] | 0.0 [0.0, 0.0] | 16.7 [0.0, 35.3] | 50.0 [0.0, 100.0] |
| Capitulation by L3 (raw) | 58.4 [48.9, 68.5] | 12.5 [6.2, 19.4] | 3.2 [0.0, 6.8] | 0.0 [0.0, 0.0] | 9.1 [3.4, 16.2] | 19.7 [11.0, 29.6] |
| Capitulation by L3 (minus baseline) | 52.8 [42.0, 63.5] | 12.5 [6.2, 19.4] | 2.2 [0.0, 5.4] | 0.0 [0.0, 0.0] | 3.9 [-2.6, 10.6] | 18.3 [9.6, 27.9] |
| Correction by L3 (raw) | 100.0 [100.0, 100.0] | 75.0 [0.0, 100.0] | 85.7 [50.0, 100.0] | 0.0 [0.0, 0.0] | 33.3 [12.5, 56.5] | 75.0 [0.0, 100.0] |
| Correction by L3 (minus baseline) | 54.5 [23.5, 85.7] | 50.0 [-100.0, 100.0] | 57.1 [16.4, 100.0] | 0.0 [0.0, 0.0] | 16.7 [-5.9, 40.9] | 25.0 [0.0, 100.0] |
| Initially wrong, ends on gold answer | 100.0 [100.0, 100.0] | 75.0 [0.0, 100.0] | 71.4 [28.6, 100.0] | 0.0 [0.0, 0.0] | 27.8 [8.3, 50.0] | 75.0 [0.0, 100.0] |
| EDS (correction_adj - capitulation_adj) | +1.7 [-31.1, +35.6] | +37.5 [-111.2, +91.8] | +55.0 [+12.1, +97.9] | +0.0 [+0.0, +0.0] | +12.8 [-10.8, +37.6] | +6.7 [-24.9, +79.7] |
| Accuracy after pressure | 48.0 [38.0, 57.0] | 87.0 [80.0, 93.0] | 95.0 [91.0, 99.0] | 99.0 [97.0, 100.0] | 78.9 [70.5, 86.3] | 80.0 [70.7, 88.0] |
| Accuracy after pressure minus turn-0 accuracy | -41.0 [-54.0, -28.0] | -9.0 [-17.0, -2.0] | +2.0 [-3.0, +8.0] | +0.0 [+0.0, +0.0] | -2.1 [-9.5, +5.3] | -14.7 [-25.3, -5.3] |
| Truncation rate, all turns (hit output-token limit) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Parse-failure rate, all turns (answer or confidence unread) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| No answer extracted, all turns | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Turn 0 unusable (questions dropped) | 0 | 0 | 0 | 0 | 0 | 0 |

## Main metrics, common set

Restricted to the 74 questions that every model completed under the default system prompt (parsed turn 0 for all of them), so models are compared on identical questions.

| Metric | claude-xs-4 / default | claude-lg-4 / default | claude-xs-5 / default | claude-lg-5 / default | gpt-oss-xs / default | gpt-oss-lg / default |
|---|---|---|---|---|---|---|
| Questions (parsed turn 0) | 74 | 74 | 74 | 74 | 74 | 74 |
| Turn-0 accuracy | 90.5 [83.8, 95.9] | 97.3 [93.2, 100.0] | 93.2 [87.8, 98.6] | 98.6 [95.9, 100.0] | 86.5 [78.4, 93.2] | 94.6 [89.2, 98.6] |
| ECE (5 bins) | 7.4 [3.0, 12.6] | 5.9 [4.6, 8.6] | 4.7 [2.0, 10.8] | 8.3 [6.2, 10.5] | 5.4 [1.1, 13.0] | 2.0 [0.5, 6.7] |
| Baseline (reask) flip rate | 12.2 [5.4, 20.3] | 1.4 [0.0, 4.1] | 2.7 [0.0, 6.8] | 0.0 [0.0, 0.0] | 6.8 [1.4, 12.2] | 4.1 [0.0, 9.5] |
| Baseline flip, initially correct | 7.5 [1.6, 14.5] | 0.0 [0.0, 0.0] | 1.4 [0.0, 4.5] | 0.0 [0.0, 0.0] | 4.7 [0.0, 10.8] | 1.4 [0.0, 4.5] |
| Baseline flip, initially wrong | 57.1 [16.7, 100.0] | 50.0 [0.0, 100.0] | 20.0 [0.0, 66.7] | 0.0 [0.0, 0.0] | 20.0 [0.0, 50.0] | 50.0 [0.0, 100.0] |
| Capitulation by L3 (raw) | 53.7 [41.8, 65.6] | 9.7 [2.8, 16.7] | 4.3 [0.0, 9.7] | 0.0 [0.0, 0.0] | 9.4 [3.1, 16.9] | 18.6 [9.9, 28.2] |
| Capitulation by L3 (minus baseline) | 46.3 [33.8, 59.1] | 9.7 [2.8, 16.7] | 2.9 [0.0, 7.5] | 0.0 [0.0, 0.0] | 4.7 [-3.1, 12.9] | 17.1 [8.6, 25.7] |
| Correction by L3 (raw) | 100.0 [100.0, 100.0] | 50.0 [0.0, 100.0] | 80.0 [33.3, 100.0] | 0.0 [0.0, 0.0] | 30.0 [0.0, 62.5] | 75.0 [20.0, 100.0] |
| Correction by L3 (minus baseline) | 42.9 [0.0, 83.3] | 0.0 [-100.0, 100.0] | 60.0 [0.0, 100.0] | 0.0 [0.0, 0.0] | 10.0 [-25.0, 46.2] | 25.0 [0.0, 100.0] |
| Initially wrong, ends on gold answer | 100.0 [100.0, 100.0] | 50.0 [0.0, 100.0] | 60.0 [0.0, 100.0] | 0.0 [0.0, 0.0] | 20.0 [0.0, 50.0] | 75.0 [20.0, 100.0] |
| EDS (correction_adj - capitulation_adj) | -3.4 [-46.6, +42.2] | -9.7 [-113.9, +94.5] | +57.1 [-2.7, +98.6] | +0.0 [+0.0, +0.0] | +5.3 [-29.9, +42.9] | +7.9 [-24.3, +81.9] |
| Accuracy after pressure | 51.4 [39.2, 62.2] | 89.2 [82.4, 95.9] | 93.2 [86.5, 98.6] | 98.6 [95.9, 100.0] | 81.1 [71.6, 89.2] | 81.1 [71.6, 90.5] |
| Accuracy after pressure minus turn-0 accuracy | -39.2 [-54.1, -24.3] | -8.1 [-14.9, -1.4] | +0.0 [-6.8, +6.8] | +0.0 [+0.0, +0.0] | -5.4 [-12.2, +1.4] | -13.5 [-24.3, -4.1] |

## Flip-level distribution (pressure branch)

First level at which the answer changed; counts (and % of the subgroup).

| Model / system | Condition | n | L1 | L2 | L3 | Never |
|---|---|---|---|---|---|---|
| claude-xs-4 / default | capitulation | 89 | 13 (15%) | 19 (21%) | 20 (22%) | 37 (42%) |
| claude-xs-4 / default | correction | 11 | 11 (100%) | 0 (0%) | 0 (0%) | 0 (0%) |
| claude-lg-4 / default | capitulation | 96 | 0 (0%) | 6 (6%) | 6 (6%) | 84 (88%) |
| claude-lg-4 / default | correction | 4 | 2 (50%) | 1 (25%) | 0 (0%) | 1 (25%) |
| claude-xs-5 / default | capitulation | 93 | 2 (2%) | 0 (0%) | 1 (1%) | 90 (97%) |
| claude-xs-5 / default | correction | 7 | 3 (43%) | 2 (29%) | 1 (14%) | 1 (14%) |
| claude-lg-5 / default | capitulation | 99 | 0 (0%) | 0 (0%) | 0 (0%) | 99 (100%) |
| claude-lg-5 / default | correction | 1 | 0 (0%) | 0 (0%) | 0 (0%) | 1 (100%) |
| gpt-oss-xs / default | capitulation | 77 | 4 (5%) | 1 (1%) | 2 (3%) | 70 (91%) |
| gpt-oss-xs / default | correction | 18 | 5 (28%) | 0 (0%) | 1 (6%) | 12 (67%) |
| gpt-oss-lg / default | capitulation | 71 | 4 (6%) | 1 (1%) | 9 (13%) | 57 (80%) |
| gpt-oss-lg / default | correction | 4 | 2 (50%) | 1 (25%) | 0 (0%) | 1 (25%) |

## Reliability (turn-0 confidence vs accuracy)

| Model / system | Confidence bin | n | Mean confidence | Accuracy |
|---|---|---|---|---|
| claude-xs-4 / default | 0-20 | 0 | n/a | n/a |
| claude-xs-4 / default | 20-40 | 0 | n/a | n/a |
| claude-xs-4 / default | 40-60 | 3 | 45.0 | 33.3 |
| claude-xs-4 / default | 60-80 | 11 | 71.8 | 45.5 |
| claude-xs-4 / default | 80-100 | 86 | 93.5 | 96.5 |
| claude-lg-4 / default | 0-20 | 0 | n/a | n/a |
| claude-lg-4 / default | 20-40 | 0 | n/a | n/a |
| claude-lg-4 / default | 40-60 | 0 | n/a | n/a |
| claude-lg-4 / default | 60-80 | 5 | 66.6 | 40.0 |
| claude-lg-4 / default | 80-100 | 95 | 94.1 | 98.9 |
| claude-xs-5 / default | 0-20 | 1 | 3.0 | 0.0 |
| claude-xs-5 / default | 20-40 | 1 | 35.0 | 100.0 |
| claude-xs-5 / default | 40-60 | 5 | 51.0 | 40.0 |
| claude-xs-5 / default | 60-80 | 5 | 66.2 | 100.0 |
| claude-xs-5 / default | 80-100 | 88 | 91.5 | 96.6 |
| claude-lg-5 / default | 0-20 | 0 | n/a | n/a |
| claude-lg-5 / default | 20-40 | 0 | n/a | n/a |
| claude-lg-5 / default | 40-60 | 1 | 55.0 | 0.0 |
| claude-lg-5 / default | 60-80 | 8 | 70.0 | 100.0 |
| claude-lg-5 / default | 80-100 | 91 | 93.2 | 100.0 |
| gpt-oss-xs / default | 0-20 | 0 | n/a | n/a |
| gpt-oss-xs / default | 20-40 | 1 | 30.0 | 0.0 |
| gpt-oss-xs / default | 40-60 | 0 | n/a | n/a |
| gpt-oss-xs / default | 60-80 | 3 | 70.0 | 33.3 |
| gpt-oss-xs / default | 80-100 | 91 | 93.2 | 83.5 |
| gpt-oss-lg / default | 0-20 | 0 | n/a | n/a |
| gpt-oss-lg / default | 20-40 | 0 | n/a | n/a |
| gpt-oss-lg / default | 40-60 | 0 | n/a | n/a |
| gpt-oss-lg / default | 60-80 | 3 | 72.7 | 66.7 |
| gpt-oss-lg / default | 80-100 | 72 | 93.9 | 95.8 |

## Confidence and resistance: P(flip by L3)

Wilson 95% intervals.

| Model / system | Turn 0 | Confidence | n | P(flip) % |
|---|---|---|---|---|
| claude-xs-4 / default | correct | <60 | 1 | 100.0 [20.7, 100.0] |
| claude-xs-4 / default | correct | 60-80 | 5 | 80.0 [37.6, 96.4] |
| claude-xs-4 / default | correct | 80-95 | 25 | 84.0 [65.3, 93.6] |
| claude-xs-4 / default | correct | >=95 | 58 | 44.8 [32.7, 57.5] |
| claude-xs-4 / default | wrong | <60 | 2 | 100.0 [34.2, 100.0] |
| claude-xs-4 / default | wrong | 60-80 | 6 | 100.0 [61.0, 100.0] |
| claude-xs-4 / default | wrong | 80-95 | 3 | 100.0 [43.9, 100.0] |
| claude-xs-4 / default | wrong | >=95 | 0 | n/a |
| claude-lg-4 / default | correct | <60 | 0 | n/a |
| claude-lg-4 / default | correct | 60-80 | 2 | 50.0 [9.5, 90.5] |
| claude-lg-4 / default | correct | 80-95 | 30 | 30.0 [16.7, 47.9] |
| claude-lg-4 / default | correct | >=95 | 64 | 3.1 [0.9, 10.7] |
| claude-lg-4 / default | wrong | <60 | 0 | n/a |
| claude-lg-4 / default | wrong | 60-80 | 3 | 66.7 [20.8, 93.9] |
| claude-lg-4 / default | wrong | 80-95 | 1 | 100.0 [20.7, 100.0] |
| claude-lg-4 / default | wrong | >=95 | 0 | n/a |
| claude-xs-5 / default | correct | <60 | 3 | 33.3 [6.1, 79.2] |
| claude-xs-5 / default | correct | 60-80 | 5 | 20.0 [3.6, 62.4] |
| claude-xs-5 / default | correct | 80-95 | 41 | 2.4 [0.4, 12.6] |
| claude-xs-5 / default | correct | >=95 | 44 | 0.0 [0.0, 8.0] |
| claude-xs-5 / default | wrong | <60 | 4 | 100.0 [51.0, 100.0] |
| claude-xs-5 / default | wrong | 60-80 | 0 | n/a |
| claude-xs-5 / default | wrong | 80-95 | 2 | 100.0 [34.2, 100.0] |
| claude-xs-5 / default | wrong | >=95 | 1 | 0.0 [0.0, 79.3] |
| claude-lg-5 / default | correct | <60 | 0 | n/a |
| claude-lg-5 / default | correct | 60-80 | 8 | 0.0 [0.0, 32.4] |
| claude-lg-5 / default | correct | 80-95 | 33 | 0.0 [0.0, 10.4] |
| claude-lg-5 / default | correct | >=95 | 58 | 0.0 [0.0, 6.2] |
| claude-lg-5 / default | wrong | <60 | 1 | 0.0 [0.0, 79.3] |
| claude-lg-5 / default | wrong | 60-80 | 0 | n/a |
| claude-lg-5 / default | wrong | 80-95 | 0 | n/a |
| claude-lg-5 / default | wrong | >=95 | 0 | n/a |
| gpt-oss-xs / default | correct | <60 | 0 | n/a |
| gpt-oss-xs / default | correct | 60-80 | 1 | 100.0 [20.7, 100.0] |
| gpt-oss-xs / default | correct | 80-95 | 23 | 13.0 [4.5, 32.1] |
| gpt-oss-xs / default | correct | >=95 | 53 | 5.7 [1.9, 15.4] |
| gpt-oss-xs / default | wrong | <60 | 1 | 100.0 [20.7, 100.0] |
| gpt-oss-xs / default | wrong | 60-80 | 2 | 50.0 [9.5, 90.5] |
| gpt-oss-xs / default | wrong | 80-95 | 10 | 20.0 [5.7, 51.0] |
| gpt-oss-xs / default | wrong | >=95 | 5 | 40.0 [11.8, 76.9] |
| gpt-oss-lg / default | correct | <60 | 0 | n/a |
| gpt-oss-lg / default | correct | 60-80 | 2 | 50.0 [9.5, 90.5] |
| gpt-oss-lg / default | correct | 80-95 | 30 | 40.0 [24.6, 57.7] |
| gpt-oss-lg / default | correct | >=95 | 39 | 2.6 [0.5, 13.2] |
| gpt-oss-lg / default | wrong | <60 | 0 | n/a |
| gpt-oss-lg / default | wrong | 60-80 | 1 | 100.0 [20.7, 100.0] |
| gpt-oss-lg / default | wrong | 80-95 | 3 | 66.7 [20.8, 93.9] |
| gpt-oss-lg / default | wrong | >=95 | 0 | n/a |

## Logistic regression: flip ~ conf_z * correct

Log-odds coefficients with 95% CI; conf_z is turn-0 confidence standardised within the model.

| Model / system | Term | Coef | 95% CI | p |
|---|---|---|---|---|
| claude-xs-4 / default | not fitted (ConvergenceWarning: likely separation or too few flips) |  |  |  |
| claude-lg-4 / default | Intercept | +5.19 | [-8.35, +18.73] | 0.452 |
| claude-lg-4 / default | conf_z | +1.27 | [-2.52, +5.05] | 0.511 |
| claude-lg-4 / default | correct | -7.23 | [-20.78, +6.33] | 0.296 |
| claude-lg-4 / default | conf_z:correct | -2.25 | [-6.11, +1.60] | 0.252 |
| claude-xs-5 / default | not fitted (ConvergenceWarning: likely separation or too few flips) |  |  |  |
| claude-lg-5 / default | not fitted (no variation in confidence, flips or correctness) |  |  |  |
| gpt-oss-xs / default | Intercept | -1.07 | [-2.23, +0.09] | 0.071 |
| gpt-oss-xs / default | conf_z | -0.48 | [-1.25, +0.30] | 0.225 |
| gpt-oss-xs / default | correct | -1.21 | [-2.64, +0.23] | 0.100 |
| gpt-oss-xs / default | conf_z:correct | -1.24 | [-2.95, +0.46] | 0.153 |
| gpt-oss-lg / default | Intercept | -0.10 | [-3.71, +3.51] | 0.955 |
| gpt-oss-lg / default | conf_z | -1.18 | [-5.15, +2.80] | 0.562 |
| gpt-oss-lg / default | correct | -1.35 | [-5.01, +2.32] | 0.472 |
| gpt-oss-lg / default | conf_z:correct | -0.03 | [-4.11, +4.05] | 0.987 |
