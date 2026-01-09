#!/bin/bash

# Test 1: Login as DK_ADMIN
echo "=== Test 1: Login as DK_ADMIN (sri.mulyana) ==="
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=sri.mulyana&password=password123")

echo "$LOGIN_RESPONSE" | python3 -m json.tool

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  
  echo -e "\n=== Test 2: Update Order Status with DK_ADMIN token ==="
  curl -s -X PUT http://localhost:8000/api/orders/29035ce8-2b7d-4673-b2b9-2e76a9a4cb02/status \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status": "PROCESSING"}' | python3 -m json.tool
else
  echo "Login failed - trying with different credentials"
fi

echo -e "\n=== Test 3: Login as CLIENT_ADMIN (joko.prasetyo) ==="
LOGIN_RESPONSE_CLIENT=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=joko.prasetyo&password=password123")

echo "$LOGIN_RESPONSE_CLIENT" | python3 -m json.tool

if echo "$LOGIN_RESPONSE_CLIENT" | grep -q "access_token"; then
  TOKEN_CLIENT=$(echo "$LOGIN_RESPONSE_CLIENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  
  echo -e "\n=== Test 4: Try to Update Order Status with CLIENT_ADMIN token (should fail) ==="
  curl -s -X PUT http://localhost:8000/api/orders/29035ce8-2b7d-4673-b2b9-2e76a9a4cb02/status \
    -H "Authorization: Bearer $TOKEN_CLIENT" \
    -H "Content-Type: application/json" \
    -d '{"status": "PROCESSING"}' | python3 -m json.tool
fi
