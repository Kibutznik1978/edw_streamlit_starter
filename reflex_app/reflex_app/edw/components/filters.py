"""Advanced Filtering UI Component.

This module provides comprehensive filtering controls for the EDW Pairing Analyzer:
- Basic filters: Max duty day length, max legs per duty
- Duty day criteria: Duration, legs, EDW status with match modes
- Trip-level filters: EDW type, Hot Standby status
- Sort options and reset functionality
"""

import reflex as rx

from ..edw_state import EDWState


def filters_component() -> rx.Component:
    """Advanced filtering controls component.

    Displays collapsible filter panel with multiple filtering options.
    Only shown when results are available.

    Returns:
        Reflex component
    """
    return rx.cond(
        EDWState.has_results,
        rx.vstack(
            # Header with filter count indicator
            rx.hstack(
                rx.heading(
                    "Advanced Filters",
                    size="6",
                    weight="bold",
                ),
                rx.badge(
                    rx.cond(
                        EDWState.filtered_trip_count == EDWState.total_unique_pairings,
                        EDWState.filtered_trip_count.to(str) + " pairings (all)",
                        EDWState.filtered_trip_count.to(str) + " of " + EDWState.total_unique_pairings.to(str) + " pairings",
                    ),
                    color_scheme="blue",
                    size="2",
                ),
                spacing="3",
                align="center",
                width="100%",
                justify="between",
            ),

            # Collapsible filter sections
            rx.accordion.root(
                # Basic Filters Section
                rx.accordion.item(
                    rx.accordion.trigger(
                        rx.hstack(
                            rx.icon("sliders-horizontal", size=18),
                            rx.text("Basic Filters", weight="medium"),
                            spacing="2",
                        ),
                    ),
                    rx.accordion.content(
                        rx.vstack(
                            # Max duty day length slider
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        "Minimum Duty Day Length",
                                        size="2",
                                        weight="medium",
                                    ),
                                    rx.text(
                                        EDWState.filter_duty_day_min.to(str) + " hrs",
                                        size="2",
                                        color="gray",
                                    ),
                                    spacing="2",
                                    align="center",
                                    width="100%",
                                    justify="between",
                                ),
                                rx.slider(
                                    default_value=[EDWState.filter_duty_day_min],
                                    on_value_commit=lambda value: EDWState.set_filter_duty_day_min(value[0]),
                                    min=0,
                                    max=EDWState.filter_duty_day_max_available,
                                    step=0.5,
                                    width="100%",
                                ),
                                rx.text(
                                    "Show trips with at least one duty day of this length",
                                    size="1",
                                    color="gray",
                                ),
                                spacing="1",
                                width="100%",
                            ),

                            # Max legs per duty slider
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        "Minimum Legs Per Duty Day",
                                        size="2",
                                        weight="medium",
                                    ),
                                    rx.text(
                                        EDWState.filter_legs_min.to(str),
                                        size="2",
                                        color="gray",
                                    ),
                                    spacing="2",
                                    align="center",
                                    width="100%",
                                    justify="between",
                                ),
                                rx.slider(
                                    default_value=[EDWState.filter_legs_min],
                                    on_value_commit=lambda value: EDWState.set_filter_legs_min(value[0]),
                                    min=0,
                                    max=EDWState.filter_legs_max_available,
                                    step=1,
                                    width="100%",
                                ),
                                rx.text(
                                    "Show trips with at least one duty day with this many legs",
                                    size="1",
                                    color="gray",
                                ),
                                spacing="1",
                                width="100%",
                            ),

                            spacing="4",
                            width="100%",
                            padding="2",
                        ),
                    ),
                    value="basic",
                ),

                # Duty Day Criteria Section
                rx.accordion.item(
                    rx.accordion.trigger(
                        rx.hstack(
                            rx.icon("filter", size=18),
                            rx.text("Duty Day Criteria", weight="medium"),
                            spacing="2",
                        ),
                    ),
                    rx.accordion.content(
                        rx.vstack(
                            rx.callout.root(
                                rx.callout.text(
                                    "Find trips based on specific duty day characteristics. "
                                    "Choose whether ANY or ALL duty days must match the criteria.",
                                ),
                                size="1",
                                color="blue",
                            ),

                            # Match mode selector
                            rx.vstack(
                                rx.text(
                                    "Match Mode",
                                    size="2",
                                    weight="medium",
                                ),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Select match mode"),
                                    rx.select.content(
                                        rx.select.item("Disabled", value="Disabled"),
                                        rx.select.item("Any duty day matches", value="Any duty day matches"),
                                        rx.select.item("All duty days match", value="All duty days match"),
                                    ),
                                    value=EDWState.match_mode,
                                    on_change=EDWState.set_match_mode,
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),

                            # Criteria controls (only shown when not disabled)
                            rx.cond(
                                EDWState.match_mode != "Disabled",
                                rx.vstack(
                                    # Duty duration minimum
                                    rx.vstack(
                                        rx.hstack(
                                            rx.text(
                                                "Minimum Duration",
                                                size="2",
                                                weight="medium",
                                            ),
                                            rx.text(
                                                EDWState.duty_duration_min.to(str) + " hrs",
                                                size="2",
                                                color="gray",
                                            ),
                                            spacing="2",
                                            align="center",
                                            width="100%",
                                            justify="between",
                                        ),
                                        rx.slider(
                                            default_value=[EDWState.duty_duration_min],
                                            on_value_commit=lambda value: EDWState.set_duty_duration_min(value[0]),
                                            min=0,
                                            max=24,
                                            step=0.5,
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                    ),

                                    # Duty legs minimum
                                    rx.vstack(
                                        rx.hstack(
                                            rx.text(
                                                "Minimum Legs",
                                                size="2",
                                                weight="medium",
                                            ),
                                            rx.text(
                                                EDWState.duty_legs_min.to(str),
                                                size="2",
                                                color="gray",
                                            ),
                                            spacing="2",
                                            align="center",
                                            width="100%",
                                            justify="between",
                                        ),
                                        rx.slider(
                                            default_value=[EDWState.duty_legs_min],
                                            on_value_commit=lambda value: EDWState.set_duty_legs_min(value[0]),
                                            min=0,
                                            max=10,
                                            step=1,
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                    ),

                                    # EDW status filter
                                    rx.vstack(
                                        rx.text(
                                            "EDW Status",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.select.root(
                                            rx.select.trigger(placeholder="Select EDW status"),
                                            rx.select.content(
                                                rx.select.item("Any", value="Any"),
                                                rx.select.item("EDW Only", value="EDW Only"),
                                                rx.select.item("Non-EDW Only", value="Non-EDW Only"),
                                            ),
                                            value=EDWState.duty_edw_filter,
                                            on_change=EDWState.set_duty_edw_filter,
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                    ),

                                    spacing="4",
                                    width="100%",
                                ),
                            ),

                            spacing="4",
                            width="100%",
                            padding="2",
                        ),
                    ),
                    value="criteria",
                ),

                # Trip-Level Filters Section
                rx.accordion.item(
                    rx.accordion.trigger(
                        rx.hstack(
                            rx.icon("list-filter", size=18),
                            rx.text("Trip-Level Filters", weight="medium"),
                            spacing="2",
                        ),
                    ),
                    rx.accordion.content(
                        rx.vstack(
                            # EDW trip filter
                            rx.vstack(
                                rx.text(
                                    "Trip Type",
                                    size="2",
                                    weight="medium",
                                ),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Select trip type"),
                                    rx.select.content(
                                        rx.select.item("All", value="All"),
                                        rx.select.item("EDW Only", value="EDW Only"),
                                        rx.select.item("Day Only", value="Day Only"),
                                    ),
                                    value=EDWState.filter_edw,
                                    on_change=EDWState.set_filter_edw,
                                    width="100%",
                                ),
                                rx.text(
                                    "EDW = trips touching 02:30-05:00 local time",
                                    size="1",
                                    color="gray",
                                ),
                                spacing="1",
                                width="100%",
                            ),

                            # Hot Standby filter
                            rx.vstack(
                                rx.text(
                                    "Hot Standby",
                                    size="2",
                                    weight="medium",
                                ),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Select Hot Standby filter"),
                                    rx.select.content(
                                        rx.select.item("All", value="All"),
                                        rx.select.item("Hot Standby Only", value="Hot Standby Only"),
                                        rx.select.item("Exclude Hot Standby", value="Exclude Hot Standby"),
                                    ),
                                    value=EDWState.filter_hot_standby,
                                    on_change=EDWState.set_filter_hot_standby,
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),

                            spacing="4",
                            width="100%",
                            padding="2",
                        ),
                    ),
                    value="trip",
                ),

                # Sort Options Section
                rx.accordion.item(
                    rx.accordion.trigger(
                        rx.hstack(
                            rx.icon("arrow-up-down", size=18),
                            rx.text("Sort Options", weight="medium"),
                            spacing="2",
                        ),
                    ),
                    rx.accordion.content(
                        rx.vstack(
                            rx.text(
                                "Sort By",
                                size="2",
                                weight="medium",
                            ),
                            rx.select.root(
                                rx.select.trigger(placeholder="Select sort field"),
                                rx.select.content(
                                    rx.select.item("Trip ID", value="Trip ID"),
                                    rx.select.item("Frequency", value="Frequency"),
                                    rx.select.item("TAFB Hours", value="TAFB Hours"),
                                    rx.select.item("Duty Days", value="Duty Days"),
                                ),
                                value=EDWState.sort_by,
                                on_change=EDWState.set_sort_by,
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                            padding="2",
                        ),
                    ),
                    value="sort",
                ),

                type="multiple",  # Allow multiple sections open
                width="100%",
                variant="soft",
            ),

            # Reset button
            rx.button(
                rx.icon("rotate-ccw", size=16),
                "Reset All Filters",
                on_click=EDWState.reset_filters,
                variant="soft",
                color_scheme="gray",
                width="100%",
                cursor="pointer",
            ),

            width="100%",
            spacing="4",
            padding="4",
            border_radius="8px",
            border=f"1px solid {rx.color('gray', 6)}",
            background=rx.color("gray", 2),
        )
    )
