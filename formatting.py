"""Display formatting utilities."""

from pyrainbird.const import DayOfWeek, ProgramFrequency

DAY_ABBREV = {
    DayOfWeek.SUNDAY: "Sun",
    DayOfWeek.MONDAY: "Mon",
    DayOfWeek.TUESDAY: "Tue",
    DayOfWeek.WEDNESDAY: "Wed",
    DayOfWeek.THURSDAY: "Thu",
    DayOfWeek.FRIDAY: "Fri",
    DayOfWeek.SATURDAY: "Sat",
}

DAY_ORDER = [
    DayOfWeek.SUNDAY,
    DayOfWeek.MONDAY,
    DayOfWeek.TUESDAY,
    DayOfWeek.WEDNESDAY,
    DayOfWeek.THURSDAY,
    DayOfWeek.FRIDAY,
    DayOfWeek.SATURDAY,
]


def format_frequency(program) -> str:
    freq = program.frequency
    if freq == ProgramFrequency.CUSTOM:
        days = [DAY_ABBREV[d] for d in DAY_ORDER if d in program.days_of_week]
        return " ".join(days) if days else "No days set"
    elif freq == ProgramFrequency.CYCLIC:
        period = program.period or 1
        return f"Every {period} day{'s' if period != 1 else ''}"
    elif freq == ProgramFrequency.ODD:
        return "Odd days"
    elif freq == ProgramFrequency.EVEN:
        return "Even days"
    return str(freq)


def format_duration(td) -> str:
    total_minutes = int(td.total_seconds() // 60)
    return f"{total_minutes} min"
