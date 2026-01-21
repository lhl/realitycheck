# Inbox - Simple Source Queue

**Status**: Planning
**Created**: 2026-01-22

## Concept

A simple place to queue URLs and notes for future processing. Subfolders organize items by topic/task.

```
inbox/
├── README.md              # Optional: inbox-wide notes
├── url-1.md               # Items in root = general queue
├── url-2.md
├── ai-productivity/       # Subfolder = task/topic collection
│   ├── README.md          # Optional: collection notes
│   ├── source-1.md
│   └── source-2.md
└── energy-transition/
    └── stross-follow-up.md
```

## Item Format

Minimal - just enough to remember why you saved it:

```markdown
# [Title or description]

**URL**: https://example.com/article
**Added**: 2026-01-22

[Optional notes, context, related claims]
```

Or even simpler - just a URL and a line of context:

```markdown
https://example.com/article

Why: contradicts TECH-2026-001
```

## Commands

```bash
# Add to root inbox
/inbox add <url> [notes]

# Add to subfolder (creates if needed)
/inbox <folder> add <url> [notes]

# List inbox contents
/inbox list
/inbox <folder> list

# Process items (runs /check on each)
/inbox process              # Process root items
/inbox <folder> process     # Process folder items

# Clear processed items
/inbox <folder> clear
```

## Workflow Examples

### Quick capture
```bash
/inbox add https://example.com/interesting-article "Relates to labor automation claims"
```

### Collect sources on a topic
```bash
/inbox ai-productivity add https://arxiv.org/abs/... "Another RCT"
/inbox ai-productivity add https://... "Industry survey"

# Later, process all at once
/inbox ai-productivity process
```

### Batch processing
```bash
/inbox ai-productivity process --quick   # Quick extractions
/inbox ai-productivity process           # Full analyses
```

## Integration with /check

When `/inbox process` runs:
1. Iterate through items in folder
2. Run `/check <url>` for each
3. On success, either:
   - Move item to `inbox/.processed/` (archive), or
   - Delete item (simpler)
4. On failure, leave item in place with error note

## Implementation

### Phase 1: Manual
- Create `inbox/` in data repo
- Add items manually as markdown files
- Process by reading and running `/check` manually

### Phase 2: Commands
- `/inbox add` - creates item file
- `/inbox list` - shows contents
- `/inbox process` - iterates and runs `/check`

### Phase 3: Polish
- Auto-extract title from URL on add
- Track processed/failed status
- Subfolder summaries

## Version History

- 2026-01-22: Simplified from over-engineered multi-queue system
