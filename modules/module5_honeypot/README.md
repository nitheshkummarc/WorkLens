# module5_honeypot

Flags internally impossible profiles; module6 gives them a final score of 0.

- **H1**: 3 or more skills at advanced/expert with `duration_months == 0`
- **H2**: total career months > `years_of_experience * 12 * 1.5 + 12`

On the provided pool these flag 43 candidates (0.043%). A keyword-stuffed profile with a plausible timeline is not a honeypot; capability scoring and the anti-signals handle it.

```python
from modules.module5_honeypot import HoneypotDetector
analysis = HoneypotDetector().detect(candidate)
```
