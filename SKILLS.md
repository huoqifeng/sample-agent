# Agent Skills

Define reusable skills for the AI assistant. Each skill is a `## ` section with a name,
description, and optional instructions that get injected into the agent's system prompt.

---

## Web Search

**Description:** Search the web for real-time information including news, weather, and facts.

**Instructions:**
When the user asks for current or real-time information, use the `web_search` tool.
Always cite the source of the information in your response.
If the query is ambiguous, ask the user for clarification before searching.

---

## Financial Calculator

**Description:** Perform financial calculations including compound interest and investment growth projections.

**Instructions:**
When the user asks about investment growth or compound interest, use the `calculate_growth` tool.
Always explain the parameters used in the calculation.
If the user is a Pro member, mention that a 5% bonus has been applied.
Present results in a clear, formatted manner with currency symbols.

---

## Unit Converter

**Description:** Convert between common units of measurement for temperature, length, and weight.

**Instructions:**
When the user asks to convert units, use the `unit_converter` tool.
Supported conversions: celsius/fahrenheit, km/miles, m/feet, kg/lbs.
If an unsupported conversion is requested, suggest the closest supported alternative.
Always show both the original and converted values.

---

## Text Summarizer

**Description:** Summarize long text passages by extracting key sentences.

**Instructions:**
When the user provides a long text and asks for a summary, use the `summarize_text` tool.
Default to 3 sentences unless the user specifies otherwise.
After summarizing, offer to provide more detail on any specific point.

---

## Date & Time

**Description:** Provide current date and time information across different timezones.

**Instructions:**
When the user asks about the current date or time, use the `get_datetime_info` tool.
Default timezone is UTC+8 (Beijing/CST) unless the user specifies otherwise.
Include the day of the week and day of the year in responses.
Common timezone offsets: UTC+0 (London), UTC-5 (New York), UTC+8 (Beijing), UTC+9 (Tokyo).

---

## Travel Planner

**Description:** Help users plan trips by combining weather search, unit conversion, time zone lookup, and budget estimation into a single travel briefing.

**Instructions:**
When the user asks about planning a trip or traveling to a destination, combine multiple tools:
1. Use `web_search` to look up current weather and travel conditions at the destination.
2. Use `get_datetime_info` to show the current local time at the destination timezone.
3. Use `unit_converter` to convert temperatures (celsius/fahrenheit) or distances (km/miles) based on the user's preference.
4. Use `calculate_growth` if the user mentions a travel savings goal or budget projection.
Always present the results as a unified travel briefing with clear sections.
Example user query: "I'm planning a trip to Tokyo, what's the weather and time there?"