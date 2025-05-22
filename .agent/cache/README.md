# Agent Cache Directory

## Purpose
This directory serves as a cache for AI agents to store temporary computation results, embeddings, or other processed data to improve performance.

## What Goes Here
- Cached computation results
- Embedding vectors
- Pre-processed data
- Temporary model artifacts

## Rules
- Contents can be safely deleted
- No critical data should be stored here
- Cache may be cleared automatically
- Respect size limits

## Example Files
- `embeddings/artist_names.npy`
- `models/temp_model_weights.h5`

## Next Step
This is an internal directory used by the agent framework.
