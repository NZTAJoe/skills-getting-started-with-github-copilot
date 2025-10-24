from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.url.path == "/static/index.html"

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Test that we get a dictionary of activities
    assert isinstance(activities, dict)
    
    # Test that each activity has the required fields
    for activity_name, activity in activities.items():
        assert isinstance(activity_name, str)
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

def test_signup_for_activity():
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # Try signing up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]
    
    # Try signing up again (should fail)
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_nonexistent_activity():
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_unregister_from_activity():
    # First, sign up a participant
    activity_name = "Programming Class"
    email = "test_unregister@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Now unregister them
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify they were removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity_name]["participants"]
    
    # Try unregistering again (should fail)
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]

def test_activity_capacity():
    activity_name = "Chess Club"
    base_email = "capacity_test{}@mergington.edu"
    
    # Get current number of participants
    activities_response = client.get("/activities")
    activities = activities_response.json()
    current_participants = len(activities[activity_name]["participants"])
    max_participants = activities[activity_name]["max_participants"]
    
    # Fill up the remaining spots
    for i in range(current_participants, max_participants):
        email = base_email.format(i)
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to add one more participant (should fail)
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"]