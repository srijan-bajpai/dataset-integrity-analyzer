# Streamlit UI Formatting Guidelines

When building or modifying Streamlit applications for this project, always adhere to the following styling and formatting rules:

## 1. Avoid Emojis
Do not use literal emoji characters (e.g., emojis for status, page icons, decorative emojis) in strings, markdown, or component configurations.
- Use textual indicators like `[CRITICAL]`, `[HIGH]`, `[MEDIUM]` for severity.
- Use Streamlit's native `st.error`, `st.warning`, `st.success`, `st.info` containers for visual differentiation.

## 2. Section Structure: Heading, Data, Conclusion
Every results section must follow this exact layout:

1. **Heading** -- the section title or metric name.
2. **Data** -- the numbers, percentages, charts, tables. Show the raw findings first.
3. **Conclusion** -- a short, formal but accessible explanation of what the data means in practice. This conclusion must be *dynamic*: it must reference the actual values found (class names, specific percentages, counts) rather than giving a static generic description.

The conclusion should be understandable to someone who is not a machine learning expert, but it should remain professional and not overly casual. Think "ELI5 but formal."

Use `st.info(...)` or `st.warning(...)` for these conclusions. Do not use `st.expander` for conclusions -- they should be visible by default.

## 3. No Static Jargon Definitions
Do not add generic definitions of metrics before the data. The user sees the metric name and its value first. The conclusion paragraph after the data explains what the number means *for this specific dataset*. Avoid walls of text.

## 4. Professional Layouts
- Use `st.columns`, `st.tabs`, and `st.divider` to organise information cleanly.
- Group related insights together and ensure a clear visual hierarchy.
