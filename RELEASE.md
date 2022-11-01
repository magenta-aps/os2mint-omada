Release type: minor

[#53184] Operate on full MO history, instead of just the present

Omada already provides temporality through its 'VALIDFROM' and 'VALIDTO' fields, so all of an object's validity intervals should be synchronised; operating only on the latest/present one is insufficient.
