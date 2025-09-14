import requests
import json

BASE_URL = 'http://localhost:8585/api'

def test_workflow():
    # 1. Login as user1
    print("1. Login as user1...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'bob',
        'password': 'bob'
    })
    user1_token = response.json()['access']
    
    # 2. Create document
    print("2. Creating document...")
    headers = {'Authorization': f'Bearer {user1_token}'}
    response = requests.post(f'{BASE_URL}/documents/', headers=headers, json={})
    document_id = response.json()['id']
    print(f"Document created with ID: {document_id}")
    
    # 3. User1 fills fields 1-4
    print("3. User1 filling fields 1-4...")
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field1': 'Data 1',
            'field2': 'Data 2',
            'field3': 'Data 3',
            'field4': 'Data 4'
        }
    )
    print("Fields 1-4 filled")
    
    # 4. Login as user2
    print("4. Login as user2...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'user2',
        'password': 'password123'
    })
    user2_token = response.json()['access']
    
    # 5. User2 fills fields 5-8
    print("5. User2 filling fields 5-8...")
    headers = {'Authorization': f'Bearer {user2_token}'}
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field5': 'Data 5',
            'field6': 'Data 6',
            'field7': 'Data 7',
            'field8': 'Data 8'
        }
    )
    print("Fields 5-8 filled")
    
    # 6. Login as user3
    print("6. Login as user3...")
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'user3',
        'password': 'password123'
    })
    user3_token = response.json()['access']
    
    # 7. User3 fills fields 9-11
    print("7. User3 filling fields 9-11...")
    headers = {'Authorization': f'Bearer {user3_token}'}
    response = requests.patch(
        f'{BASE_URL}/documents/{document_id}/',
        headers=headers,
        json={
            'field9': 'Data 9',
            'field10': 'Data 10',
            'field11': 'Data 11'
        }
    )
    print("Fields 9-11 filled - Document moved to approval stage")
    
    # 8. User1 approves
    print("8. User1 approving...")
    headers = {'Authorization': f'Bearer {user1_token}'}
    response = requests.post(
        f'{BASE_URL}/documents/{document_id}/approve/',
        headers=headers,
        json={
            'action': 'approve',
            'comments': 'Looks good from my side'
        }
    )
    print("User1 approved")
    
    # Continue with other approvals...
    print("\nWorkflow test completed!")
    print(f"Check document status at: {BASE_URL}/documents/{document_id}/status/")

if __name__ == '__main__':
    test_workflow()