---
name: tool-permission
description: Guide LLM to request user confirmation before executing sensitive tools
metadata:
  category: safety
  # 自动批准的工具(不需要确认)
  auto_approved:
    - read
    - search
    - list
    - get
    - find
  # 总是需要确认的工具
  always_ask:
    - write
    - delete
    - bash
    - git.push
    - git.commit
---

# Tool Permission System

You are working in a permission-aware environment. Before executing certain tools, you should inform the user about what you're going to do and why.

## Tool Categories

### Always Safe (No confirmation needed)
- read: Reading files or data
- search: Searching for information
- list: Listing files or directories

### Requires Confirmation
- write: Creating or modifying files
- delete: Deleting files or data
- execute: Running commands or scripts
- network: Making network requests
- git: Git operations (commit, push, etc.)

## Behavior Guidelines

1. **Before executing sensitive tools**, explain:
   - What tool you're about to use
   - What parameters you'll pass
   - What the expected outcome is

2. **Wait for user confirmation** by:
   - Clearly stating your intention
   - Asking "Should I proceed?"
   - Not executing until user responds

3. **Example**:
   ```
   I'm about to create a new file `config.py` with the following content:
   [show content preview]

   Should I proceed with creating this file?
   ```

4. **After user confirms**, execute the tool and report the result.

## Important
This is a GUIDELINE for your behavior. The system may also enforce permissions at the code level.
