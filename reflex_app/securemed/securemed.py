import reflex as rx
from .state import State

def header() -> rx.Component:
    return rx.hstack(
        rx.heading("SecureMed Chat", size="7", color_scheme="cyan"),
        rx.spacer(),
        rx.color_mode.button(),
        width="100%",
        padding="1.5em",
        border_bottom="1px solid rgba(255,255,255,0.1)",
    )

def step_0_demographics() -> rx.Component:
    return rx.vstack(
        rx.heading("Patient Intake", size="8", margin_bottom="0.5em"),
        rx.text("Tell us about yourself and your primary concern today.", color_scheme="gray"),
        rx.divider(),
        rx.vstack(
            rx.text("Age", weight="bold"),
            rx.input(
                placeholder="Ex: 35", 
                type="number", 
                on_change=State.change_age, 
                value=State.age.to(str),
                width="100%"
            ),
            rx.text("Gender", weight="bold"),
            rx.select(
                ["Male", "Female", "Other"],
                placeholder="Select Gender",
                on_change=State.set_gender,
                value=State.gender,
                width="100%"
            ),
            rx.text("Language Preference", weight="bold"),
            rx.select(
                ["en", "pt"],
                placeholder="Select Language",
                on_change=State.set_lang,
                value=State.lang,
                width="100%"
            ),
            rx.text("What is your main health concern today?", weight="bold"),
            rx.text_area(
                placeholder="Describe your symptoms briefly...",
                on_change=State.set_chief_complaint,
                value=State.chief_complaint,
                width="100%",
                height="100px"
            ),
            spacing="4",
            width="100%",
            padding_y="1em"
        ),
        rx.button(
            "Start Consultation", 
            on_click=State.init_session, 
            loading=State.loading,
            color_scheme="cyan",
            size="3",
            width="100%"
        ),
        width="100%",
        spacing="5",
    )

def step_1_initial_qs() -> rx.Component:
    return rx.vstack(
        rx.heading("Step 1: Clinical Assessment", size="7"),
        rx.text("Please review the questions below carefully.", color_scheme="gray"),
        rx.card(
            rx.scroll_area(
                rx.text(State.initial_questions_text),
                height="200px"
            ),
            width="100%",
            padding="1em",
            variant="classic"
        ),
        rx.text("Your Answers (OPQRST)", weight="bold"),
        rx.text_area(
            placeholder="Type your answers here...",
            on_change=State.set_initial_answers,
            value=State.initial_answers,
            width="100%",
            height="150px"
        ),
        rx.button(
            "Submit & Continue", 
            on_click=State.submit_initial_answers, 
            loading=State.loading,
            color_scheme="cyan",
            size="3",
            width="100%"
        ),
        width="100%",
        spacing="5"
    )

def step_2_follow_up_qs() -> rx.Component:
    return rx.vstack(
        rx.heading("Step 2: Medical History", size="7"),
        rx.text("Final set of clinical questions.", color_scheme="gray"),
        rx.card(
            rx.scroll_area(
                rx.text(State.follow_up_questions_text),
                height="200px"
            ),
            width="100%",
            padding="1em",
            variant="classic"
        ),
        rx.text("Your History (SAMPLE)", weight="bold"),
        rx.text_area(
            placeholder="Type your history details here...",
            on_change=State.set_follow_up_answers,
            value=State.follow_up_answers,
            width="100%",
            height="150px"
        ),
        rx.button(
            "Generate Final Report", 
            on_click=State.submit_follow_up_answers, 
            loading=State.loading,
            color_scheme="cyan",
            size="3",
            width="100%"
        ),
        width="100%",
        spacing="5"
    )

def step_3_summary() -> rx.Component:
    return rx.vstack(
        rx.heading("Consultation Complete! ✅", size="8", text_align="center"),
        rx.text("Your clinical summary has been generated and is ready for download.", text_align="center"),
        rx.divider(),
        rx.button(
            "Download PDF Report", 
            on_click=State.download_report,
            color_scheme="green",
            size="4",
            width="100%",
            padding="2em"
        ),
        rx.button(
            "Start New Session", 
            on_click=rx.redirect("/"),
            color_scheme="gray",
            variant="ghost"
        ),
        width="100%",
        spacing="5",
        padding_y="2em"
    )

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            header(),
            rx.container(
                rx.card(
                    rx.match(
                        State.step,
                        (0, step_0_demographics()),
                        (1, step_1_initial_qs()),
                        (2, step_2_follow_up_qs()),
                        (3, step_3_summary()),
                        step_0_demographics()
                    ),
                    padding="2em",
                    width="100%",
                    background="rgba(255,255,255,0.05)",
                    backdrop_filter="blur(15px)",
                    border="1px solid rgba(255,255,255,0.1)",
                    border_radius="20px",
                    box_shadow="0 8px 32px 0 rgba(0,0,0,0.37)"
                ),
                max_width="600px",
                padding_top="2em",
                padding_bottom="5em"
            ),
            width="100%",
            min_height="100vh",
            background="radial-gradient(circle at top right, #0a192f, #001f3f, #001529)"
        ),
        width="100%"
    )

app = rx.App(
    theme=rx.theme(
        appearance="dark", 
        has_background=True, 
        accent_color="cyan",
        gray_color="slate"
    )
)
app.add_page(index)
