# Agent Context Directory

## Purpose
This directory stores session-specific context information for AI agents operating in the data lake. It helps maintain state and continuity across agent interactions.

## What Goes Here
- Session state files
- Context caches
- Temporary processing metadata
- Agent-specific configurations

## Rules
- Files are automatically managed by the agent framework
- Do not manually modify these files
- Contents may be purged automatically
- Sensitive information should be properly secured

## Example Files
- `session_abc123/context.json`
- `user_prefs/john_doe/preferences.json`

## Next Step
This is an internal directory used by the agent framework.
