import pytest
import reflex as rx
from reflex_app.preconsult.preconsult import header, stepper_component, step_2_history, admin_dashboard
from reflex_app.preconsult.state import State

def test_header_rendering():
    comp = header()
    assert isinstance(comp, rx.Component)
    assert comp is not None

def test_stepper_component_rendering():
    comp = stepper_component()
    assert isinstance(comp, rx.Component)
    assert comp is not None

def test_step_2_history_rendering():
    comp = step_2_history()
    assert isinstance(comp, rx.Component)
    assert comp is not None

def test_admin_dashboard_rendering():
    comp = admin_dashboard()
    assert isinstance(comp, rx.Component)
    assert comp is not None

def test_state_step_progress():
    state = State()
    state.step = 0
    assert state.step_progress == 16  # int(1/6 * 100) = 16
    
    state.step = 5
    assert state.step_progress == 100
