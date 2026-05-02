import reflex as rx
from .state import State
try:
    from securemed_chat.api.endpoints import router as api_router
except ImportError:
    api_router = None


def header() -> rx.Component:
    return rx.hstack(
        rx.heading(State.t["title"], size={"initial": "6", "sm": "7"}, color_scheme="cyan"),
        rx.spacer(),
        rx.color_mode.button(),
        width="100%",
        padding={"initial": "1em", "sm": "1.5em"},
        border_bottom="1px solid rgba(255,255,255,0.1)",
    )

def step_0_demographics() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["intake"], size={"initial": "6", "sm": "7", "md": "8"}, margin_bottom="0.5em"),
            rx.text(State.t["intake_desc"], color_scheme="gray"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.vstack(
            rx.text(State.t["age"], weight="bold"),
            rx.hstack(
                *[rx.button(bracket, on_click=State.set_age_bracket(bracket),
                            variant=rx.cond(State.age_bracket == bracket, "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for bracket in ["18-25", "26-35", "36-45", "46-60", "60+"]],
                wrap="wrap", spacing="2"
            ),
            rx.text(State.t["gender"], weight="bold"),
            rx.select(
                State.gender_opts,
                placeholder=State.t["gender_ph"],
                on_change=State.set_gender,
                value=State.gender,
                width="100%",
                min_height="44px",
                aria_label="Select your gender"
            ),
            spacing="4",
            width="100%",
            padding_y="1em",
            animation="fadeInUp 0.4s ease-out 0.1s both"
        ),
        rx.button(
            State.t["start_btn"], 
            on_click=State.go_to_step_1, 
            color_scheme="cyan",
            size="3",
            width="100%",
            min_height="44px",
            _hover={"transform": "scale(1.02)", "bg": "cyan.600"},
            transition="all 0.2s ease",
            animation="fadeInUp 0.4s ease-out 0.2s both"
        ),
        width="100%",
        spacing="5"
    )

def step_1_chief_complaint() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["step_1"], size={"initial": "6", "sm": "7"}),
            rx.text(State.t["step_1_desc"], color_scheme="gray"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.vstack(
            rx.text(State.t["specialist"], weight="bold"),
            rx.input(
                placeholder=State.t["specialist_ph"],
                on_change=State.set_specialist,
                value=State.specialist,
                width="100%",
                min_height="44px",
                aria_label="Specialist you are seeing"
            ),
            rx.text(State.t["concern"], weight="bold"),
            rx.text_area(
                placeholder=State.t["concern_ph"],
                on_change=State.set_chief_complaint,
                value=State.chief_complaint,
                width="100%",
                height="80px",
                min_height="44px",
                aria_label="Chief Complaint"
            ),
            animation="fadeInUp 0.4s ease-out 0.1s both", spacing="4", width="100%"
        ),
        rx.vstack(
            rx.text(State.t["duration"], weight="bold"),
            rx.hstack(
                *[rx.button(opt, on_click=State.set_duration(opt),
                            variant=rx.cond(State.duration == opt, "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for opt in ["Started today", "A few days", "Weeks", "Months", "Years"]],
                wrap="wrap", spacing="2"
            ),
            rx.text(State.t["complaint_detail"], weight="bold"),
            rx.text_area(
                placeholder=State.t["complaint_detail_ph"],
                on_change=State.set_complaint_detail,
                value=State.complaint_detail,
                width="100%",
                height="80px",
                min_height="44px",
                aria_label="Additional details"
            ),
            animation="fadeInUp 0.4s ease-out 0.2s both", spacing="4", width="100%"
        ),
        rx.button(State.t["start_btn"], on_click=State.go_to_step_2, color_scheme="cyan", size="3", width="100%", min_height="44px", animation="fadeInUp 0.4s ease-out 0.3s both"),
        width="100%", spacing="5"
    )

def step_2_history() -> rx.Component:
    def medication_item(med_idx):
        return rx.hstack(
            rx.input(
                placeholder=State.t["medications_ph"],
                on_change=lambda val: State.update_medication(med_idx, val),
                value=State.medications[med_idx],
                width="100%",
                min_height="44px",
                aria_label="Medication name"
            ),
            rx.button(
                State.t["remove"], 
                on_click=lambda: State.remove_medication(med_idx), 
                color_scheme="red", 
                variant="outline",
                min_height="44px",
                aria_label="Remove medication"
            ),
            width="100%"
        )

    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["step_2"], size={"initial": "6", "sm": "7"}),
            rx.text(State.t["step_2_desc"], color_scheme="gray"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.vstack(
            rx.text(State.t["conditions_label"], weight="bold"),
            rx.hstack(
                *[rx.button(opt, on_click=State.toggle_condition(opt),
                            variant=rx.cond(State.conditions.contains(opt), "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for opt in ["Hypertension", "Diabetes", "Asthma/Bronchitis", "Depression/Anxiety", "Thyroid issues"]],
                wrap="wrap", spacing="2"
            ),
            rx.text(State.t["medications_label"], weight="bold"),
            rx.vstack(
                rx.foreach(State.medications, lambda m, i: medication_item(i)),
                rx.button(State.t["add_medication"], on_click=State.add_medication, variant="ghost", min_height="44px"),
                align_items="start", width="100%"
            ),
            animation="fadeInUp 0.4s ease-out 0.1s both", spacing="4", width="100%"
        ),
        rx.vstack(
            rx.text(State.t["allergies_label"], weight="bold"),
            rx.radio(
                [State.t["allergies_no"], State.t["allergies_yes"]],
                on_change=lambda val: State.set_allergies_flag(val == State.t["allergies_yes"]),
                default_value=State.t["allergies_no"],
                direction="row",
                aria_label="Do you have any drug allergies?"
            ),
            rx.cond(
                State.allergies_flag,
                rx.text_area(
                    placeholder=State.t["allergies_ph"],
                    on_change=State.set_allergies_text,
                    value=State.allergies_text,
                    width="100%",
                    min_height="44px",
                    aria_label="List your drug allergies"
                )
            ),
            animation="fadeInUp 0.4s ease-out 0.2s both", spacing="4", width="100%"
        ),
        rx.button(State.t["start_btn"], on_click=State.go_to_step_3, color_scheme="cyan", size="3", width="100%", min_height="44px", animation="fadeInUp 0.4s ease-out 0.3s both"),
        width="100%", spacing="5"
    )

def step_3_lifestyle() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["step_3"], size={"initial": "6", "sm": "7"}),
            rx.text(State.t["step_3_desc"], color_scheme="gray"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.vstack(
            rx.text(State.t["family_history_label"], weight="bold"),
            rx.hstack(
                *[rx.button(opt, on_click=State.toggle_family_history(opt),
                            variant=rx.cond(State.family_history.contains(opt), "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for opt in ["Cancer", "Heart disease/Heart attack", "Diabetes", "Alzheimer's"]],
                wrap="wrap", spacing="2"
            ),
            animation="fadeInUp 0.4s ease-out 0.1s both", spacing="4", width="100%"
        ),
        rx.vstack(
            rx.text(State.t["smoking_label"], weight="bold"),
            rx.hstack(
                *[rx.button(opt, on_click=State.set_smoking(opt),
                            variant=rx.cond(State.smoking == opt, "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for opt in ["Currently smoke", "Former smoker", "Never smoked"]],
                wrap="wrap", spacing="2"
            ),
            rx.text(State.t["alcohol_label"], weight="bold"),
            rx.hstack(
                *[rx.button(opt, on_click=State.set_alcohol(opt),
                            variant=rx.cond(State.alcohol == opt, "solid", "outline"),
                            padding="0.75em 1em", min_height="44px")
                  for opt in ["Rarely", "Socially", "Frequently", "Never"]],
                wrap="wrap", spacing="2"
            ),
            animation="fadeInUp 0.4s ease-out 0.2s both", spacing="4", width="100%"
        ),
        rx.button(
            State.t["generate_qs_btn"], 
            on_click=State.init_session, 
            loading=State.loading,
            color_scheme="cyan", size="3", width="100%", min_height="44px",
            animation="fadeInUp 0.4s ease-out 0.3s both"
        ),
        width="100%", spacing="5"
    )


def step_4_interview_qs() -> rx.Component:
    def question_item(q, idx):
        return rx.vstack(
            rx.text(q, weight="bold"),
            rx.text_area(
                placeholder=State.t["answers_ph"],
                on_change=lambda val: State.set_answer(idx, val),
                value=State.current_answers[idx],
                width="100%", height="80px", min_height="44px",
                aria_label="Answer for clinical question"
            ),
            width="100%", spacing="2"
        )

    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["step_4"], size={"initial": "6", "sm": "7"}),
            rx.text(State.t["step_4_desc"], color_scheme="gray"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.box(
            rx.cond(
                State.questions.length() > 0,
                rx.vstack(
                    rx.foreach(State.questions, lambda q, i: question_item(q, i)),
                    width="100%"
                ),
                rx.center(rx.spinner(), width="100%", padding="2em")
            ),
            width="100%", animation="fadeInUp 0.4s ease-out 0.1s both"
        ),
        rx.button(
            State.t["submit_continue"], 
            on_click=State.submit_answers, 
            loading=State.loading,
            color_scheme="cyan", size="3", width="100%", min_height="44px",
            animation="fadeInUp 0.4s ease-out 0.2s both"
        ),
        width="100%", spacing="5"
    )

def step_5_summary() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.heading(State.t["complete_title"], size={"initial": "7", "sm": "8"}, text_align="center"),
            rx.text(State.t["complete_desc"], text_align="center"),
            rx.divider(),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0s both"
        ),
        rx.vstack(
            rx.button(
                State.t["download_btn"], 
                on_click=State.download_report,
                loading=State.loading,
                color_scheme="green",
                size="4", width="100%", padding="2em", min_height="44px",
                _hover={"transform": "scale(1.02)"}, transition="all 0.2s ease"
            ),
            rx.button(
                State.t["copy_btn"],
                on_click=rx.set_clipboard(State.summary_text),
                color_scheme="blue",
                variant="outline",
                size="3", width="100%", min_height="44px"
            ),
            rx.button(
                State.t["start_new"], 
                on_click=rx.redirect("/"),
                color_scheme="gray",
                variant="ghost", width="100%", min_height="44px",
                _hover={"transform": "scale(1.02)"}, transition="all 0.2s ease"
            ),
            width="100%", spacing="2", animation="fadeInUp 0.4s ease-out 0.1s both"
        ),
        width="100%", spacing="5", padding_y="2em"
    )

def stepper_component() -> rx.Component:
    def stepper_item(idx: int):
        is_active = State.step == idx
        is_completed = State.step > idx
        
        bg_color = rx.cond(
            is_active, 
            "rgba(0, 200, 255, 0.2)", 
            rx.cond(is_completed, "rgba(0, 200, 255, 0.4)", "transparent")
        )
        border_color = rx.cond(is_active | is_completed, "cyan", "rgba(255,255,255,0.2)")
        
        return rx.hstack(
            rx.center(
                rx.cond(is_completed, rx.icon("check", size=16), rx.text(str(idx + 1))),
                width="30px", height="30px", border_radius="50%", background=bg_color,
                border="2px solid", border_color=border_color,
                color=rx.cond(is_active | is_completed, "cyan", "gray"), font_weight="bold",
            ),
            # Use safe item fetching from step names array
            rx.cond(
                State.step_names.length() > idx,
                rx.text(State.step_names[idx], color=rx.cond(is_active, "white", "gray"), 
                        weight=rx.cond(is_active, "bold", "regular"), display={"initial": "none", "sm": "block"}),
                rx.text("")
            ),
            spacing="2", align_items="center"
        )
        
    return rx.box(
        rx.hstack(
            *[stepper_item(i) for i in range(6)],
            spacing={"initial": "2", "sm": "5"}, justify="center", width="100%", wrap="wrap"
        ),
        padding_bottom="2em", width="100%",
    )

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            header(),
            rx.container(
                stepper_component(),
                rx.card(
                    rx.match(
                        State.step,
                        (0, step_0_demographics()),
                        (1, step_1_chief_complaint()),
                        (2, step_2_history()),
                        (3, step_3_lifestyle()),
                        (4, step_4_interview_qs()),
                        (5, step_5_summary()),
                        step_0_demographics()
                    ),
                    padding={"initial": "1.25em", "sm": "1.5em", "md": "2em"},
                    width="100%",
                    background="rgba(255,255,255,0.05)",
                    backdrop_filter="blur(15px)",
                    border="1px solid rgba(255,255,255,0.1)",
                    border_radius="20px",
                    box_shadow="0 8px 32px 0 rgba(0,0,0,0.37)"
                ),
                max_width={"initial": "95%", "sm": "90%", "md": "600px"},
                padding_top="2em", padding_bottom="5em"
            ),
            width="100%", min_height="100vh",
            background="radial-gradient(circle at top right, #0a192f, #001f3f, #001529)"
        ),
        width="100%"
    )

style = {
    "@keyframes fadeInUp": {
        "from": {"opacity": "0", "transform": "translateY(16px)"},
        "to": {"opacity": "1", "transform": "translateY(0)"}
    },
    "::placeholder": {"color": "rgba(255,255,255,0.6)"}
}

app = rx.App(
    style=style,
    theme=rx.theme(
        appearance="dark", 
        has_background=True, 
        accent_color="cyan",
        gray_color="slate"
    )
)

if api_router:
    from fastapi import FastAPI
    custom_api = FastAPI()
    custom_api.include_router(api_router)
    app._api.mount("/api", custom_api)

app.add_page(index, on_load=State.detect_lang)
