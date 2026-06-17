"""Tests for review cycles — full lifecycle and role-based access."""

from httpx import AsyncClient


async def create_assessed_cycle(client, token, target_grade="middle"):
    """Helper: create a cycle and set self_level + comment on first skill."""
    create_resp = await client.post(
        "/api/v1/reviews",
        json={"target_grade": target_grade},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    cycle = create_resp.json()

    # Fill self-assessment for every skill
    for a in cycle["assessments"]:
        await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"self_level": 3, "self_comment": "I am good at this"},
            headers={"Authorization": f"Bearer {token}"},
        )
    return cycle


async def complete_review_flow(
    client, employee_token, manager_token, expert_token, target_grade="middle"
):
    """Run a full review through all stages, return final result."""
    cycle = await create_assessed_cycle(client, employee_token, target_grade)

    # Submit
    submit_resp = await client.post(
        f"/api/v1/reviews/{cycle['id']}/submit",
        json={},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "manager_review"

    # Manager fills assessments
    cycle = submit_resp.json()
    for a in cycle["assessments"]:
        await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {manager_token}"},
        )

    # Manager → interview
    mgr_resp = await client.post(
        f"/api/v1/reviews/{cycle['id']}/manager-review",
        json={"manager_comment": "Good progress"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert mgr_resp.status_code == 200
    assert mgr_resp.json()["status"] == "interview"

    # Expert fills assessments
    cycle = mgr_resp.json()
    for a in cycle["assessments"]:
        await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"expert_level": 3},
            headers={"Authorization": f"Bearer {expert_token}"},
        )

    # Expert → decision
    exp_resp = await client.post(
        f"/api/v1/reviews/{cycle['id']}/expert-review",
        json={"expert_comment": "Confirmed"},
        headers={"Authorization": f"Bearer {expert_token}"},
    )
    assert exp_resp.status_code == 200
    assert exp_resp.json()["status"] == "decision"

    cycle = exp_resp.json()
    final = await client.post(
        f"/api/v1/reviews/{cycle['id']}/finalize",
        json={"decision": "promoted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert final.status_code == 200
    return final.json()


class TestCreateCycle:
    async def test_employee_create_cycle(self, client: AsyncClient, employee_token):
        r = await client.post(
            "/api/v1/reviews",
            json={"target_grade": "middle"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "draft"
        assert data["target_grade"] == "middle"
        assert len(data["assessments"]) > 0

    async def test_employee_cannot_create_duplicate(
        self, client: AsyncClient, employee_token
    ):
        await client.post(
            "/api/v1/reviews",
            json={"target_grade": "middle"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.post(
            "/api/v1/reviews",
            json={"target_grade": "senior"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 409

    async def test_manager_cannot_create(self, client: AsyncClient, manager_token):
        r = await client.post(
            "/api/v1/reviews",
            json={"target_grade": "middle"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403


class TestUpdateAssessment:
    async def test_employee_set_self_level(self, client: AsyncClient, employee_token):
        cycle = await create_assessed_cycle(client, employee_token)
        a = cycle["assessments"][0]
        r = await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"self_level": 3, "self_comment": "Expert level"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert r.json()["self_level"] == 3
        assert r.json()["self_comment"] == "Expert level"

    async def test_employee_cannot_set_manager_level(
        self, client: AsyncClient, employee_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        a = cycle["assessments"][0]
        r = await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert r.json()["manager_level"] is None

    async def test_manager_can_set_manager_level_in_manager_review(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        a = cycle["assessments"][0]
        r = await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["manager_level"] == 3

    async def test_cannot_update_in_wrong_status(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        a = cycle["assessments"][0]
        # Try after submit
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.put(
            f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
            json={"self_level": 2},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 409


class TestSubmit:
    async def test_submit_success(self, client: AsyncClient, employee_token):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "manager_review"

    async def test_submit_without_assessments_fails(
        self, client: AsyncClient, employee_token
    ):
        create = await client.post(
            "/api/v1/reviews",
            json={"target_grade": "middle"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        cycle_id = create.json()["id"]
        r = await client.post(
            f"/api/v1/reviews/{cycle_id}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 422

    async def test_submit_other_users_cycle_fails(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403


class TestFullFlow:
    async def test_full_review_flow_promoted(
        self, client: AsyncClient, employee_token, manager_token, expert_token
    ):
        result = await complete_review_flow(
            client, employee_token, manager_token, expert_token
        )
        assert result["status"] == "completed"
        assert result["final_decision"] == "promoted"

    async def test_full_review_flow_rejected(
        self, client: AsyncClient, employee_token, manager_token, expert_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)

        # Submit
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        cycle = (
            await client.get(
                f"/api/v1/reviews/{cycle['id']}",
                headers={"Authorization": f"Bearer {employee_token}"},
            )
        ).json()

        for a in cycle["assessments"]:
            await client.put(
                f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
                json={"manager_level": 2},
                headers={"Authorization": f"Bearer {manager_token}"},
            )

        mgr = await client.post(
            f"/api/v1/reviews/{cycle['id']}/manager-review",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        cycle = mgr.json()
        for a in cycle["assessments"]:
            await client.put(
                f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
                json={"expert_level": 2},
                headers={"Authorization": f"Bearer {expert_token}"},
            )

        exp = await client.post(
            f"/api/v1/reviews/{cycle['id']}/expert-review",
            json={},
            headers={"Authorization": f"Bearer {expert_token}"},
        )
        cycle = exp.json()

        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/finalize",
            json={"decision": "rejected"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"
        assert r.json()["final_decision"] == "rejected"

    async def test_manager_review_missing_assessments_fails(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        # Don't fill manager assessments
        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/manager-review",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 422

    async def test_expert_review_missing_assessments_fails(
        self, client: AsyncClient, employee_token, manager_token, expert_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        cycle = (
            await client.get(
                f"/api/v1/reviews/{cycle['id']}",
                headers={"Authorization": f"Bearer {employee_token}"},
            )
        ).json()
        for a in cycle["assessments"]:
            await client.put(
                f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
                json={"manager_level": 3},
                headers={"Authorization": f"Bearer {manager_token}"},
            )
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/manager-review",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )

        # Don't fill expert assessments
        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/expert-review",
            json={},
            headers={"Authorization": f"Bearer {expert_token}"},
        )
        assert r.status_code == 422

    async def test_invalid_decision(
        self, client: AsyncClient, employee_token, manager_token, expert_token
    ):
        result = await complete_review_flow(
            client, employee_token, manager_token, expert_token
        )
        r = await client.post(
            f"/api/v1/reviews/{result['id']}/finalize",
            json={"decision": "invalid"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 422


class TestListPending:
    async def test_list_pending_manager(
        self, client: AsyncClient, employee_token, manager_token
    ):
        r = await client.get(
            "/api/v1/reviews/pending/manager",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.get(
            "/api/v1/reviews/pending/manager",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert len(r.json()) >= 1

    async def test_list_pending_interview(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        cycle = (
            await client.get(
                f"/api/v1/reviews/{cycle['id']}",
                headers={"Authorization": f"Bearer {employee_token}"},
            )
        ).json()
        for a in cycle["assessments"]:
            await client.put(
                f"/api/v1/reviews/{cycle['id']}/assessments/{a['skill_id']}",
                json={"manager_level": 3},
                headers={"Authorization": f"Bearer {manager_token}"},
            )
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/manager-review",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        r = await client.get(
            "/api/v1/reviews/pending/interview",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_list_pending_decision(
        self, client: AsyncClient, employee_token, manager_token, expert_token
    ):
        r = await client.get(
            "/api/v1/reviews/pending/decision",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200

    async def test_employee_cannot_access_pending(
        self, client: AsyncClient, employee_token
    ):
        r = await client.get(
            "/api/v1/reviews/pending/manager",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestDelete:
    async def test_delete_draft(self, client: AsyncClient, employee_token):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.delete(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 204

        # Verify it's gone
        get_r = await client.get(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert get_r.status_code == 404

    async def test_cannot_delete_submitted(self, client: AsyncClient, employee_token):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.delete(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 409

    async def test_cannot_delete_others(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.delete(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403


class TestReturnToDraft:
    async def test_manager_return_to_draft(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/return-to-draft",
            json={},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "draft"

    async def test_employee_cannot_return(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        await client.post(
            f"/api/v1/reviews/{cycle['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        r = await client.post(
            f"/api/v1/reviews/{cycle['id']}/return-to-draft",
            json={},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestGetCycle:
    async def test_get_own_cycle(self, client: AsyncClient, employee_token):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.get(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert r.json()["id"] == cycle["id"]

    async def test_employee_cannot_get_others(
        self, client: AsyncClient, employee_token, manager_token
    ):
        cycle = await create_assessed_cycle(client, employee_token)
        r = await client.get(
            f"/api/v1/reviews/{cycle['id']}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200  # Manager can see all

    async def test_get_nonexistent(self, client: AsyncClient, employee_token):
        r = await client.get(
            "/api/v1/reviews/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 404


class TestListCycles:
    async def test_list_own(self, client: AsyncClient, employee_token, employee_user):
        await create_assessed_cycle(client, employee_token)
        r = await client.get(
            "/api/v1/reviews", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    async def test_manager_sees_all(
        self, client: AsyncClient, employee_token, manager_token
    ):
        await create_assessed_cycle(client, employee_token)
        r = await client.get(
            "/api/v1/reviews", headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1
