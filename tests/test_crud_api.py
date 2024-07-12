import time


def test_root(test_client):
    response = test_client.get('/api/healthchecker')
    assert response.status_code == 200
    assert response.json() == {'message': 'The API is LIVE!!'}


def test_create_get_user(test_client, user_payload):
    response = test_client.post('/api/users', json=user_payload)
    assert response.status_code == 201

    response = test_client.get(f'/api/users/{user_payload["id"]}')
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['status'] == 'Success'
    assert response_json['user']['id'] == user_payload['id']
    assert response_json['user']['first_name'] == 'John'
    assert response_json['user']['last_name'] == 'Doe'


def test_create_update_user(test_client, user_payload, user_payload_update):
    response = test_client.post('/api/users', json=user_payload)
    assert response.status_code == 201

    # Update the created user
    time.sleep(
        1
    )

    response = test_client.patch(
        f'/api/users/{user_payload["id"]}', json=user_payload_update
    )

    response_json = response.json()
    assert response.status_code == 202
    assert response_json['status'] == 'Success'
    assert response_json['user']['id'] == user_payload['id']
    assert response_json['user']['first_name'] == 'Jane'
    assert response_json['user']['last_name'] == 'Doe'
    assert response_json['user']['activated'] is True
    assert (
            response_json['user']['updatedAt'] is not None
            and response_json['user']['updatedAt'] > response_json['user']['createdAt']
    )


def test_update_user_wrong_payload(test_client, user_id, user_payload_update):
    user_payload_update['first_name'] = True
    # first_name should be a str not a boolean

    response = test_client.patch(f'/api/users/{user_id}', json=user_payload_update)
    assert response.status_code == 422
    response_json = response.json()
    assert response_json == {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['body', 'first_name'],
                'msg': 'Input should be a valid string',
                'input': True,
            }
        ]
    }


def test_create_delete_user(test_client, user_payload):
    response = test_client.post('/api/users', json=user_payload)
    assert response.status_code == 201

    # Delete the created user
    response = test_client.delete(f'/api/users/{user_payload["id"]}')
    response_json = response.json()
    assert response.status_code == 202
    assert response_json['status'] == 'Success'
    assert response_json['message'] == "User deleted successfully"

    # Get the deleted user
    response = test_client.get(f'/api/users/{user_payload["id"]}')
    assert response.status_code == 404
    assert response_json['status'] == 'Success'
    assert response_json['message'] == 'User deleted successfully'


def test_get_user_not_found(test_client, user_id):
    response = test_client.get(f'/api/users/{user_id}')
    assert response.status_code == 404
    response_json = response.json()
    assert response_json['detail'] == f'No User with this id: {user_id} found'


def test_create_user_wrong_payload(test_client):
    response = test_client.post('/api/users', json={})
    assert response.status_code == 422


def test_update_user_doesnt_exist(test_client, user_id, user_payload_update):
    response = test_client.patch(f'/api/users/{user_id}', json=user_payload_update)
    assert response.status_code == 404
    response_json = response.json()
    assert response_json['detail'] == f'No User with this id: {user_id} found'
