from flask import Flask, send_file
import subprocess
import os

app = Flask(__name__)

@app.route('/run-script', methods=['POST'])
def run_script():
    # Assuming your script generates an image called 'output_image.png'
    subprocess.run(['python', 'your_script.py'])  # Run your script

    # Serve the generated image
    return send_file('output_image.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)

