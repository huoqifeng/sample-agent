import streamlit as st
import asyncio
import os
import re
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI


# --- 0. SKILLS.md LOADER ---
@dataclass
class Skill:
    """A skill parsed from SKILLS.md."""
    name: str
    description: str
    instructions: str


def load_skills(filepath: str = 'SKILLS.md') -> list[Skill]:
    """Parse SKILLS.md and return a list of Skill objects.

    Expected format per skill:
        ## Skill Name
        **Description:** ...
        **Instructions:**
        line1
        line2
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    skills: list[Skill] = []
    # Split by ## headings (level 2)
    sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split('\n')
        name = lines[0].strip()

        # Skip the top-level heading (# Agent Skills)
        if name.startswith('#'):
            continue

        body = '\n'.join(lines[1:])

        # Extract description
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+)', body)
        description = desc_match.group(1).strip() if desc_match else ''

        # Extract instructions (everything after **Instructions:**)
        instr_match = re.search(r'\*\*Instructions:\*\*\s*\n([\s\S]*)', body)
        instructions = instr_match.group(1).strip() if instr_match else ''

        skills.append(Skill(name=name, description=description, instructions=instructions))

    return skills


def build_skills_prompt(skills: list[Skill]) -> str:
    """Build a system prompt section from loaded skills."""
    if not skills:
        return ''

    parts = ['You have the following skills available:\n']
    for skill in skills:
        parts.append(f'### {skill.name}')
        parts.append(f'{skill.description}')
        if skill.instructions:
            parts.append(f'Guidelines:\n{skill.instructions}')
        parts.append('')

    return '\n'.join(parts)


# Load skills from SKILLS.md
skills = load_skills()
skills_prompt = build_skills_prompt(skills)

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="PydanticAI Agent", page_icon="🤖")
st.title("🤖 PydanticAI Research Assistant")

# Sidebar for API Key and Settings
with st.sidebar:
    st.header("Settings")
    base_url = st.text_input("Base URL", value="https://ai.gitee.com/v1")
    model_name = st.text_input("Model Name", value="Qwen3-8B")
    api_key = st.text_input("API Key", type="password", help="Optional for free models")
    is_pro = st.checkbox("Pro Member Mode", value=True)

    # Display loaded skills from SKILLS.md
    st.divider()
    st.header("Loaded Skills")
    if skills:
        for skill in skills:
            with st.expander(f"{skill.name}"):
                st.markdown(f"**{skill.description}**")
                if skill.instructions:
                    st.code(skill.instructions, language=None)
    else:
        st.info("No SKILLS.md found. Add one to define agent skills.")

# --- 2. AGENT DEFINITION ---
@dataclass
class UserContext:
    user_name: str
    is_pro_member: bool

def get_agent(key: str, base_url: str, model_name: str):
    custom_client = AsyncOpenAI(
        base_url=base_url,
        api_key=key or "EMPTY"
    )

    # Pass the client to OpenAIModel via OpenAIProvider
    model = OpenAIModel(
        model_name,
        provider=OpenAIProvider(openai_client=custom_client),
    )

    # Build system prompt with skills from SKILLS.md
    base_prompt = "You are a helpful assistant."
    system_prompt = f"{base_prompt}\n\n{skills_prompt}" if skills_prompt else base_prompt

    return Agent(model, deps_type=UserContext, system_prompt=system_prompt)

# --- 3. TOOLS / SKILLS ---
# Skills are capabilities the agent can invoke via @agent.tool decorators.
# Each skill is a function that the LLM can call to perform a specific task.

agent = get_agent(api_key, base_url, model_name)

# ---- Skill 1: Web Search ----
@agent.tool
async def web_search(ctx: RunContext[UserContext], query: str) -> str:
    """Search the web for current information on any topic."""
    return f"Simulated result for '{query}': The weather is 22°C."

# ---- Skill 2: Compound Interest Calculator ----
@agent.tool
def calculate_growth(ctx: RunContext[UserContext], initial: float, rate: float, years: int) -> str:
    """Calculates compound interest growth. Pro members get a 5% bonus."""
    bonus = 1.05 if ctx.deps.is_pro_member else 1.0
    result = initial * (rate ** years) * bonus
    return f"Calculated Value: {result:.2f} (Pro: {ctx.deps.is_pro_member})"

# ---- Skill 3: Unit Converter ----
@agent.tool
def unit_converter(ctx: RunContext[UserContext], value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units of measurement.

    Supported conversions:
    - Temperature: celsius <-> fahrenheit
    - Length: km <-> miles, m <-> feet
    - Weight: kg <-> lbs
    """
    conversions: dict[tuple[str, str], float] = {
        ('celsius', 'fahrenheit'): lambda v: v * 9 / 5 + 32,
        ('fahrenheit', 'celsius'): lambda v: (v - 32) * 5 / 9,
        ('km', 'miles'): lambda v: v * 0.621371,
        ('miles', 'km'): lambda v: v / 0.621371,
        ('m', 'feet'): lambda v: v * 3.28084,
        ('feet', 'm'): lambda v: v / 3.28084,
        ('kg', 'lbs'): lambda v: v * 2.20462,
        ('lbs', 'kg'): lambda v: v / 2.20462,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    return f"Unsupported conversion: {from_unit} -> {to_unit}. Supported: celsius/fahrenheit, km/miles, m/feet, kg/lbs"

# ---- Skill 4: Text Summarizer ----
@agent.tool
def summarize_text(ctx: RunContext[UserContext], text: str, max_sentences: int = 3) -> str:
    """Summarize a given text by extracting the first N sentences.

    Args:
        text: The text to summarize.
        max_sentences: Maximum number of sentences to include (default: 3).
    """
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    summary = '. '.join(sentences[:max_sentences]) + '.'
    return f"Summary ({len(sentences[:max_sentences])}/{len(sentences)} sentences): {summary}"

# ---- Skill 5: Date & Time Info ----
@agent.tool
def get_datetime_info(ctx: RunContext[UserContext], timezone_offset: int = 8) -> str:
    """Get the current date and time information.

    Args:
        timezone_offset: UTC offset in hours (default: 8 for CST/Beijing).
    """
    from datetime import datetime, timedelta, timezone
    tz = timezone(timedelta(hours=timezone_offset))
    now = datetime.now(tz)
    return (
        f"Current Time (UTC{'+' if timezone_offset >= 0 else ''}{timezone_offset}): "
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Day of week: {now.strftime('%A')} | "
        f"Day of year: {now.timetuple().tm_yday}"
    )

# ---- Skill 6: Travel Planner (multi-tool skill) ----
@agent.tool
async def travel_planner(ctx: RunContext[UserContext], destination: str, home_timezone: int = 8) -> str:
        """Plan a trip by gathering weather, local time, and travel info for a destination.

        This skill combines multiple tools into one travel briefing:
        - Searches for current weather and travel conditions
        - Shows destination local time vs home time
        - Converts temperature between celsius and fahrenheit
        - Plane ticket information and price compare
        - Provides a travel readiness summary

        Args:
            destination: The travel destination city/country.
            home_timezone: The user's home UTC offset (default: 8 for Beijing).
        """
        from datetime import datetime, timedelta, timezone as tz_mod

        # --- Destination timezone mapping ---
        tz_map: dict[str, int] = {
            'tokyo': 9, 'japan': 9, 'osaka': 9,
            'new york': -5, 'nyc': -5, 'washington': -5,
            'london': 0, 'uk': 0,
            'paris': 1, 'berlin': 1, 'france': 1, 'germany': 1,
            'sydney': 11, 'australia': 11,
            'dubai': 4, 'uae': 4,
            'beijing': 8, 'shanghai': 8, 'china': 8,
            'seoul': 9, 'korea': 9,
            'bangkok': 7, 'thailand': 7,
            'singapore': 8,
            'los angeles': -8, 'la': -8, 'san francisco': -8,
        }
        dest_lower = destination.lower()
        dest_tz = tz_map.get(dest_lower, 0)

        # --- Tool 1: Web Search for weather & conditions ---
        weather_result = f"Simulated result for '{destination} weather travel conditions': Clear skies, 25°C, good travel conditions."

        # --- Tool 2: Get local time at destination ---
        dest_zone = tz_mod(timedelta(hours=dest_tz))
        home_zone = tz_mod(timedelta(hours=home_timezone))
        dest_now = datetime.now(dest_zone)
        home_now = datetime.now(home_zone)

        # --- Tool 3: Unit conversion (temperature) ---
        temp_c = 25.0  # from simulated weather
        temp_f = temp_c * 9 / 5 + 32

        # --- Tool 4: Plane ticket information and price compare ---
        import random
        airlines = ['Air China', 'China Eastern', 'China Southern', 'United Airlines', 'Delta Airlines']
        ticket_info = []
        for airline in random.sample(airlines, k=min(3, len(airlines))):
            price = random.randint(800, 3500)
            duration_h = random.randint(2, 16)
            duration_m = random.choice([0, 15, 30, 45])
            stops = random.choice([0, 0, 1, 1, 2])
            stop_label = 'Direct' if stops == 0 else f'{stops} stop{"s" if stops > 1 else ""}'
            ticket_info.append({
                'airline': airline,
                'price': price,
                'duration': f'{duration_h}h {duration_m}m',
                'stops': stop_label,
            })
        ticket_info.sort(key=lambda x: x['price'])
        cheapest = ticket_info[0]
        ticket_lines = '\n'.join(
            f"   {'👑 ' if t == cheapest else '   '}{t['airline']:<20} ${t['price']:<8} {t['duration']:<8} {t['stops']}"
            for t in ticket_info
        )

        # --- Build unified travel briefing ---
        briefing = f"""🌍 Travel Briefing: {destination}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 Weather & Conditions:
   {weather_result}

🕐 Time Zones:
   {destination}: {dest_now.strftime('%Y-%m-%d %H:%M %A')} (UTC{'+' if dest_tz >= 0 else ''}{dest_tz})
   Home:          {home_now.strftime('%Y-%m-%d %H:%M %A')} (UTC{'+' if home_timezone >= 0 else ''}{home_timezone})
   Time difference: {abs(dest_tz - home_timezone)}h {'ahead' if dest_tz > home_timezone else 'behind' if dest_tz < home_timezone else '(same)'}

🌡️ Temperature:
   {temp_c}°C = {temp_f:.1f}°F

✈️ Plane Tickets (sorted by price):
   {"Airline":<20} {"Price":<8} {"Duration":<8} Stops
   {"─" * 50}
{ticket_lines}
   💡 Best deal: {cheapest['airline']} at ${cheapest['price']}

✅ Travel Readiness: All checks passed!"""

        return briefing

# --- 4. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask me anything (e.g., 'Search for weather and calc $1000 growth')"):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Agent Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Initialize context
                deps = UserContext(user_name="User", is_pro_member=is_pro)
                
                # Run the agent (using run_sync for Streamlit compatibility)
                result = agent.run_sync(prompt, deps=deps)
                
                response_text = result.data
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"An error occurred: {e}")


# brew install pyenv
# poetry env use $(pyenv prefix 3.11)/bin/python
# poetry lock
# poetry install --no-root
# poetry run streamlit run app.py