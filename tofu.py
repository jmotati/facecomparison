# imports
import requests
import base64
import json

# api keys: 
API_KEY = "d45fd466-51e2-4701-8da8-04351c872236"
API_SECRET = "171e8465-f548-401d-b63b-caf0dc28df5f"

def upload_image_file_form(image_path, detection_flags=None):
    """
    Uploads an image to the Betaface API using the /v2/media/file endpoint.
    Sends API key as a form field instead of a header.
    
    Args:
        image_path (str): Path to the image file to upload
        detection_flags (list, optional): List of detection flags
    
    Returns:
        dict: The JSON response from the API
    """
    base_url = "https://www.betafaceapi.com/api"
    endpoint = "/v2/media/file"
    
    headers = {
        "accept": "application/json"
    }
    
    # Prepare the files and data for multipart upload
    files = {
        'file': (image_path.split("\\")[-1], open(image_path, 'rb'), 'image/jpeg')
    }
    
    # Include the API key in the form data
    data = {
        "api_key": API_KEY
    }
    
    # Add detection flags if provided
    if detection_flags:
        data["detection_flags"] = json.dumps(detection_flags)
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            headers=headers,
            files=files,
            data=data
        )
        
        # Print response details for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text[:200]}...")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    finally:
        # Make sure to close the file
        files['file'][1].close()

def extract_uuids(response_json):
    """
    Extracts face_uuid and media_uuid from the Betaface API response.
    
    Args:
        response_json (dict): The JSON response from the Betaface API
        
    Returns:
        dict: A dictionary containing:
            - media_uuid: The UUID of the uploaded media
            - face_uuids: A list of UUIDs for all detected faces
            - first_face_uuid: The UUID of the first detected face (if any)
    """
    result = {
        "media_uuid": None,
        "face_uuids": [],
        "first_face_uuid": None
    }
    
    # Check if we have a valid response
    if not response_json or not isinstance(response_json, dict):
        print("Invalid response format")
        return result
    
    # Extract media_uuid
    if "media" in response_json and "media_uuid" in response_json["media"]:
        result["media_uuid"] = response_json["media"]["media_uuid"]
    
    # Extract face_uuid(s)
    if "media" in response_json and "faces" in response_json["media"]:
        faces = response_json["media"]["faces"]
        if faces and isinstance(faces, list):
            result["face_uuids"] = [face["face_uuid"] for face in faces if "face_uuid" in face]
            
            # Get the first face_uuid if available
            if result["face_uuids"]:
                result["first_face_uuid"] = result["face_uuids"][0]
    
    return result

def upload_multiple_images(image_paths, detection_flags=None):
    """
    Uploads multiple images to the Betaface API using the /v2/media/file endpoint.
    
    Args:
        image_paths (list): List of paths to the image files to upload
        detection_flags (list, optional): List of detection flags
    
    Returns:
        list: A list of dictionaries containing the results for each image
    """
    results = []
    
    for image_path in image_paths:
        print(f"\nUploading image: {image_path}")
        
        # Upload the image using the form method (which works)
        result = upload_image_file_form(image_path, detection_flags)
        
        if result:
            # Extract UUIDs
            uuids = extract_uuids(result)
            
            # Print the extracted UUIDs
            print(f"Media UUID: {uuids['media_uuid']}")
            
            if uuids['first_face_uuid']:
                print(f"First Face UUID: {uuids['first_face_uuid']}")
                print(f"Total faces detected: {len(uuids['face_uuids'])}")
            else:
                print("No faces detected in the image")
            
            # Add result to the list
            results.append({
                'image_path': image_path,
                'api_response': result,
                'uuids': uuids
            })
        else:
            print(f"Failed to upload image: {image_path}")
            results.append({
                'image_path': image_path,
                'api_response': None,
                'uuids': None
            })
    
    return results

def recognize_faces(source_face_uuid, target_face_uuids):
    """
    Compare a face against target faces using the /v2/recognize endpoint.
    Uses the API key in the request body, consistent with other successful API calls.
    
    Args:
        source_face_uuid (str): UUID of the source face to compare
        target_face_uuids (list): List of target face UUIDs to compare against
        
    Returns:
        dict: The recognition results with match scores
    """
    base_url = "https://www.betafaceapi.com/api"
    endpoint = "/v2/recognize"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload according to the API documentation
    payload = {
        "api_key": API_KEY,
        "faces_uuids": [source_face_uuid],  # List of faces to be recognized
        "targets": target_face_uuids,       # List of target faces to compare against
        "parameters": "min_match_score:0.4" # Optional parameters
    }
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Print response details for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text[:200]}...")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making recognition request: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Define image paths
    image_paths = [
        "C:\\Users\\MOTATJX\\Downloads\\Aaron-Creeley-2306841.jpg",
        "C:\\Users\\MOTATJX\\Downloads\\test copy.png"
    ]
    
    # Upload all images
    results = upload_multiple_images(image_paths, detection_flags=["gender", "age"])
    
    # Print summary
    print("\n--- SUMMARY ---")
    for i, result in enumerate(results):
        filename = result['image_path'].split('\\')[-1]
        print(f"\nImage {i+1}: {filename}")
        if result['uuids'] and result['uuids']['media_uuid']:
            print(f"  Status: Success")
            print(f"  Media UUID: {result['uuids']['media_uuid']}")
            print(f"  Faces detected: {len(result['uuids']['face_uuids'])}")
        else:
            print(f"  Status: Failed")
    
    # Collect all face UUIDs from the results
    face_uuids = []
    for result in results:
        if result['uuids'] and result['uuids']['face_uuids']:
            face_uuids.extend(result['uuids']['face_uuids'])
    
    # Perform face comparison if we have at least 2 faces
    if len(face_uuids) >= 2:
        print("\n--- FACE COMPARISON ---")
        print(f"Comparing face {face_uuids[0]} with {len(face_uuids)-1} other face(s)")
        
        # Use the first face as source, compare with all other faces
        comparison_result = recognize_faces(face_uuids[0], face_uuids[1:])
        
        # Process and display the comparison results
        if comparison_result and 'results' in comparison_result:
            print("\nComparison results:")
            
            # Print the full response in a nicely formatted JSON
            print("Full response:")
            print(json.dumps(comparison_result, indent=4))
        else:
            print("Face comparison failed or returned no results")
    else:
        print("\nNot enough faces detected for comparison. Need at least 2 faces.")

