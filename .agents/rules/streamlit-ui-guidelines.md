# Streamlit UI Formatting Guidelines

When building or modifying Streamlit applications for this project, always adhere to the following styling and formatting rules:

## 1. Avoid Emojis
Do not use literal emoji characters (e.g., 🚀, 🔍, 🚨, ⚠️, ✅) in strings, markdown, or component configurations (like `page_icon`). 
- Instead of emojis for status, use textual indicators like `[CRITICAL]`, `[WARNING]`, `[INFO]`.
- Leverage Streamlit's native status containers (`st.error`, `st.warning`, `st.success`) where appropriate, but rely on their built-in UI rather than injecting custom emojis into their text.

## 2. Accessible Explanations (Formal "ELI5")
When presenting complex metrics, jargon, or data visualizations, always include an explanatory note.
- The note should explain what the metric means in practice and what conclusion the user should draw.
- The tone should be "ELI5 but formal": accessible to non-experts without being overly simplistic or colloquial.
- Present these notes consistently, for example using `st.info`, `st.caption`, or an `st.expander` labeled "What does this mean?".

## 3. Professional Layouts
- Make use of Streamlit layout options like `st.columns`, `st.tabs`, and `st.divider` to organize information cleanly.
- Group related insights together and ensure a clear visual hierarchy.
