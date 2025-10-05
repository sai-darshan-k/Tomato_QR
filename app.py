from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import base64
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')  # Serve frontend page

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # Get the image from request
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Read image
        input_image = Image.open(file.stream)
        
        # Remove background
        output_image = remove(input_image)
        
        # Convert to base64
        buffered = io.BytesIO()
        output_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/composite-image', methods=['POST'])
def composite_image():
    try:
        data = request.get_json()
        
        # Decode base64 images
        person_data = data['personImage'].split(',')[1]
        background_data = data['backgroundImage'].split(',')[1]
        
        person_image = Image.open(io.BytesIO(base64.b64decode(person_data)))
        background_image = Image.open(io.BytesIO(base64.b64decode(background_data)))
        
        # Resize person to fit background while maintaining aspect ratio
        bg_width, bg_height = background_image.size
        person_width, person_height = person_image.size
        
        # Calculate scaling to fit 80% of background height
        scale = (bg_height * 0.8) / person_height
        new_person_width = int(person_width * scale)
        new_person_height = int(person_height * scale)
        
        person_image = person_image.resize((new_person_width, new_person_height), Image.LANCZOS)
        
        # Center the person on background
        x_offset = (bg_width - new_person_width) // 2
        y_offset = bg_height - new_person_height - 20  # 20px from bottom
        
        # Composite images
        background_image.paste(person_image, (x_offset, y_offset), person_image)
        
        # Convert to base64
        buffered = io.BytesIO()
        background_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
