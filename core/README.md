# Core Module

The Core module handles the translation of raw geometry into semantic objects.

## The `WallBuildUp` Object

The wall is constructed relative to the structural layer:
- **Structure**: Reference (Y = 0 to Thickness)
- **External**: Negative Y coordinates
- **Internal**: Positive Y coordinates (starting after structure)

## Configuration Example

Here is how to define a layer in the configuration dictionary:

