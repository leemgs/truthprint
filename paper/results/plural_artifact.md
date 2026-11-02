# Generator plural artifact ("cache misss")

153 of 800 source sentences contain the ungrammatical plural *cache misss* (template generator appends "s"); they were translated as is. Stage-2 recovery on the committed NLLB outputs (Wilson 95% CI): affected sentences vs a plural control (454 sources with another patient and quantity > 1, grammatical plural) and singular sentences. The affected group differs from the control only in the patient noun, so the patient noun and the misspelling are confounded.

| Condition | Group | n | Patient | core6 record | All nine fields |
|---|---|---|---|---|---|
| ar | affected | 153 | 0.007 [0.001,0.036] | 0.837 [0.770,0.887] | 0.007 [0.001,0.036] |
| ar | plural_control | 454 | 0.476 [0.430,0.522] | 0.522 [0.476,0.568] | 0.271 [0.232,0.314] |
| ar | singular | 193 | 0.549 [0.479,0.618] | 0.668 [0.599,0.731] | 0.404 [0.337,0.475] |
| de | affected | 153 | 1.000 [0.976,1.000] | 1.000 [0.976,1.000] | 0.752 [0.678,0.813] |
| de | plural_control | 454 | 1.000 [0.992,1.000] | 0.775 [0.735,0.811] | 0.566 [0.520,0.611] |
| de | singular | 193 | 0.995 [0.971,0.999] | 0.907 [0.857,0.940] | 0.788 [0.725,0.839] |
| hi | affected | 153 | 1.000 [0.976,1.000] | 0.699 [0.623,0.766] | 0.660 [0.582,0.730] |
| hi | plural_control | 454 | 0.760 [0.719,0.797] | 0.919 [0.890,0.940] | 0.687 [0.643,0.728] |
| hi | singular | 193 | 0.839 [0.781,0.884] | 0.959 [0.920,0.979] | 0.699 [0.631,0.760] |
| ko | affected | 153 | 1.000 [0.976,1.000] | 0.902 [0.845,0.940] | 0.379 [0.306,0.458] |
| ko | plural_control | 454 | 0.974 [0.954,0.985] | 0.590 [0.544,0.635] | 0.405 [0.361,0.451] |
| ko | singular | 193 | 0.865 [0.810,0.906] | 0.725 [0.658,0.783] | 0.461 [0.392,0.532] |
| rt | affected | 153 | 0.510 [0.431,0.588] | 0.817 [0.748,0.870] | 0.190 [0.135,0.259] |
| rt | plural_control | 454 | 0.960 [0.938,0.975] | 0.707 [0.664,0.747] | 0.436 [0.391,0.482] |
| rt | singular | 193 | 0.860 [0.804,0.902] | 0.684 [0.615,0.745] | 0.389 [0.323,0.459] |
| zh | affected | 153 | 1.000 [0.976,1.000] | 0.824 [0.755,0.876] | 0.320 [0.252,0.398] |
| zh | plural_control | 454 | 0.925 [0.897,0.946] | 0.601 [0.556,0.645] | 0.344 [0.301,0.388] |
| zh | singular | 193 | 0.855 [0.798,0.898] | 0.694 [0.626,0.755] | 0.290 [0.231,0.358] |

core6 record recovery, all sentences vs excluding affected ones:

| Condition | All | Without affected |
|---|---|---|
| ar | 0.618 [0.583,0.651] | 0.566 [0.527,0.603] |
| de | 0.850 [0.824,0.873] | 0.815 [0.783,0.843] |
| hi | 0.886 [0.862,0.906] | 0.930 [0.908,0.948] |
| ko | 0.682 [0.649,0.714] | 0.631 [0.593,0.667] |
| rt | 0.723 [0.690,0.752] | 0.700 [0.664,0.734] |
| zh | 0.666 [0.633,0.698] | 0.629 [0.591,0.665] |

core6 document attribution (id-addressed, >= half of the sentences), all sentences vs excluding affected ones:

| Condition | All | Without affected |
|---|---|---|
| ar | 0.900 [0.786,0.957] | 0.700 [0.562,0.809] |
| de | 1.000 [0.929,1.000] | 0.980 [0.895,0.996] |
| hi | 1.000 [0.929,1.000] | 1.000 [0.929,1.000] |
| ko | 0.940 [0.838,0.979] | 0.900 [0.786,0.957] |
| rt | 0.980 [0.895,0.996] | 0.960 [0.865,0.989] |
| zh | 0.940 [0.838,0.979] | 0.920 [0.812,0.968] |
