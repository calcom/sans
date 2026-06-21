"""Tiny shared helpers used across the build steps."""


def axis_index(axes, tag):
    """Position of the axis with this tag in an axis list (a glyphsLib `font.axes`
    or a fontTools `fvar.axes`), or None if absent. Replaces the
    `next((i for i, a in enumerate(axes) if a.axisTag == tag), None)` one-liner
    that was duplicated across the build steps."""
    return next((i for i, axis in enumerate(axes) if axis.axisTag == tag), None)


def axis_by_tag(axes, tag):
    """The axis object with this tag (not its index), or None if absent."""
    return next((axis for axis in axes if axis.axisTag == tag), None)
