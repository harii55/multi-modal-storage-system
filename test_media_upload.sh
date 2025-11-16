#!/bin/bash

# Enhanced Testing Script for Multi-Modal Storage System
# Tests folder organization by user and MIME type

echo "🚀 Multi-Modal Storage System - Enhanced Testing"
echo "=================================================="

USER_ID="usr_67f8a1c9"
BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}Creating test files...${NC}"

# Create test directory
mkdir -p test_files/sample_files

# 1. Create sample image
echo "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9Qz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC" | base64 -d > test_files/sample_files/test_image.png

# 2. Create sample document
cat > test_files/sample_files/test_document.txt << 'EOF'
This is a test document for the multi-modal storage system.
It should be categorized under 'documents' folder.
EOF

# 3. Create sample markdown
cat > test_files/sample_files/README.md << 'EOF'
# Test Markdown File
This file tests document categorization.
EOF

# 4. Create sample CSV
cat > test_files/sample_files/data.csv << 'EOF'
id,name,value
1,Test,100
2,Sample,200
EOF

# 5. Create a ZIP archive with multiple files
cd test_files/sample_files
zip -q test_archive.zip test_image.png test_document.txt README.md data.csv
cd ../..

echo -e "${GREEN}✅ Test files created${NC}\n"

# Test 1: Upload Image
echo -e "${BLUE}Test 1: Uploading Image (should go to images folder)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/test_image.png" \
  -F "user_id=$USER_ID" | jq '.'
echo ""

# Test 2: Upload Document
echo -e "${BLUE}Test 2: Uploading Text Document (should go to documents folder)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/test_document.txt" \
  -F "user_id=$USER_ID" | jq '.'
echo ""

# Test 3: Upload Markdown
echo -e "${BLUE}Test 3: Uploading Markdown (should go to documents folder)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/README.md" \
  -F "user_id=$USER_ID" | jq '.'
echo ""

# Test 4: Upload CSV
echo -e "${BLUE}Test 4: Uploading CSV (should go to documents folder)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/data.csv" \
  -F "user_id=$USER_ID" | jq '.'
echo ""

# Test 5: Upload ZIP Archive (should extract and categorize)
echo -e "${BLUE}Test 5: Uploading ZIP Archive (should extract and categorize each file)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/test_archive.zip" \
  -F "user_id=$USER_ID" | jq '.'
echo ""

# Test 6: Upload without user_id (should use 'anonymous')
echo -e "${BLUE}Test 6: Uploading without user_id (should use 'anonymous' folder)${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/test_image.png" | jq '.'
echo ""

# Test 7: Different user
echo -e "${BLUE}Test 7: Uploading with different user_id${NC}"
curl -s -X POST "$BASE_URL/v1/upload" \
  -F "file=@test_files/sample_files/test_document.txt" \
  -F "user_id=usr_12345" | jq '.'
echo ""

echo -e "\n${GREEN}✅ All media tests completed!${NC}"
echo -e "${YELLOW}Expected MinIO folder structure:${NC}"
echo "user-uploads/"
echo "  └── users/"
echo "      ├── $USER_ID/"
echo "      │   ├── images/"
echo "      │   │   └── {uuid}_test_image.png"
echo "      │   └── documents/"
echo "      │       ├── {uuid}_test_document.txt"
echo "      │       ├── {uuid}_README.md"
echo "      │       └── {uuid}_data.csv"
echo "      ├── anonymous/"
echo "      │   └── images/"
echo "      │       └── {uuid}_test_image.png"
echo "      └── usr_12345/"
echo "          └── documents/"
echo "              └── {uuid}_test_document.txt"
