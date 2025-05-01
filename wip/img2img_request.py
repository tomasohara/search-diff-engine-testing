import requests
import json
import base64
import os
from pathlib import Path

# === CONFIGURATION ===
VASTAI_BASE_URL = "http://58.79.62.172:58779"  # Base URL
TOKEN = "121db4022dee58bdd8628db2b0c56b8d57f73753f5a6ca07c74f3af242dbcad2"  # Token from the portal URL

# API endpoints
API_URL_WITH_TOKEN = lambda path: f"{VASTAI_BASE_URL}{path}?token={TOKEN}"
IMG2IMG_URL = API_URL_WITH_TOKEN("/sdapi/v1/img2img")
MODELS_URL = API_URL_WITH_TOKEN("/sdapi/v1/sd-models")
OPTIONS_URL = API_URL_WITH_TOKEN("/sdapi/v1/options")

# Model to use (set this to the safetensors model you want)
# This will be updated with available models from the server
MODEL_TO_USE = "v1-5-pruned-emaonly.safetensors"  # Example model name, will be updated with actual available models

SD_HEADER = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

# === PRESET PARAMETERS ===
PARAMS = {
    "prompt": "ink sketch, 2d, handdrawn, (a pug looking at the camera, curious)",
    "negative_prompt": "blurry, low resolution, 3d, color",
    "denoising_strength": 0.75,
    "cfg_scale": 7.0,
    "steps": 30,
    "sampler_name": "Euler a",
    "width": 512,
    "height": 512,
    "batch_size": 1,
}

# Function to encode image to base64
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        raise

# Function to get available models
def get_available_models():
    try:
        print("Fetching available models...")
        response = requests.get(MODELS_URL, headers=SD_HEADER, timeout=30)
        
        if response.status_code == 200:
            models = response.json()
            print(f"Found {len(models)} models:")
            for i, model in enumerate(models):
                print(f"{i+1}. {model['title']} ({model['model_name']})")
            return models
        else:
            print(f"Error fetching models: {response.status_code} {response.text}")
            return []
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return []

# Function to set the active model
def set_model(model_name):
    try:
        print(f"Setting model to: {model_name}")
        payload = {
            "sd_model_checkpoint": model_name
        }
        response = requests.post(OPTIONS_URL, json=payload, headers=SD_HEADER, timeout=30)
        
        if response.status_code == 200:
            print(f"Model successfully set to {model_name}")
            return True
        else:
            print(f"Error setting model: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Error setting model: {str(e)}")
        return False

def run_img2img(image_path):
    try:
        # Check if file exists
        if not os.path.isfile(image_path):
            print(f"Error: Input image file not found: {image_path}")
            return False
            
        # Encode image to base64
        b64_image = encode_image_to_base64(image_path)
        
        # Prepare request payload
        payload = PARAMS.copy()
        payload["init_images"] = [b64_image]
        
        # Send request with token in URL
        print(f"Sending img2img request...")
        response = requests.post(
            IMG2IMG_URL,
            json=payload, 
            headers=SD_HEADER,
            timeout=120  # Longer timeout for image generation
        )
        
        # Add some debugging info
        print(f"Response status code: {response.status_code}")
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            if "images" in result and result["images"]:
                image_data = result["images"][0]
                # Create output directory if it doesn't exist
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate a unique filename based on the input filename
                input_filename = Path(image_path).stem
                output_path = os.path.join(output_dir, f"{input_filename}_output.png")
                
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_data))
                print(f"Generated image saved to {output_path}")
                return True
            else:
                print("Error: No images returned in the response")
                print(f"Response content: {result}")
                return False
        else:
            print("Error:", response.status_code, response.text)
            return False
            
    except Exception as e:
        print(f"An error occurred during img2img: {str(e)}")
        return False

# Check if the server is reachable
def check_server():
    try:
        # Try a GET request to check if the server is up
        check_url = API_URL_WITH_TOKEN("/sdapi/v1/sd-models")
        response = requests.get(check_url, headers=SD_HEADER, timeout=10)
        
        print(f"Server check status: {response.status_code}")
        if response.status_code == 200:
            print("Server is reachable and accepting requests")
            return True
        else:
            print(f"Server returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Server connection error: {e}")
        return False

def customize_parameters():
    """Allow the user to customize generation parameters"""
    try:
        print("\n=== Customize Parameters (press Enter to keep default) ===")
        
        # Copy the default parameters
        custom_params = PARAMS.copy()
        
        # Get user input for each parameter
        new_prompt = input(f"Prompt [{custom_params['prompt']}]: ")
        if new_prompt:
            custom_params["prompt"] = new_prompt
            
        new_neg_prompt = input(f"Negative prompt [{custom_params['negative_prompt']}]: ")
        if new_neg_prompt:
            custom_params["negative_prompt"] = new_neg_prompt
            
        new_strength = input(f"Denoising strength (0.0-1.0) [{custom_params['denoising_strength']}]: ")
        if new_strength:
            try:
                custom_params["denoising_strength"] = float(new_strength)
            except ValueError:
                print("Invalid value, keeping default")
                
        new_cfg = input(f"CFG scale [{custom_params['cfg_scale']}]: ")
        if new_cfg:
            try:
                custom_params["cfg_scale"] = float(new_cfg)
            except ValueError:
                print("Invalid value, keeping default")
                
        new_steps = input(f"Steps [{custom_params['steps']}]: ")
        if new_steps:
            try:
                custom_params["steps"] = int(new_steps)
            except ValueError:
                print("Invalid value, keeping default")
                
        print(f"Parameters updated: {json.dumps(custom_params, indent=2)}")
        return custom_params
    except Exception as e:
        print(f"Error customizing parameters: {str(e)}")
        return PARAMS  # Return default parameters on error

if __name__ == "__main__":
    print("=== VastAI Stable Diffusion img2img Client ===")
    
    # Check if server is reachable
    if check_server():
        # Get available models
        models = get_available_models()
        
        if models:
            # Let user choose a model
            print("\nChoose a model to use:")
            choice = input("Enter the number of the model (or press Enter for default): ")
            
            if choice and choice.isdigit() and 1 <= int(choice) <= len(models):
                selected_model = models[int(choice)-1]["model_name"]
                print(f"Selected model: {selected_model}")
            else:
                # Use the first model as default if no valid choice
                selected_model = models[0]["model_name"]
                print(f"Using default model: {selected_model}")
            
            # Set the selected model
            if set_model(selected_model):
                # Ask user if they want to customize parameters
                customize = input("\nDo you want to customize the generation parameters? (y/n): ").lower()
                if customize.startswith('y'):
                    PARAMS = customize_parameters()
                
                # Get input image path
                input_image_path = input("\nEnter the path to your input image: ")
                if not input_image_path:
                    input_image_path = "pug.jpg"  # Default image
                    print(f"Using default image: {input_image_path}")
                
                # Check if file exists before proceeding
                if os.path.isfile(input_image_path):
                    run_img2img(input_image_path)
                else:
                    print(f"Error: Input image file not found: {input_image_path}")
        else:
            print("No models available. Please check your Stable Diffusion installation.")
    else:
        print("Server is not reachable. Please check your VastAI instance.")