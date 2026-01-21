# /rc-stats - Database Statistics

Show statistics about the Reality Check database.

## Usage

```
/rc-stats
```

## Output

Displays counts for all tables:
- Claims
- Sources
- Chains
- Predictions
- Contradictions
- Definitions

## Implementation

Run the stats command:

```bash
uv run python scripts/db.py stats
```

## Related Commands

- `/rc-validate` - Check data integrity
- `/rc-export` - Export data to files
