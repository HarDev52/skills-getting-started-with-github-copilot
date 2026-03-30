"""
Test suite for the Mergington High School API

Tests are organized using the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the functionality being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Fixture to reset activities to known state before each test"""
    # Arrange: Define the initial state
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join the varsity and intramural basketball teams",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        },
        "Tennis Club": {
            "description": "Develop tennis skills and compete in tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        },
        "Drama Club": {
            "description": "Perform in school plays and develop acting skills",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Art Studio": {
            "description": "Explore painting, sculpture, and digital art",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 16,
            "participants": []
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 14,
            "participants": []
        }
    }

    # Clear and reinitialize activities
    activities.clear()
    activities.update(initial_activities)

    yield  # Run the test

    # Cleanup (if needed for additional tests)
    activities.clear()
    activities.update(initial_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html"""
        # Arrange: Client is ready (fixture)

        # Act: Send GET request to root endpoint
        response = client.get("/", follow_redirects=False)

        # Assert: Verify redirect response
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities_returns_list(self, client):
        """Test that GET /activities returns all activities"""
        # Arrange: Client is ready (fixture)
        expected_activities_count = 9

        # Act: Send GET request to retrieve all activities
        response = client.get("/activities")

        # Assert: Verify response and structure
        assert response.status_code == 200
        returned_activities = response.json()
        assert isinstance(returned_activities, dict)
        assert len(returned_activities) == expected_activities_count
        assert "Chess Club" in returned_activities
        assert "Programming Class" in returned_activities

    def test_activity_has_required_fields(self, client):
        """Test that each activity contains required fields"""
        # Arrange: Define expected fields for each activity
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act: Retrieve activities and inspect first one
        response = client.get("/activities")
        activities_data = response.json()
        chess_club = activities_data["Chess Club"]

        # Assert: Verify all required fields are present
        assert set(chess_club.keys()) == expected_fields

    def test_activity_participants_is_list(self, client):
        """Test that participants field is a list"""
        # Arrange: Client is ready

        # Act: Retrieve activities
        response = client.get("/activities")
        activities_data = response.json()

        # Assert: Verify participants is a list for all activities
        for activity_name, activity_info in activities_data.items():
            assert isinstance(activity_info["participants"], list)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_available_activity_succeeds(self, client):
        """Test successful signup for an activity with available spots"""
        # Arrange: Prepare activity and student data
        activity_name = "Basketball Team"
        student_email = "new_student@mergington.edu"

        # Act: Sign up student for activity
        response = client.post(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify successful signup
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {student_email} for {activity_name}"
        assert student_email in activities[activity_name]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test signup for non-existent activity returns 404"""
        # Arrange: Prepare invalid activity and student data
        activity_name = "Nonexistent Activity"
        student_email = "student@mergington.edu"

        # Act: Attempt to sign up for non-existent activity
        response = client.post(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify 404 error response
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup_returns_400(self, client):
        """Test that signing up twice for the same activity returns 400"""
        # Arrange: Student already signed up for Chess Club
        activity_name = "Chess Club"
        student_email = "michael@mergington.edu"  # Already in participants

        # Act: Attempt to sign up again for the same activity
        response = client.post(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify 400 error response
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_adds_student_to_participants(self, client):
        """Test that signup correctly adds student to activity participants"""
        # Arrange: Get initial participant count and new student email
        activity_name = "Drama Club"
        student_email = "test_student@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act: Sign up student
        client.post(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify student was added
        updated_count = len(activities[activity_name]["participants"])
        assert updated_count == initial_count + 1
        assert student_email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_from_activity_succeeds(self, client):
        """Test successful unregistration from an activity"""
        # Arrange: Student is currently signed up for Chess Club
        activity_name = "Chess Club"
        student_email = "michael@mergington.edu"

        # Act: Unregister student from activity
        response = client.delete(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify successful unregistration
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {student_email} from {activity_name}"
        assert student_email not in activities[activity_name]["participants"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test unregistration from non-existent activity returns 404"""
        # Arrange: Prepare invalid activity and student data
        activity_name = "Nonexistent Activity"
        student_email = "student@mergington.edu"

        # Act: Attempt to unregister from non-existent activity
        response = client.delete(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify 404 error response
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_400(self, client):
        """Test unregistration when not signed up returns 400"""
        # Arrange: Student is not signed up for Tennis Club
        activity_name = "Tennis Club"
        student_email = "not_signed_up@mergington.edu"

        # Act: Attempt to unregister student who isn't signed up
        response = client.delete(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify 400 error response
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister correctly removes student from participants"""
        # Arrange: Student is signed up for Programming Class
        activity_name = "Programming Class"
        student_email = "emma@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act: Unregister student
        client.delete(f"/activities/{activity_name}/signup?email={student_email}")

        # Assert: Verify student was removed
        updated_count = len(activities[activity_name]["participants"])
        assert updated_count == initial_count - 1
        assert student_email not in activities[activity_name]["participants"]