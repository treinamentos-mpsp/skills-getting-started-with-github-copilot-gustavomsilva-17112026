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
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details(client):
    # Arrange
    activity = "Empty Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    details = response.json()[activity]
    assert details["participants"] == []
    assert details["max_participants"] == 1


def test_signup_adds_participant(client):
    # Arrange
    activity = "Empty Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert client.get("/activities").json()[activity]["participants"] == [email]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "member@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()[activity]["participants"] == [email]


def test_signup_rejects_full_activity(client):
    # Arrange
    activity = "Full Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert client.get("/activities").json()[activity]["participants"] == [
        "full@mergington.edu"
    ]


def test_remove_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "member@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity}"}
    assert client.get("/activities").json()[activity]["participants"] == []


def test_remove_participant_returns_404_for_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"
    email = "member@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_returns_404_when_not_signed_up(client):
    # Arrange
    activity = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
