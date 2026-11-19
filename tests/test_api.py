import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["member@mergington.edu"],
        },
        "Empty Club": {
            "description": "A club with open spots",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": [],
        },
        "Full Club": {
            "description": "A full club",
            "schedule": "Tuesdays",
            "max_participants": 1,
            "participants": ["full@mergington.edu"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Empty Club"]["participants"] == []
    assert response.json()["Empty Club"]["max_participants"] == 1


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Empty Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@mergington.edu for Empty Club"
    }
    activities_response = client.get("/activities")
    assert activities_response.json()["Empty Club"]["participants"] == [
        "new@mergington.edu"
    ]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "member@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "member@mergington.edu"
    ]


def test_signup_rejects_full_activity(client):
    response = client.post(
        "/activities/Full Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert client.get("/activities").json()["Full Club"]["participants"] == [
        "full@mergington.edu"
    ]


def test_remove_participant(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "member@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed member@mergington.edu from Chess Club"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == []


def test_remove_participant_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "member@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_returns_404_when_not_signed_up(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
